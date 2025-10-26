# get_response(model: str, system_prompt: str, user_prompt: str, *, temperature: float = 0.2, priority: bool = False)
# algo:
#     extract from a line of positive_data.jsonl
#     # {"category": "Positive", "query": "Can you please make an audio MeeTime call to my friend at this number 16502531234?", "intent": [{"name": "CALL_MEETIME", "arguments": {"PHONE_NUMBER": "16502531234", "MEDIA_TYPE": "AUDIO"}}], "match": "True"}
#     告诉LLM来用这条数据做adverseral data generation，规则如下：
#         将query里的语气稍作修改，数字和人名做一下无害替换。只修改语气和数字/人名！
#         在api.jsonl中提取到intent对应的description和argument description等信息
#         # 如 {"name": "CALL_MEETIME", "description": "Initiates a MeeTime call to the specified phone number.\n\nThis function allows the user to start a Huawei MeeTime call. It can be used\nto make either an audio or video call depending on the specified media type.", "arguments": {"PHONE_NUMBER": {"description": "The phone number to call.\n- This should be a valid telephone number (e.g., \"13800138000\").\n- The number must be registered with Huawei MeeTime service.", "type": "str", "required": true}, "MEDIA_TYPE": {"description": "The type of call to initiate.\n- \"AUDIO\": Start an audio call. (default)\n- \"VIDEO\": Start a video call.", "type": "{\"AUDIO\", \"VIDEO\"}", "required": false, "default": "AUDIO"}}}
#         使用这个信息在同一intent下任意编造一组符合要求的错误argument数据（可以适当保留原样，修改其中部分即可，也可以全部修改）
#         若此intent没有argument，跳过生成此数据
#         Finalise 错误数据
#         # {"category": "False_Argument", "query": "{New query}", "intent": [{"name": "CALL_MEETIME", "arguments": {"PHONE_NUMBER": "8832749238", "MEDIA_TYPE": "AUDIO"}}], "match": "False"}
#     保存这一数据，检查好格式无误后append入false_argument.jsonl

import json
import os
import re
import sys
import random
from datetime import datetime, timedelta

from helper import get_response  # <-- uses your provided helper

# -----------------------------
# IO helpers
# -----------------------------
def load_jsonl(path):
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except Exception as e:
                print(f"[WARN] Failed to parse JSON on {path} line {i}: {e}")
    return items

def save_jsonl_append(path, obj):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def extract_primary_intent(positive_item):
    intents = positive_item.get("intent", [])
    if not intents:
        return None, None
    intent_obj = intents[0]
    return intent_obj.get("name"), intent_obj.get("arguments", {})

# -----------------------------
# LLM query perturbation with argument extraction
# -----------------------------
SYS_PERTURB = """You are a careful data generator.
Return a single JSON object with two keys: "perturbed_query" and "correct_arguments".

Rules:
1) Modify the original query by:
   - Changing TONE (e.g., add/remove 'please', punctuation, minor politeness changes)
   - Replacing NUMBERS and PERSON NAMES with different harmless substitutes
2) Do NOT change the semantic intent (keep verbs like 'call', 'start', 'navigate', etc.)
3) Extract the CORRECT arguments from YOUR perturbed query that match the API schema
4) The correct_arguments should reflect what the USER asks for in the perturbed query
5) Output JSON ONLY, no prose, no markdown.

IMPORTANT - When generating replacement numbers:
- DO NOT use sequential/incremental patterns like 12345678901, 11111111111, etc.
- Use realistic-looking numbers with mixed digits (e.g., 13857294016, 15923847501)
- For phone numbers, use proper regional formats if applicable
- Avoid obvious fake patterns

Example:
Original: "Call John at 1234567890"
Output: {
  "perturbed_query": "Please call Alice at 13857294016",
  "correct_arguments": {"PHONE_NUMBER": "13857294016", "RECIPIENT_NAME": "Alice"}
}
"""

USER_PERTURB_TMPL = """ORIGINAL_QUERY:
{original_query}

ORIGINAL_ARGUMENTS:
{original_args}

API_SCHEMA:
{api_schema}

Generate a perturbed query with tone/number/name changes, and extract the CORRECT arguments from your perturbed query.
Return JSON ONLY:
{{
  "perturbed_query": "<modified-query>",
  "correct_arguments": {{"ARG_NAME": "value", ...}}
}}
"""

