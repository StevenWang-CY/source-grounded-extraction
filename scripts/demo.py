"""Show the source, candidate, and CRM outcome of both workflows for one saved case."""

import argparse
import json
from pathlib import Path

from crm_study.schema import read_jsonl


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=Path("results/test"))
    parser.add_argument("--case-id", default="scenario-05-3")
    args = parser.parse_args()
    case = next((c for c in read_jsonl(args.run / "cases.jsonl") if c["id"] == args.case_id), None)
    if case is None:
        parser.error(f"{args.case_id} is not one of this run's cases")
    results = [
        r
        for r in read_jsonl(args.run / "predictions.jsonl")
        if r["case_id"] == args.case_id and r["repeat"] == 0
    ]
    split = {"dev": "development", "test": "test", "test2": "second test"}[case["split"]]
    print(f"Saved {split} case: {case['id']}")
    print(case["query"])
    print("\nSources:")
    for source in case["sources"]:
        print(
            f"  {source['id']} (allowed={source['allowed']}, date={source['source_date']}): {source['text']}"
        )
    print("\nOriginal records:")
    for record in case["crm"]:
        print(
            f"  {record['id']}: {record['name']} | {record.get('organization', '')} | {json.dumps(record['facts'])}"
        )
        if record["aliases"]:
            print("    Declared aliases:", ", ".join(record["aliases"]))
    for result in sorted(results, key=lambda r: r["strategy"]):
        p = result["prediction"]
        print(f"\n{result['strategy'].upper()}: {p['decision']} ({result['latency_seconds']:.1f}s)")
        changes = next(
            (s["output"] for s in result["stages"] if s["stage"] == "contract_check"), {}
        )
        for field, change in changes.items():
            print(f"  Contract check: {field} {change['model']!r} stored as {change['stored']!r}")
        print("  Candidate:", json.dumps(p["candidate"], ensure_ascii=False))
        print("  Resolution:", json.dumps(p["resolution"]))
        print("  Reason:", p.get("reason"))  # a direct response may omit its reason
        if p.get("checks"):
            print("  Checks:", json.dumps(p["checks"]))
        write = result["stages"][-1]["output"]
        print("  CRM write:", write["applied"], "| record:", write["record_id"])
        if write["applied"]:
            target = next(r for r in write["crm"] if r["id"] == write["record_id"])
            print("  Stored facts:", json.dumps(target["facts"], ensure_ascii=False))
        if write.get("error"):
            print("  Write error:", write["error"])
        if result["error"]:
            print("  Error:", result["error"])


if __name__ == "__main__":
    main()
