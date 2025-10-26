# get_response(model: str, system_prompt: str, user_prompt: str, *, temperature: float = 0.2, priority: bool = False)
# algo:
#     extract from a line of positive_data.jsonl
#     # {"category": "Positive", "query": "Can you please make an audio MeeTime call to my friend at this number 16502531234?", "intent": [{"name": "CALL_MEETIME", "arguments": {"PHONE_NUMBER": "16502531234", "MEDIA_TYPE": "AUDIO"}}], "match": "True"}
#     告诉LLM来用这条数据做adverseral data generation，规则如下：
#         将query里的语气稍作修改，数字和人名做一下无害替换。只修改语气和数字/人名！
#         提取当前intent，根据CLUSTER随机找到一个不属于其category的intent new，
#         在api.jsonl中提取到intent new对应的description和argument description等信息
#         # {"name": "CREATE_CALENDER_EVENT", "description": "Add a new event to the user's calendar.\n", "arguments": {"TITLE": {"description": "The event title.", "type": "str", "required": true}, "DESCRIPTION": {"description": "The event description.", "type": "str", "required": true}, "EVENT_LOCATION": {"description": "The event location. Default is None.", "type": "str", "required": false, "default": null}, "EXTRA_EVENT_ALL_DAY": {"description": "A boolean specifying whether this is an all-day event. Default is False.", "type": "bool", "required": false, "default": false}, "EXTRA_EVENT_BEGIN_TIME": {"description": "The start time of the event in ISO 8601 format. Default is None.", "type": "str", "required": false, "default": null}, "EXTRA_EVENT_END_TIME": {"description": "The end time of the event in ISO 8601 format. Default is None.", "type": "str", "required": false, "default": null}}}
#         使用这个信息任意编造一组符合要求的假intent数据，包含其argument等
#         Finalise 错误数据
#         # {"category": "False_Intent_Easy", "query": "{New query}", "intent": [{"name": "{false intent}", "arguments": {"{name}": "...", "{name}": "..."}}], "match": "False"}
#     保存这一数据，检查好格式无误后append入false_intent_easy.jsonl

import json
import os
import re
import sys
import random
from datetime import datetime, timedelta

from helper import get_response  # <-- uses your provided helper

CLUSTER = {
    "0": ['OPEN_CAMERA', 'TAKE_PHOTO'],
    "1": ['START_NAVIGATE', 'GET_CURRENT_LOCATION', 'VIEW_ROUTES'],
    "2": ['SEARCH_CALL_RECORD', 'VIEW_CALL_RECORD'],
    "3": ['CREATE_CALENDER_EVENT'],
    "4": ['SET_PLAYBACK_STATE'],
    "5": ['CALL_MEETIME', 'START_CALL', 'MAKE_CALL'],
    "6": ['READ_EMAIL', 'SEND_EMAIL', 'WRITE_EMAIL'],
    "7": ['PAY_REPAYMENT']
}

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

# -----------------------------
# Intent utilities
# -----------------------------
def intent_to_cluster(intent_name):
    for cid, intents in CLUSTER.items():
        if intent_name in intents:
            return cid
    return None

def pick_false_intent(original_intent_name):
    orig_cluster = intent_to_cluster(original_intent_name)
    other_clusters = [cid for cid in CLUSTER.keys() if cid != orig_cluster]
    if not other_clusters:
        other_clusters = list(CLUSTER.keys())
    chosen_cluster = random.choice(other_clusters)
    chosen_intent = random.choice(CLUSTER[chosen_cluster])
    return chosen_intent

def extract_primary_intent(positive_item):
    intents = positive_item.get("intent", [])
    if not intents:
        return None
    return intents[0].get("name")

# -----------------------------
# LLM perturbation
# -----------------------------
SYS_PERTURB = """You are a careful data generator.
Return a single JSON object with exactly one key: "perturbed_query".
The value must be a string that is a lightly modified version of the input query.

Rules (obligatory):
1) Only modify TONE (e.g., add/remove 'please', punctuation, minor politeness changes) AND
   replace NUMBERS and PERSON NAMES with harmless substitutes.
2) Do NOT introduce or remove any operational constraints, steps, or APIs.
3) Keep the same user intent semantics otherwise — do not change verbs like 'call', 'start', 'navigate', etc.
4) Do NOT add new entities, tasks, or tools that were not in the original query.
5) Output JSON ONLY, no prose, no markdown.
"""

USER_PERTURB_TMPL = """ORIGINAL_QUERY:
{q}

Return JSON ONLY:
{{"perturbed_query": "<lightly-modified-query>"}}
"""

def llm_perturb_query(query, model="gpt-4o", temperature=0.2):
    user_prompt = USER_PERTURB_TMPL.format(q=query)
    resp = get_response(model=model, system_prompt=SYS_PERTURB, user_prompt=user_prompt, temperature=temperature)
    try:
        m = re.search(r"\{.*\}", resp, flags=re.DOTALL)
        if not m:
            raise ValueError("No JSON object found in LLM response")
        data = json.loads(m.group(0))
        new_q = data.get("perturbed_query")
        if not isinstance(new_q, str) or len(new_q.strip()) == 0:
            raise ValueError("perturbed_query missing/empty")
        return new_q.strip()
    except Exception as e:
        print(f"[WARN] LLM perturbation failed, falling back to original query. Reason: {e}")
        return query

