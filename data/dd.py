import json, sys, pathlib

def convert_any_to_jsonl(in_path: str, out_path: str):
    p_in = pathlib.Path(in_path)
    raw = p_in.read_text(encoding="utf-8").strip()

    records = None

    # 1) Try JSON array: [ {...}, {...} ]
    try:
        obj = json.loads(raw)
        if isinstance(obj, list):
            records = obj
    except json.JSONDecodeError:
        pass

    # 2) Fallback: JSON Lines (one JSON object per non-empty line)
    if records is None:
        records = []
        lines = [ln for ln in raw.splitlines() if ln.strip()]
        for i, ln in enumerate(lines, 1):
            try:
                records.append(json.loads(ln))
            except json.JSONDecodeError as e:
                raise SystemExit(
                    f"❌ Line {i} is not valid JSON: {e}\n"
                    f"↳ Offending line:\n{ln}"
                )

    # 3) Write compact JSONL
    with open(out_path, "w", encoding="utf-8") as fw:
        for obj in records:
            fw.write(json.dumps(obj, ensure_ascii=False) + "\n")

    print(f"✅ Converted {len(records)} entries → {out_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python convert_any_to_jsonl.py <input.json|jsonl> <output.jsonl>")
        sys.exit(1)
    convert_any_to_jsonl(sys.argv[1], sys.argv[2])

