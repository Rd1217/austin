import json
import csv
import sys
from typing import Any, Dict, List


INPUT_JSON = "testing.json"
OUTPUT_CSV = "enquiries.csv"


def flatten(obj: Any, prefix: str = "", sep: str = ".") -> Dict[str, Any]:
    """
    Flatten nested dicts using dot notation.
    Lists are stored as JSON strings.
    """
    out: Dict[str, Any] = {}

    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}{sep}{k}" if prefix else k
            out.update(flatten(v, key, sep=sep))
    elif isinstance(obj, list):
        # store lists as JSON text
        out[prefix] = json.dumps(obj, ensure_ascii=False)
    else:
        out[prefix] = obj

    return out


def main():
    # Load JSON
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Extract rows from listData
    if isinstance(data, dict) and "listData" in data and isinstance(data["listData"], list):
        rows: List[Dict[str, Any]] = data["listData"]
    else:
        print("❌ Could not find 'listData' array in the JSON file.", file=sys.stderr)
        print("Expected format: { 'listData': [ ... ] }", file=sys.stderr)
        sys.exit(1)

    if not rows:
        print("⚠️ listData is empty. CSV will contain only headers (none).")
        # still create empty CSV
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            f.write("")
        print(f"✅ Wrote empty CSV: {OUTPUT_CSV}")
        sys.exit(0)

    # Flatten each row (in case there are nested objects)
    flat_rows = [flatten(r) for r in rows]

    # Collect all columns across all rows
    columns: List[str] = []
    seen = set()
    for r in flat_rows:
        for k in r.keys():
            if k not in seen:
                seen.add(k)
                columns.append(k)

    # Write CSV
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(flat_rows)

    print(f"✅ Input JSON : {INPUT_JSON}")
    print(f"✅ Rows       : {len(rows)}")
    print(f"✅ Output CSV : {OUTPUT_CSV}")


if __name__ == "__main__":
    main()