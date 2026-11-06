"""Score saved predictions after inference. This module never supplies model input."""

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median

from .reporting import write_report
from .resolution import canonical_organization
from .schema import Candidate, normalize, normalize_fact_value, quote_in_source, validate_resolution

SCORING_VERSION = "4"

FIELDS = (
    "entity_type",
    "subject",
    "attribute",
    "value",
    "organization",
    "effective_date",
    "source_id",
)


def field_value(field: str, value, case: dict, candidate: dict):
    if value is None:
        return None
    if field in {"source_id", "effective_date"}:
        return value
    if field == "value":
        return normalize_fact_value(candidate.get("attribute", ""), str(value))
    if field == "organization":
        return canonical_organization(str(value), case["crm"])
    return normalize(str(value))


def crm_write_correct(result: dict, case: dict, gold: dict) -> bool:
    """Check the saved CRM state, independently of the write implementation.

    A matched record keeps its original identity metadata. A new record must also
    have the labelled name/context. Non-persisted extraction metadata is scored
    separately by candidate_exact_match.
    """
    prediction = result["prediction"]
    if result["error"] or prediction["decision"] != "accept" or gold["decision"] != "accept":
        return False
    resolution = prediction["resolution"]
    if any(resolution.get(k) != gold["resolution"].get(k) for k in ("status", "entity_id")):
        return False
    update = next((s["output"] for s in result["stages"] if s["stage"] == "crm_update"), {})
    if not update.get("applied") or update.get("error"):
        return False
    is_new = resolution["status"] == "new"
    target_id = f"new-{case['id']}" if is_new else resolution["entity_id"]
    if update.get("record_id") != target_id:
        return False
    initial = {r["id"]: r for r in case["crm"]}
    records = update.get("crm", [])
    written = {r["id"]: r for r in records}
    if len(written) != len(records) or set(written) != set(initial) | {target_id}:
        return False
    if any(written[key] != record for key, record in initial.items() if key != target_id):
        return False
    target = written[target_id]
    for candidate in gold["candidates"]:
        attribute = candidate["attribute"]
        if target.get("entity_type") != candidate["entity_type"]:
            continue
        if is_new:
            if (
                normalize(target.get("name", "")) != normalize(candidate["subject"])
                or field_value("organization", target.get("organization"), case, candidate)
                != field_value("organization", candidate.get("organization"), case, candidate)
                or target.get("aliases") != []
            ):
                continue
            old_facts = {}
        else:
            if {k: v for k, v in target.items() if k != "facts"} != {
                k: v for k, v in initial[target_id].items() if k != "facts"
            }:
                continue
            old_facts = initial[target_id].get("facts", {})
        facts = target.get("facts", {})
        if {k: v for k, v in facts.items() if k != attribute} != {
            k: v for k, v in old_facts.items() if k != attribute
        }:
            continue
        fact = facts.get(attribute, {})
        if any(
            field_value(k, fact.get(k), case, candidate)
            != field_value(k, candidate.get(k), case, candidate)
            for k in ("value", "effective_date", "source_id")
        ):
            continue
        source = next((s for s in case["sources"] if s["id"] == fact.get("source_id")), None)
        if (
            source
            and source["allowed"]
            and quote_in_source(fact.get("evidence", ""), source["text"])
        ):
            return True
    return False


def rate(numerator: int, denominator: int) -> dict:
    return {
        "numerator": numerator,
        "denominator": denominator,
        "rate": numerator / denominator if denominator else None,
    }