def llm_perturb_query_and_extract_args(original_query, original_args, api_schema, model="gpt-4o", temperature=0.2):
    """
    Perturb query and extract correct arguments from the perturbed query.
    
    Returns:
        tuple: (perturbed_query, correct_arguments_from_perturbed_query)
    """
    schema_str = json.dumps(api_schema, indent=2, ensure_ascii=False)
    original_args_str = json.dumps(original_args, indent=2, ensure_ascii=False)
    
    user_prompt = USER_PERTURB_TMPL.format(
        original_query=original_query,
        original_args=original_args_str,
        api_schema=schema_str
    )
    
    resp = get_response(model=model, system_prompt=SYS_PERTURB, user_prompt=user_prompt, temperature=temperature)
    
    try:
        m = re.search(r"\{.*\}", resp, flags=re.DOTALL)
        if not m:
            raise ValueError("No JSON object found in LLM response")
        data = json.loads(m.group(0))
        
        new_query = data.get("perturbed_query")
        correct_args = data.get("correct_arguments", {})
        
        if not isinstance(new_query, str) or len(new_query.strip()) == 0:
            raise ValueError("perturbed_query missing/empty")
        if not isinstance(correct_args, dict):
            raise ValueError("correct_arguments must be a dict")
            
        return new_query.strip(), correct_args
        
    except Exception as e:
        print(f"[WARN] LLM perturbation failed, falling back to original. Reason: {e}")
        return original_query, original_args

# -----------------------------
# False argument generation (MISMATCHED WITH QUERY INTENT)
# -----------------------------
SYS_FALSE_ARG = """You are a data generator for testing intent classification systems.
Your task is to generate arguments that are VALID according to API specification but MISMATCHED with the user's query intent.

Given:
1. User's perturbed query (what the user actually wants)
2. Correct arguments extracted from the perturbed query
3. API schema (intent name, description, argument descriptions)

Generate INCORRECT arguments that:
- Are VALID according to the API specification (correct types, formats, required fields)
- But DO NOT match what the user asked for in the perturbed query
- Change 1-3 argument values to be different from the correct arguments

Rules:
1) Keep arguments in VALID format (correct types, meet API requirements)
2) Change the VALUES to mismatch what user wants in the perturbed query
3) Modify 1-3 arguments (you can keep some correct and change others)
4) Return JSON ONLY: {{"arguments": {{"ARG_NAME": "value", ...}}}}
5) No markdown, no prose
"""

USER_FALSE_ARG_TMPL = """PERTURBED_QUERY:
{perturbed_query}

CORRECT_ARGUMENTS (from perturbed query):
{correct_args}

API_SCHEMA:
{api_schema}

Generate arguments that are VALID in format but MISMATCHED with the perturbed query intent. Return JSON ONLY:
{{"arguments": {{"ARG_NAME": "value", ...}}}}
"""

def llm_generate_false_arguments(perturbed_query, correct_args, api_schema, model="gpt-4o", temperature=0.7):
    """
    Generate false arguments that don't match the perturbed query's intent.
    
    Args:
        perturbed_query: The perturbed query
        correct_args: Correct arguments from perturbed query
        api_schema: The API schema dict
        model: LLM model to use
        temperature: Higher temperature for variety
    
    Returns:
        dict: False arguments (valid format, wrong values)
    """
    schema_str = json.dumps(api_schema, indent=2, ensure_ascii=False)
    correct_args_str = json.dumps(correct_args, indent=2, ensure_ascii=False)
    
    user_prompt = USER_FALSE_ARG_TMPL.format(
        perturbed_query=perturbed_query,
        correct_args=correct_args_str,
        api_schema=schema_str
    )
    
    resp = get_response(model=model, system_prompt=SYS_FALSE_ARG, user_prompt=user_prompt, temperature=temperature)
    
    try:
        m = re.search(r"\{.*\}", resp, flags=re.DOTALL)
        if not m:
            raise ValueError("No JSON object found in LLM response")
        data = json.loads(m.group(0))
        args = data.get("arguments", {})
        if not isinstance(args, dict):
            raise ValueError("arguments must be a dict")
        return args
    except Exception as e:
        print(f"[WARN] LLM false argument generation failed. Reason: {e}")
        return correct_args  # Fallback

