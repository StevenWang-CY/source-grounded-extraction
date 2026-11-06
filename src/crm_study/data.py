"""Dataset checks useful for catching annotation and cleaning mistakes."""

import random
from collections import Counter, defaultdict

from .schema import (
    DECISIONS,
    ENTITY_ATTRIBUTES,
    Candidate,
    normalize,
    quote_in_source,
    validate_date,
    validate_resolution,
)


def validate_dataset(cases: list[dict], labels: list[dict]) -> dict:
    ids = [c["id"] for c in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate case IDs")
    gold = {g["case_id"]: g for g in labels}
    if set(ids) != set(gold) or len(labels) != len(gold):
        raise ValueError("Cases and answer keys must have the same unique IDs")
    seen = set()
    for case in cases:
        if case["split"] not in {"dev", "test"}:
            raise ValueError("Unknown dataset split")
        if case["time_scope"] not in {"current", "historical"}:
            raise ValueError("Unknown time scope")
        validate_date(case["as_of"])
        record_ids = [r["id"] for r in case["crm"]]
        if len(record_ids) != len(set(record_ids)):
            raise ValueError("Duplicate record IDs within a case")
        for record in case["crm"]:
            if not {"id", "name", "entity_type", "aliases", "facts"} <= record.keys():
                raise ValueError(f"A CRM record in {case['id']} lacks a required field")
            if record["entity_type"] not in ENTITY_ATTRIBUTES:
                raise ValueError("Unknown CRM entity type")
            for attribute, fact in record["facts"].items():
                if attribute not in ENTITY_ATTRIBUTES[record["entity_type"]]:
                    raise ValueError("CRM fact has the wrong record type")
                validate_date(fact.get("effective_date"))
        sources = {s["id"]: s for s in case["sources"]}
        if len(sources) != len(case["sources"]):
            raise ValueError("Duplicate source IDs within a case")
        for source in sources.values():
            validate_date(source["source_date"])
            if not isinstance(source["allowed"], bool):
                raise ValueError("Permission label must be boolean")
            text = normalize(source["text"])
            if text in seen:
                raise ValueError("Source text duplicated across cases")
            seen.add(text)
        answer = gold[case["id"]]
        if case.get("dataset_version") != answer.get("dataset_version"):
            raise ValueError("Case and answer-key dataset versions differ")
        if answer["decision"] not in DECISIONS:
            raise ValueError("Unknown answer-key decision")
        validate_resolution(answer["resolution"])
        if answer["decision"] == "accept" and not answer["candidates"]:
            raise ValueError("An accepted answer needs a candidate")
        for c in answer["candidates"]:
            candidate = Candidate.from_dict(c)
            if candidate.source_id not in sources or not quote_in_source(
                candidate.evidence, sources[candidate.source_id]["text"]
            ):
                raise ValueError(f"Invalid gold evidence in {case['id']}")
            if answer["decision"] == "accept" and not sources[candidate.source_id]["allowed"]:
                raise ValueError("Gold accepted a disallowed source")
        resolution = answer["resolution"]
        if resolution["status"] == "matched" and resolution["entity_id"] not in record_ids:
            raise ValueError("Gold matched an unknown CRM ID")
        if resolution["status"] == "matched":
            target = next(r for r in case["crm"] if r["id"] == resolution["entity_id"])
            if any(c["entity_type"] != target["entity_type"] for c in answer["candidates"]):
                raise ValueError("Gold candidate and matched record have different types")
    return {"cases": len(cases), "labels": len(labels), "sources": len(seen), "status": "valid"}


def grouped_split(cases: list[dict], seed: int = 20261115) -> dict[str, str]:
    """Keep connected identity/source groups together and balance relation counts.

    Greedy assignment need not produce exact proportions with large connected groups;
    the audit reports achieved counts. Input order cannot change the assignment.
    """
    parents = {c["id"]: c["id"] for c in cases}

    def root(key):
        while parents[key] != key:
            parents[key] = parents[parents[key]]
            key = parents[key]
        return key

    owner = {}
    for case in sorted(cases, key=lambda c: c["id"]):
        for key in case["split_keys"]:
            if key in owner:
                parents[root(case["id"])] = root(owner[key])
            owner[key] = case["id"]
    groups = defaultdict(list)
    for case in sorted(cases, key=lambda c: c["id"]):
        groups[root(case["id"])].append(case)
    ordered = list(groups.values())
    rng = random.Random(seed)
    rng.shuffle(ordered)
    ordered.sort(key=len, reverse=True)
    totals = Counter(c["provenance"]["relation"] for c in cases)
    counts = {"dev": Counter(), "test": Counter()}
    assignments = {}
    for group in ordered:
        weights = Counter(c["provenance"]["relation"] for c in group)
        costs = {
            split: sum(
                ((counts[split][r] + n) ** 2 - counts[split][r] ** 2) / totals[r]
                for r, n in weights.items()
            )
            for split in counts
        }
        choices = [s for s in counts if costs[s] == min(costs.values())]
        split = rng.choice(choices)
        counts[split].update(weights)
        assignments.update({c["id"]: split for c in group})
    return assignments


def identity_keys(case: dict) -> set[str]:
    """Names/QIDs for overlap auditing; local record IDs are not identities."""
    keys = set()
    for record in case["crm"]:
        for name in [record["name"], *record.get("aliases", [])]:
            keys.add("identity:" + normalize(name))
        if record.get("organization"):
            keys.add("identity:" + normalize(record["organization"]))
    provenance = case.get("provenance", {})
    for key in ("head_qid", "tail_qid"):
        if key == "tail_qid" and provenance.get("relation") != "P127":
            continue  # Job titles and locations are permitted shared values.
        if provenance.get(key):
            keys.add("qid:" + provenance[key])
    return keys


def audit_split(cases: list[dict], labels: list[dict]) -> dict:
    """Audit actual source/identity overlap as well as authored grouping keys."""
    validation = validate_dataset(cases, labels)
    by_id = {g["case_id"]: g for g in labels}
    keys = defaultdict(set)
    for case in cases:
        if not case.get("split_keys"):
            raise ValueError(f"Missing split groups in {case['id']}")
        keys[case["split"]].update(case["split_keys"])
        keys[case["split"]].update(identity_keys(case))
    overlap = keys["dev"] & keys["test"]
    if overlap:
        raise ValueError(f"Cross-split entity/source/template overlap: {sorted(overlap)}")
    distributions = {}
    for split in ("dev", "test"):
        selected = [c for c in cases if c["split"] == split]
        distributions[split] = {
            "cases": len(selected),
            "origins": dict(Counter(c["origin"] for c in selected)),
            "decisions": dict(Counter(by_id[c["id"]]["decision"] for c in selected)),
            "categories": dict(Counter(c["category"] for c in selected)),
            "templates": sorted(
                {
                    c["provenance"]["template_id"]
                    for c in selected
                    if "template_id" in c["provenance"]
                }
            ),
        }
    return {
        **validation,
        "dataset_version": "2",
        "assignment_seed": 20261115,
        "cross_split_overlap": [],
        "splits": distributions,
        "scope": "Documents, target/owner identities, CRM names/aliases, and synthetic templates; shared cities and role labels are allowed.",
    }