def score_one(result: dict, case: dict, gold: dict) -> dict:
    prediction = result["prediction"]
    # A later failure does not erase a completed extraction; decision and write measures
    # still count it as a pipeline error.
    stages = {s["stage"]: s["output"] for s in result["stages"]}
    extracted = stages.get("direct", stages.get("extraction"))
    predicted, extraction_valid = {}, False
    if isinstance(extracted, dict) and "candidate" in extracted:
        candidate = extracted["candidate"]
        try:
            predicted = Candidate.from_dict(candidate).to_dict() if candidate is not None else {}
            extraction_valid = True
        except (ValueError, TypeError):
            pass
    alternatives = gold["candidates"] or [{}]

    def compare(expected):
        scores = {}
        for field in FIELDS:
            p = field_value(field, predicted.get(field), case, predicted)
            g = field_value(field, expected.get(field), case, expected)
            scores[field] = {
                "tp": int(p is not None and p == g),
                "fp": int(p is not None and p != g),
                "fn": int(g is not None and p != g),
            }
        correct = all(
            field_value(k, predicted.get(k), case, predicted)
            == field_value(k, expected.get(k), case, expected)
            for k in FIELDS
        )
        return correct, scores

    compared = [compare(c) for c in alternatives]
    candidate_correct, fields = max(
        compared, key=lambda c: (c[0], sum(v["tp"] for v in c[1].values()))
    )
    resolution = stages.get("resolution")
    if result["strategy"] == "direct" and isinstance(extracted, dict):
        resolution = extracted.get("resolution")
    try:
        validate_resolution(resolution)
    except (ValueError, TypeError):  # raw model output, e.g. an unhashable status
        resolution = None
    resolution_correct = resolution is not None and all(
        resolution.get(k) == gold["resolution"].get(k) for k in ("status", "entity_id")
    )
    source = next((s for s in case["sources"] if s["id"] == predicted.get("source_id")), None)
    quote_matches = bool(source and quote_in_source(predicted.get("evidence", ""), source["text"]))
    allowed = bool(source and source["allowed"])
    healthy = result["error"] is None
    accepted = prediction["decision"] == "accept"
    update = stages.get("crm_update", {})
    correct_write = crm_write_correct(result, case, gold)
    correct_accept = correct_write and candidate_correct and quote_matches and allowed
    verification = stages.get("verification")
    verification_correct = None
    if healthy and candidate_correct and verification and "verification" in gold:
        verification_correct = all(
            verification.get(k) == v for k, v in gold["verification"].items()
        )
    failure_types = []
    if not healthy:
        failure_types.append("response_error")
    if not extraction_valid or not candidate_correct:
        failure_types.append("extraction")
    if not resolution_correct:
        failure_types.append("entity_resolution")
    if verification_correct is False:
        failure_types.append("verification")
    if predicted and not quote_matches:
        failure_types.append("quote")
    if accepted and not allowed:
        failure_types.append("permission")
    if update.get("error"):
        failure_types.append("write_error")
    if accepted and not correct_write:
        failure_types.append("incorrect_acceptance")
    if not healthy or prediction["decision"] != gold["decision"]:
        failure_types.append("decision")
    return {
        "case_id": case["id"],
        "strategy": result["strategy"],
        "repeat": result.get("repeat", 0),
        "split": case["split"],
        "origin": case["origin"],
        "category": case["category"],
        "condition": case.get("provenance", {}).get("condition", case["category"]),
        "expected_decision": gold["decision"],
        "decision": prediction["decision"],
        "decision_correct": healthy and prediction["decision"] == gold["decision"],
        "candidate_correct": extraction_valid and candidate_correct,
        "resolution_correct": resolution_correct,
        "extraction_valid": extraction_valid,
        "has_candidate": bool(predicted),
        "quote_matches": quote_matches,
        "source_allowed": allowed,
        "accepted": accepted,
        "correct_accept": correct_accept,
        "correct_write": correct_write,
        "write_error": update.get("error"),
        "pipeline_ok": healthy,
        "verification_correct": verification_correct,
        "fields": fields,
        "failures": failure_types,
        "latency_seconds": result["latency_seconds"],
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
        "model_calls": len(result["calls"]),
        "estimated_api_cost_usd": result["model_settings"].get("estimated_api_cost_usd"),
    }