# -----------------------------
# False argument generation
# -----------------------------
SYS_ARG_GEN = """You are a precise data generator for testing intent classification systems.
Given an API schema (intent name, description, and argument descriptions), generate a plausible but FABRICATED set of arguments.

Rules:
1) Generate realistic-looking argument values that match the type and description
2) For required arguments, always provide values
3) For optional arguments, randomly include them (~50% probability)
4) Use realistic data (e.g., phone numbers like "14155552368", dates in ISO format, realistic names/titles)
5) Return JSON ONLY with structure: {{"arguments": {{"ARG_NAME": "value", ...}}}}
6) No markdown, no prose, just the JSON object
"""

USER_ARG_GEN_TMPL = """API_SCHEMA:
{schema}

Generate plausible fabricated arguments. Return JSON ONLY:
{{"arguments": {{"ARG_NAME": "value", ...}}}}
"""

def llm_generate_false_arguments(api_schema, model="gpt-4o", temperature=0.5):
    schema_str = json.dumps(api_schema, indent=2, ensure_ascii=False)
    user_prompt = USER_ARG_GEN_TMPL.format(schema=schema_str)
    resp = get_response(model=model, system_prompt=SYS_ARG_GEN, user_prompt=user_prompt, temperature=temperature)
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
        print(f"[WARN] LLM argument generation failed. Reason: {e}")
        return {}

# -----------------------------
# Main generation logic
# -----------------------------
def generate_adversarial_data(
    positive_jsonl_path="positive_data.jsonl",
    api_jsonl_path="api.jsonl",
    output_jsonl_path="false_intent_easy.jsonl",
    model="gpt-4o",
    limit=None
):
    """
    Generate adversarial negative examples from positive data.
    
    Args:
        positive_jsonl_path: Path to positive examples
        api_jsonl_path: Path to API schema definitions
        output_jsonl_path: Path to output false intent examples
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
    
    # Generate adversarial examples
    generated_count = 0
    for i, pos_item in enumerate(positive_data):
        if limit and generated_count >= limit:
            break
            
        try:
            print(f"\n[{i+1}/{len(positive_data)}] Processing...")
            
            # 1. Extract original query and intent
            original_query = pos_item.get("query", "")
            if not original_query:
                print("  [SKIP] No query found")
                continue
                
            original_intent_name = extract_primary_intent(pos_item)
            if not original_intent_name:
                print("  [SKIP] No intent found")
                continue
            
            print(f"  Original intent: {original_intent_name}")
            print(f"  Original query: {original_query}")
            
            # 2. Perturb the query (modify tone and replace numbers/names)
            perturbed_query = llm_perturb_query(original_query, model=model)
            print(f"  Perturbed query: {perturbed_query}")
            
            # 3. Pick a false intent from a different cluster
            false_intent_name = pick_false_intent(original_intent_name)
            print(f"  False intent: {false_intent_name}")
            
            # 4. Get API schema for the false intent
            if false_intent_name not in api_dict:
                print(f"  [SKIP] No API schema found for {false_intent_name}")
                continue
            
            api_schema = api_dict[false_intent_name]
            
            # 5. Generate false arguments using LLM
            false_arguments = llm_generate_false_arguments(api_schema, model=model, temperature=0.5)
            print(f"  Generated arguments: {json.dumps(false_arguments, ensure_ascii=False)}")
            
            # 6. Create the false intent example
            false_example = {
                "category": "False_Intent_Easy",
                "query": perturbed_query,
                "intent": [{
                    "name": false_intent_name,
                    "arguments": false_arguments
                }],
                "match": "False"
            }
            
            # 7. Validate and save
            # Basic validation
            assert isinstance(false_example["query"], str) and len(false_example["query"]) > 0
            assert isinstance(false_example["intent"], list) and len(false_example["intent"]) > 0
            assert false_example["match"] == "False"
            
            save_jsonl_append(output_jsonl_path, false_example)
            generated_count += 1
            print(f"  [SUCCESS] Saved to {output_jsonl_path}")
            
        except Exception as e:
            print(f"  [ERROR] Failed to process item {i+1}: {e}")
            continue
    
    print(f"\n{'='*60}")
    print(f"Generation complete!")
    print(f"Generated {generated_count} adversarial examples")
    print(f"Output saved to: {output_jsonl_path}")
    print(f"{'='*60}")

# -----------------------------
# CLI entry point
# -----------------------------
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate adversarial false intent data")
    parser.add_argument("--positive", default="positive_data.jsonl", help="Path to positive data JSONL")
    parser.add_argument("--api", default="api.jsonl", help="Path to API schema JSONL")
    parser.add_argument("--output", default="false_intent_easy.jsonl", help="Path to output JSONL")
    parser.add_argument("--model", default="gpt-4.1", help="LLM model to use")
    parser.add_argument("--limit", type=int, default=None, help="Max examples to generate")
    
    args = parser.parse_args()
    
    generate_adversarial_data(
        positive_jsonl_path=args.positive,
        api_jsonl_path=args.api,
        output_jsonl_path=args.output,
        model=args.model,
        limit=args.limit
    )

