"""Build version 2 offline from reviewed FewRel records and authored scenarios."""

import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

from synthetic_cases import fact, record, source, synthetic_cases

from crm_study.data import audit_split, grouped_split
from crm_study.schema import normalize, write_jsonl

ROOT = Path(__file__).resolve().parents[1]


def detokenize(tokens):
    text = unicodedata.normalize("NFC", " ".join(tokens))
    text = re.sub(r"\s+([,.;:!?%)\]])", r"\1", text)
    text = re.sub(r"([(\[])\s+", r"\1", text)
    text = re.sub(r"\s+(['’]s)\b", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def mention(row, key):
    positions = row[key][2][0]
    if positions != list(range(min(positions), max(positions) + 1)):
        raise ValueError("Selected entity mention must have a contiguous upstream span")
    return detokenize(row["tokens"][min(positions) : max(positions) + 1])


def public_cases():
    plan = json.loads((ROOT / "data/curation/fewrel_selection.json").read_text())
    selected = json.loads((ROOT / "data/raw/fewrel/selected.json").read_text())
    expected = {(r, i) for r, indices in plan["selections"].items() for i in indices}
    if {(e["relation"], e["row_index"]) for e in selected} != expected or len(selected) != len(
        expected
    ):
        raise ValueError("Raw selection differs from curation; run scripts/collect_fewrel.py")
    cases, labels = [], []
    for entry in selected:
        row, relation, index = entry["record"], entry["relation"], entry["row_index"]
        text, subject, value = detokenize(row["tokens"]), mention(row, "h"), mention(row, "t")
        attribute = {"P39": "role", "P127": "owned_by", "P159": "headquarters"}[relation]
        entity_type = "person" if relation == "P39" else "company"
        case_id = f"fewrel-{relation.lower()}-{index:04d}"
        keys = {
            "qid:" + row["h"][1],
            "identity:" + normalize(subject),
            "identity:" + normalize(row["h"][0]),
            f"fewrel:train_wiki:{relation}:{index}",
        }
        if relation == "P127":
            keys.update(
                [
                    "qid:" + row["t"][1],
                    "identity:" + normalize(value),
                    "identity:" + normalize(row["t"][0]),
                ]
            )
        target = record("public-1", subject, entity_type, aliases=[row["h"][0]])
        query = f"Extract the {attribute} relationship stated for {subject}. Treat this as a historical passage, not a current-world lookup."
        if attribute == "headquarters":
            query += " Use the stated city or named facility; optional region/country details may be included."
        if attribute == "role":
            query += " A public office title alone does not identify an employer organization."
        cases.append(
            {
                "id": case_id,
                "dataset_version": "2",
                "origin": "fewrel_adapted",
                "category": attribute,
                "query": query,
                "as_of": "2026-10-17",
                "time_scope": "historical",
                "sources": [source(text, "wiki", source_date=None, kind="public_dataset")],
                "crm": [target],
                "split_keys": sorted(keys),
                "provenance": {
                    "dataset": "FewRel 1.0 train_wiki",
                    "url": plan["source_url"],
                    "relation": relation,
                    "row_index": index,
                    "head_qid": row["h"][1],
                    "tail_qid": row["t"][1],
                    "condition": "supported",
                    "adaptation": "detokenized text, targeted historical query, simulated CRM and permission condition; source/effective dates unknown",
                },
            }
        )
        values = [value, *plan["value_alternatives"].get(f"{relation}:{index}", [])]
        if relation == "P39" and "former " + normalize(value) in normalize(text):
            values.append("former " + value)
        candidates = [
            fact(
                subject,
                v,
                text,
                effective_date=None,
                source_id="wiki",
                entity_type=entity_type,
                attribute=attribute,
            )
            for v in values
        ]
        labels.append(
            {
                "case_id": case_id,
                "dataset_version": "2",
                "decision": "accept",
                "resolution": {"status": "matched", "entity_id": "public-1"},
                "candidates": candidates,
                "verification": {
                    "support": "supported",
                    "date_supported": True,
                    "conflicting_sources": False,
                },
                "rationale": "The historical relation is explicit; no precise effective day or current-world status is inferred.",
                "annotation": "Upstream FewRel relation/spans; passage selection, alternatives, and CRM decision authored for this study",
            }
        )
    assignment = grouped_split(cases)
    by_id = {g["case_id"]: g for g in labels}
    for case in cases:
        case["split"] = assignment[case["id"]]
    # Each split/relation: eight ordinary, one duplicate-CRM, one permission case.
    # Conditions use distinct documents, never copies of a source across the split.
    for relation in plan["selections"]:
        for split in ("dev", "test"):
            group = sorted(
                [
                    c
                    for c in cases
                    if c["split"] == split and c["provenance"]["relation"] == relation
                ],
                key=lambda c: c["id"],
            )
            if len(group) != 10:
                raise ValueError("Curation must yield ten public cases per relation per split")
            duplicate, forbidden = group[-2:]
            duplicate["crm"].append({**duplicate["crm"][0], "id": "public-2"})
            duplicate["provenance"]["condition"] = "duplicate_records"
            by_id[duplicate["id"]].update(
                decision="review",
                resolution={"status": "ambiguous", "entity_id": None},
                rationale="Two indistinguishable simulated records require review despite supported public evidence.",
            )
            forbidden["sources"][0]["allowed"] = False
            forbidden["provenance"]["condition"] = "disallowed_source"
            by_id[forbidden["id"]].update(
                decision="reject",
                rationale="This simulated task marks the public source as unavailable for writing; this is not a claim about its real license.",
            )
    return cases, labels


def main():
    cases, labels = synthetic_cases()
    public, answers = public_cases()
    cases = sorted(cases + public, key=lambda c: c["id"])
    labels = sorted(labels + answers, key=lambda g: g["case_id"])
    revision = json.loads((ROOT / "data/curation/fewrel_selection.json").read_text())[
        "annotation_revision"
    ]
    for answer in labels:
        answer["annotation_revision"] = revision
    audit_split(cases, labels)
    if len(cases) != 132:
        raise ValueError("Version 2 must contain 72 synthetic and 60 public cases")
    write_jsonl(ROOT / "data/processed/cases.jsonl", cases)
    write_jsonl(ROOT / "data/labels/answers.jsonl", labels)
    summary = {
        "dataset_version": "2",
        "annotation_revision": revision,
        "total_cases": len(cases),
        "by_origin": dict(Counter(c["origin"] for c in cases)),
        "by_split": dict(Counter(c["split"] for c in cases)),
        "by_decision": dict(Counter(g["decision"] for g in labels)),
        "public_unique_source_records": len(public),
        "synthetic_scenarios": 18,
        "cleaning": [
            "Unicode NFC and token punctuation/whitespace normalization",
            "retained original records, spans, QIDs and relation/row positions",
            "reviewed explicit subject-relation support and date interpretation",
            "unknown public dates remain null; simulated permissions and CRM are labelled adaptations",
        ],
    }
    (ROOT / "data/processed/build_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