def summarize(rows: list[dict]) -> dict:
    n = len(rows)
    accepts = sum(r["accepted"] for r in rows)
    valid = sum(r["expected_decision"] == "accept" for r in rows)
    correct_writes = sum(r["correct_write"] for r in rows)
    correct_accepts = sum(r["correct_accept"] for r in rows)
    unsafe = [r for r in rows if r["expected_decision"] != "accept"]
    field_counts = {
        field: {count: sum(r["fields"][field][count] for r in rows) for count in ("tp", "fp", "fn")}
        for field in FIELDS
    }
    total = {count: sum(v[count] for v in field_counts.values()) for count in ("tp", "fp", "fn")}
    p = rate(total["tp"], total["tp"] + total["fp"])
    recall = rate(total["tp"], total["tp"] + total["fn"])
    sources = [r for r in rows if r["has_candidate"]]
    verified = [r for r in rows if r.get("verification_correct") is not None]
    return {
        "cases": n,
        "decision_accuracy": rate(sum(r["decision_correct"] for r in rows), n),
        "accepted_update_accuracy": rate(correct_writes, accepts),
        "useful_update_coverage": rate(correct_writes, valid),
        "accepted_candidate_accuracy": rate(correct_accepts, accepts),
        "exact_candidate_coverage": rate(correct_accepts, valid),
        "unsafe_case_withholding": rate(
            sum(r["pipeline_ok"] and not r["accepted"] for r in unsafe), len(unsafe)
        ),
        "entity_resolution_accuracy": rate(sum(r["resolution_correct"] for r in rows), n),
        "candidate_exact_match": rate(sum(r["candidate_correct"] for r in rows), n),
        "verification_accuracy_on_correct_candidates": rate(
            sum(r["verification_correct"] for r in verified), len(verified)
        ),
        "quote_match_rate": rate(sum(r["quote_matches"] for r in sources), len(sources)),
        "accepted_source_permission": rate(
            sum(r["accepted"] and r["source_allowed"] for r in rows), accepts
        ),
        "field_precision": p,
        "field_recall": recall,
        "field_f1": 2 * p["rate"] * recall["rate"] / (p["rate"] + recall["rate"])
        if p["rate"] is not None and recall["rate"] is not None and p["rate"] + recall["rate"]
        else 0.0,
        "field_counts": field_counts,
        "pipeline_errors": sum(not r["pipeline_ok"] for r in rows),
        "write_errors": sum(bool(r["write_error"]) for r in rows),
        "accepted_updates": accepts,
        "correct_accepted_updates": correct_writes,
        "correct_accepted_candidates": correct_accepts,
        "latency_mean_seconds": mean(r["latency_seconds"] for r in rows) if rows else None,
        "latency_median_seconds": median(r["latency_seconds"] for r in rows) if rows else None,
        "model_calls": sum(r["model_calls"] for r in rows),
        "input_tokens": known_total(rows, "input_tokens"),
        "output_tokens": known_total(rows, "output_tokens"),
        "estimated_api_cost_usd": known_total(rows, "estimated_api_cost_usd"),
        "failure_counts": dict(Counter(f for r in rows for f in r["failures"])),
        "decision_confusion": dict(
            Counter(
                r["expected_decision"]
                + " -> "
                + (r["decision"] if r["pipeline_ok"] else "pipeline_error")
                for r in rows
            )
        ),
    }


def known_total(rows: list[dict], key: str):
    values = [r.get(key) for r in rows]
    return sum(values) if all(v is not None for v in values) else None


def execution_schedule(configuration: dict) -> set[tuple[str, str, int]]:
    """Every (case, strategy, repeat) a run must contain; repeats cover the repeated subset."""
    ids = configuration["case_ids"]
    repeat_ids = configuration.get("repeat_case_ids", ids)
    return {
        (case_id, strategy, repeat)
        for repeat in range(configuration["repeats"])
        for case_id in (ids if repeat == 0 else repeat_ids)
        for strategy in configuration["strategies"]
    }


# Which method got a paired outcome right: (direct, staged) -> label.
OUTCOMES = {
    (True, True): "both",
    (True, False): "direct_only",
    (False, True): "staged_only",
    (False, False): "neither",
}


def paired_comparison(rows: list[dict]) -> tuple[dict, list[dict]]:
    """Case-by-case counts of which method got each outcome right."""
    methods = {
        s: {r["case_id"]: r for r in rows if r["strategy"] == s} for s in ("direct", "staged")
    }
    if not all(methods.values()):
        return {"status": "requires_both_strategies"}, []
    pairs = []
    for case_id in sorted(methods["direct"]):
        direct = methods["direct"][case_id]
        pairs.append(
            {
                "case_id": case_id,
                "origin": direct["origin"],
                "category": direct["category"],
                "expected_decision": direct["expected_decision"],
                **{
                    s + "_" + k: methods[s][case_id][k]
                    for s in methods
                    for k in (
                        "decision",
                        "correct_write",
                        "decision_correct",
                        "accepted",
                        "pipeline_ok",
                        "latency_seconds",
                    )
                },
            }
        )

    def table(selected, field):
        outcomes = Counter(
            OUTCOMES[bool(r["direct_" + field]), bool(r["staged_" + field])] for r in selected
        )
        return {"cases": len(selected), **outcomes}

    return {
        "status": "paired",
        "cases": len(pairs),
        "correct_write_on_useful_cases": table(
            [r for r in pairs if r["expected_decision"] == "accept"], "correct_write"
        ),
        "correct_decision": table(pairs, "decision_correct"),
        "acceptance_on_unsafe_cases": table(
            [r for r in pairs if r["expected_decision"] != "accept"], "accepted"
        ),
        "interpretation": "Counts use primary executions only. Acceptance on a review/reject case is an error.",
    }, pairs


