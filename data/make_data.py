import json

def convert_jsonl(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as infile, \
         open(output_path, "w", encoding="utf-8") as outfile:

        for line in infile:
            data = json.loads(line.strip())

            # The "answers" field contains the tool call info
            answers = data.get("answers", [])
            if not answers:
                continue  # ignore lines without answers

            # We assume only one main intent (first answer)
            ans = answers[0]

            # Extract call arguments
            tool_name = ans.get("name")
            args = ans.get("arguments", {})

            # Construct new JSONL format
            converted = {
                "category": "Positive",
                "query": data.get("query"),
                "intent": [
                    {
                        "name": tool_name,
                        "arguments": args
                    }
                ],
                "match": "True"
            }

            outfile.write(json.dumps(converted, ensure_ascii=False) + "\n")


# Example usage
convert_jsonl("instructions.jsonl", "positive_data.jsonl")