# -----------------------------
# Main generation logic
# -----------------------------
def generate_false_argument_data(
    positive_jsonl_path="positive_data.jsonl",
    api_jsonl_path="api.jsonl",
    output_jsonl_path="false_argument.jsonl",
    model="gpt-4o",
    limit=None
):
    """
    Generate false argument examples from positive data.
    
    Args:
        positive_jsonl_path: Path to positive examples
        api_jsonl_path: Path to API schema definitions
        output_jsonl_path: Path to output false argument examples
        model: LLM model to use
        limit: Max number of examples to generate (None = all)
    """
    # Load data
    print(f"Loading positive data from {positive_jsonl_path}...")
    positive_data = load_jsonl(positive_jsonl_path)
    print(f"Loaded {len(positive_data)} positive examples")
    
    print(f"Loading API schemas from {api_jsonl_path}...")
    api_data = load_jsonl(api_jsonl_path)
    api_dict = {item["name"]: item for item in api_data}
    print(f"Loaded {len(api_dict)} API schemas")
    
    # Generate false argument examples
    generated_count = 0
    skipped_no_args = 0
    
    for i, pos_item in enumerate(positive_data):
        if limit and generated_count >= limit:
            break
            
        try:
            print(f"\n[{i+1}/{len(positive_data)}] Processing...")
            
            # 1. Extract original query and intent with arguments
            original_query = pos_item.get("query", "")
            if not original_query:
                print("  [SKIP] No query found")
                continue
            
            intent_name, original_arguments = extract_primary_intent(pos_item)
            if not intent_name:
                print("  [SKIP] No intent found")
                continue
            
            # Check if intent has arguments
            if not original_arguments or len(original_arguments) == 0:
                print(f"  [SKIP] Intent {intent_name} has no arguments")
                skipped_no_args += 1
                continue
            
            print(f"  Intent: {intent_name}")
            print(f"  Original query: {original_query}")
            print(f"  Original arguments: {json.dumps(original_arguments, ensure_ascii=False)}")
            
            # 2. Get API schema for the intent
            if intent_name not in api_dict:
                print(f"  [SKIP] No API schema found for {intent_name}")
                continue
            
            api_schema = api_dict[intent_name]
            
            # 3. Perturb the query AND extract correct arguments from perturbed query
            perturbed_query, correct_args_from_perturbed = llm_perturb_query_and_extract_args(
                original_query, 
                original_arguments, 
                api_schema,
                model=model, 
                temperature=0.2
            )
            print(f"  Perturbed query: {perturbed_query}")
            print(f"  Correct args (from perturbed): {json.dumps(correct_args_from_perturbed, ensure_ascii=False)}")
            
            # 4. Generate false arguments that don't match the perturbed query
            false_arguments = llm_generate_false_arguments(
                perturbed_query,
                correct_args_from_perturbed,  # Use correct args from perturbed query as reference
                api_schema, 
                model=model, 
                temperature=0.7
            )
            print(f"  False arguments: {json.dumps(false_arguments, ensure_ascii=False)}")
            
            # 5. Create the false argument example
            false_example = {
                "category": "False_Argument",
                "query": perturbed_query,
                "intent": [{
                    "name": intent_name,
                    "arguments": false_arguments  # Wrong arguments (don't match perturbed query)
                }],
                "match": "False"
            }
            
            # 6. Validate and save
            assert isinstance(false_example["query"], str) and len(false_example["query"]) > 0
            assert isinstance(false_example["intent"], list) and len(false_example["intent"]) > 0
            assert false_example["match"] == "False"
            assert false_example["intent"][0]["name"] == intent_name
            
            save_jsonl_append(output_jsonl_path, false_example)
            generated_count += 1
            print(f"  [SUCCESS] Saved to {output_jsonl_path}")
            
        except Exception as e:
            print(f"  [ERROR] Failed to process item {i+1}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\n{'='*60}")
    print(f"Generation complete!")
    print(f"Generated {generated_count} false argument examples")
    print(f"Skipped {skipped_no_args} intents with no arguments")
    print(f"Output saved to: {output_jsonl_path}")
    print(f"{'='*60}")

# -----------------------------
# CLI entry point
# -----------------------------
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate false argument adversarial data")
    parser.add_argument("--positive", default="positive_data.jsonl", help="Path to positive data JSONL")
    parser.add_argument("--api", default="api.jsonl", help="Path to API schema JSONL")
    parser.add_argument("--output", default="false_argument.jsonl", help="Path to output JSONL")
    parser.add_argument("--model", default="gpt-4.1", help="LLM model to use")
    parser.add_argument("--limit", type=int, default=None, help="Max examples to generate")
    
    args = parser.parse_args()
    
    generate_false_argument_data(
        positive_jsonl_path=args.positive,
        api_jsonl_path=args.api,
        output_jsonl_path=args.output,
        model=args.model,
        limit=args.limit
    )