def consistency(results: list[dict]) -> dict:
    grouped = defaultdict(list)
    for result in results:
        grouped[(result["strategy"], result["case_id"])].append(result)
    summaries = {}
    for strategy in sorted({r["strategy"] for r in results}):
        comparisons, same, errored = 0, 0, 0
        for (method, _), group in grouped.items():
            if method != strategy or len(group) < 2:
                continue
            group = sorted(group, key=lambda r: r.get("repeat", 0))
            base = group[0]["prediction"]
            for result in group[1:]:
                other = result["prediction"]
                comparisons += 1
                errored += group[0]["error"] is not None or result["error"] is not None
                same += bool(
                    group[0]["error"] is None
                    and result["error"] is None
                    and all(base.get(k) == other.get(k) for k in ("candidate", "decision"))
                    and all(
                        base["resolution"].get(k) == other["resolution"].get(k)
                        for k in ("status", "entity_id")
                    )
                )
        summaries[strategy] = {
            **rate(same, comparisons),
            "errored_comparisons": errored,
            "agreement_on_healthy_comparisons": rate(same, comparisons - errored),
        }
    return summaries


def validate_results(
    results: list[dict], configuration: dict | None = None, *, complete=True
) -> None:
    """Check that saved results are one run: no duplicates, one setting, the planned schedule."""
    keys = [(r["case_id"], r["strategy"], r.get("repeat", 0)) for r in results]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate case/strategy/repeat in saved results")
    versions = {(r["prompt_version"], r.get("workflow_version")) for r in results}
    if len(versions) > 1 or any(
        r["model_settings"] != results[0]["model_settings"] for r in results
    ):
        raise ValueError("Saved results mix models, settings, prompts, or workflows")
    if not configuration:
        return
    if results:
        planned = (configuration["prompt_version"], configuration.get("workflow_version"))
        settings = results[0]["model_settings"]
        if versions != {planned} or any(
            settings.get(k) != configuration[k]
            for k in ("backend", "model", "max_tokens", "temperature", "base_url")
            if k in configuration
        ):
            raise ValueError("Saved result settings differ from the run configuration")
    schedule = execution_schedule(configuration)
    if not set(keys) <= schedule or (complete and set(keys) != schedule):
        raise ValueError("Results do not match the case/strategy/repeat schedule in run.json")


def evaluate(
    results: list[dict], cases: list[dict], labels: list[dict], configuration: dict | None = None
) -> tuple[dict, list[dict]]:
    validate_results(results, configuration)
    case_by_id = {c["id"]: c for c in cases}
    gold_by_id = {g["case_id"]: g for g in labels}
    rows = [score_one(r, case_by_id[r["case_id"]], gold_by_id[r["case_id"]]) for r in results]
    # Repeats are used for consistency, not to inflate the main sample size.
    primary = [r for r in rows if r["repeat"] == 0]
    summary = {
        "scoring_version": SCORING_VERSION,
        "dataset_version": results[0].get("dataset_version", "1") if results else None,
        "annotation_revisions": sorted(
            {gold_by_id[r["case_id"]].get("annotation_revision", "1") for r in results}
        ),
        "prompt_version": results[0]["prompt_version"] if results else None,
        "workflow_version": results[0].get("workflow_version", "1") if results else None,
        "execution_counts": {
            "primary": len(primary),
            "repeated": len(rows) - len(primary),
            "total": len(rows),
        },
        "all_execution_overhead": {},
        "overall": {},
        "by_split": {},
        "by_origin": {},
        "by_category": {},
        "by_condition": {},
        "consistency": consistency(results),
    }
    for strategy in sorted({r["strategy"] for r in primary}):
        selected = [r for r in primary if r["strategy"] == strategy]
        all_rows = [r for r in rows if r["strategy"] == strategy]
        summary["all_execution_overhead"][strategy] = {
            "executions": len(all_rows),
            "model_calls": sum(r["model_calls"] for r in all_rows),
            **{
                key: known_total(all_rows, key)
                for key in (
                    "input_tokens",
                    "output_tokens",
                    "estimated_api_cost_usd",
                    "latency_seconds",
                )
            },
        }
        summary["overall"][strategy] = summarize(selected)
        for field, key in (
            ("split", "by_split"),
            ("origin", "by_origin"),
            ("category", "by_category"),
            ("condition", "by_condition"),
        ):
            summary[key][strategy] = {
                value: summarize([r for r in selected if r[field] == value])
                for value in sorted({r[field] for r in selected})
            }
    summary["paired_comparison"], _ = paired_comparison(primary)
    return summary, rows


def write_scores(directory: Path, summary: dict, rows: list[dict]) -> None:
    (directory / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    if rows:
        columns = [k for k in rows[0] if k != "fields"]
        with (directory / "scores.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
            writer.writeheader()
            writer.writerows(
                {k: json.dumps(r[k]) if isinstance(r[k], list) else r[k] for k in columns}
                for r in rows
            )
    _, pairs = paired_comparison([r for r in rows if r["repeat"] == 0])
    if pairs:
        with (directory / "paired_cases.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(pairs[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(pairs)
    if rows:
        write_report(directory, summary, rows)
