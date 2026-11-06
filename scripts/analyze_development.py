"""Build the development analysis behind the progress update.

Everything here reads saved results. The only model calls beyond the two development runs
are in results/verifier-check, made by scripts/check_verifier.py. Writes
results/analysis/development.json and a readable copy of its tables in development.md.
"""

import json
import re
from collections import Counter
from pathlib import Path

from crm_study.evaluation import evaluate, score_one, summarize
from crm_study.schema import parse_json_response, read_jsonl
from crm_study.stats import exact_mcnemar, paired_difference_interval, wilson_interval
from crm_study.variants import candidate_only, from_answer_key, without_verifier

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "results/development"
SECOND_RUN = ROOT / "results/development-rerun"
VERIFIER_CHECK = ROOT / "results/verifier-check"
OUTPUT = ROOT / "results/analysis"
METHODS = ("direct", "staged")

# The decision rule written for each kind of review/reject case.
INTENDED_STOP = {
    "ambiguous_identity": "ambiguous_identity",
    "conflicting_sources": "conflicting_sources",
    "disallowed_source": "source_not_allowed",
    "duplicate_records": "ambiguous_identity",
    "explicit_denial": "claim_contradicted",
    "future_update": "future_update",
    "irrelevant_document": "no_candidate",
    "same_date_conflict": "same_date_conflict",
    "stale_update": "stale_update",
    "tentative_claim": "support_uncertain",
    "undated_conflict": "undated_conflict",
}

# Staged failures on useful cases, grouped by reading each saved trace.
STAGED_FAILURES = {
    "Effective date not stated in the source": {
        "wrong": ["fewrel-p127-0072", "scenario-14-1", "scenario-14-2"],
        "missed": [],
        "example": "“August 2015” stored as 2015-08-01",
    },
    "Duplicate identity": {
        "wrong": ["fewrel-p159-0303"],
        "missed": [],
        "example": "“UAL Corporation” added beside the UAL record",
    },
    "Wrong attribute": {
        "wrong": ["scenario-17-1"],
        "missed": [],
        "example": "“working” stored as a role for an employer update",
    },
    "Entity type does not fit the attribute": {
        "wrong": [],
        "missed": ["fewrel-p127-0102", "fewrel-p159-0287", "fewrel-p159-0317"],
        "example": "“organization” returned as the entity type of a company",
    },
    "No candidate returned": {
        "wrong": [],
        "missed": ["fewrel-p39-0030", "fewrel-p39-0032", "fewrel-p39-0039"],
        "example": "No role found in “Attorney General Jeff Sessions”",
    },
    "Organization left out": {
        "wrong": [],
        "missed": ["scenario-02-2"],
        "example": "“BL” not returned as Pavel Reeve's organization",
    },
}


class Run:
    """One saved run with its answer keys. `first` holds the executions that are not repeats."""

    def __init__(self, directory: Path, answers: list[dict]):
        self.cases = read_jsonl(directory / "cases.jsonl")
        self.answers = answers
        self.gold = {a["case_id"]: a for a in answers}
        self.saved = read_jsonl(directory / "predictions.jsonl")
        self.first = {(r["case_id"], r["strategy"]): r for r in self.saved if r["repeat"] == 0}

    def first_response(self, case: dict, strategy: str) -> str:
        return self.first[case["id"], strategy]["calls"][0]["text"]

    def score(self, case: dict, result: dict) -> dict:
        return score_one({**result, "repeat": 0}, case, self.gold[case["id"]])

    def needs_withholding(self, case: dict) -> bool:
        return self.gold[case["id"]]["decision"] != "accept"


def condition(case: dict) -> str:
    return case["provenance"].get("condition", case["category"])


def with_interval(numerator: int, denominator: int) -> dict:
    low, high = wilson_interval(numerator, denominator)
    return {"count": numerator, "total": denominator, "low": low, "high": high}


def share(rate: dict) -> dict:
    return {"count": rate["numerator"], "total": rate["denominator"]}


def unsafe_accepted(rows: list[dict]) -> int:
    return sum(r["accepted"] and r["expected_decision"] != "accept" for r in rows)


def main_measures(summary: dict, rows: dict, answers: list[dict]) -> dict:
    useful = sum(a["decision"] == "accept" for a in answers)
    table = {}
    for method in METHODS:
        scores = summary["overall"][method]
        correct = scores["correct_accepted_updates"]
        table[method] = {
            "accepted_accuracy": with_interval(correct, scores["accepted_updates"]),
            "useful_coverage": with_interval(correct, useful),
            "unsafe_accepted": with_interval(unsafe_accepted(rows[method]), len(answers) - useful),
            "decisions": with_interval(scores["decision_accuracy"]["numerator"], len(answers)),
            "invalid": scores["pipeline_errors"],
        }
    return table


def paired_measures(summary: dict) -> dict:
    paired = summary["paired_comparison"]
    table = {}
    for name, key in (
        ("decision", "correct_decision"),
        ("unsafe", "acceptance_on_unsafe_cases"),
        ("useful", "correct_write_on_useful_cases"),
    ):
        direct_only = paired[key].get("direct_only", 0)
        staged_only = paired[key].get("staged_only", 0)
        table[name] = {
            "direct_only": direct_only,
            "staged_only": staged_only,
            "p": exact_mcnemar(direct_only, staged_only),
            "difference_interval": paired_difference_interval(
                direct_only, staged_only, paired[key]["cases"]
            ),
        }
    return table


def step_measures(summary: dict) -> dict:
    return {
        method: {
            "resolution": share(scores["entity_resolution_accuracy"]),
            "quote": share(scores["quote_match_rate"]),
            "allowed": share(scores["accepted_source_permission"]),
            "verification": share(scores["verification_accuracy_on_correct_candidates"]),
            "model_calls": scores["model_calls"],
            "input_tokens": scores["input_tokens"],
            "output_tokens": scores["output_tokens"],
            "seconds": scores["latency_mean_seconds"],
        }
        for method, scores in summary["overall"].items()
    }


def field_table(rows: list[dict], cases: dict) -> dict:
    """Precision and recall for the fields the proposal names, with values split by attribute."""

    def totals(selected, field):
        found = {k: sum(r["fields"][field][k] for r in selected) for k in ("tp", "fp", "fn")}
        return {
            "correct": found["tp"],
            "extracted": found["tp"] + found["fp"],
            "expected": found["tp"] + found["fn"],
        }

    def asks_role(row):
        query = cases[row["case_id"]]["query"]
        attribute = re.search(r"role|employer|headquarters|owned_by|deal_company", query).group()
        return attribute == "role"

    return {
        "Names": totals(rows, "subject"),
        "Roles": totals([r for r in rows if asks_role(r)], "value"),
        "Relationships": totals([r for r in rows if not asks_role(r)], "value"),
        "Organizations": totals(rows, "organization"),
        "Effective dates": totals(rows, "effective_date"),
    }


def origin_counts(summary: dict, run: Run) -> dict:
    return {
        method: {
            origin: {
                "correct": scores["correct_accepted_updates"],
                "useful": sum(
                    run.gold[c["id"]]["decision"] == "accept"
                    for c in run.cases
                    if c["origin"] == origin
                ),
            }
            for origin, scores in summary["by_origin"][method].items()
        }
        for method in METHODS
    }


def variant_row(name: str, rows: list[dict]) -> dict:
    scores = summarize(rows)
    return {
        "name": name,
        "accepted": scores["accepted_updates"],
        "correct": scores["correct_accepted_updates"],
        "unsafe_accepted": unsafe_accepted(rows),
        "decisions": scores["decision_accuracy"]["numerator"],
        "invalid": scores["pipeline_errors"],
    }


def direct_candidate_results(run: Run) -> dict:
    return {
        c["id"]: without_verifier(c, candidate_only(run.first_response(c, "direct")))
        for c in run.cases
    }


def staged_extraction_results(run: Run) -> dict:
    return {c["id"]: without_verifier(c, run.first_response(c, "staged")) for c in run.cases}


def stage_chain(run: Run) -> list[dict]:
    """The steps from direct to the full staged workflow, on one run's saved responses."""

    def rows(results):
        return [run.score(c, results[c["id"]]) for c in run.cases]

    def saved(strategy):
        return {c["id"]: run.first[c["id"], strategy] for c in run.cases}

    return [
        variant_row("Direct", rows(saved("direct"))),
        variant_row(
            "Direct's candidate, Python steps, no verifier", rows(direct_candidate_results(run))
        ),
        variant_row(
            "Staged extraction, Python steps, no verifier", rows(staged_extraction_results(run))
        ),
        variant_row("Full staged workflow", rows(saved("staged"))),
    ]


def review_reject_table(run: Run, checked: dict) -> tuple[dict, dict]:
    """Which rule stopped each review/reject case, and what stopped the rest."""
    table, other_stops = {}, Counter()
    for case in run.cases:
        if not run.needs_withholding(case):
            continue
        intended = INTENDED_STOP[condition(case)]
        direct = run.first[case["id"], "direct"]["prediction"]
        staged = run.first[case["id"], "staged"]["prediction"]
        row = table.setdefault(
            condition(case),
            {"cases": 0, "direct_accepted": 0, "staged_accepted": 0, "intended": 0, "checked": 0},
        )
        row["cases"] += 1
        row["direct_accepted"] += direct["decision"] == "accept"
        row["staged_accepted"] += staged["decision"] == "accept"
        row["intended"] += staged["reason"] == intended
        row["checked"] += checked[case["id"]]["prediction"].get("reason") == intended
        if staged["reason"] != intended:
            other_stops[staged["reason"]] += 1
    return dict(sorted(table.items())), dict(other_stops.most_common())


def direct_choices(run: Run) -> dict:
    """What the direct responses chose, including the ones that failed validation."""
    choices = Counter()
    for case in run.cases:
        decision = parse_json_response(run.first_response(case, "direct"))["decision"]
        valid = run.first[case["id"], "direct"]["error"] is None
        choices[f"{'valid' if valid else 'invalid'} {decision}"] += 1
    return dict(choices)


def invalid_kinds(results: list[dict]) -> dict:
    """Invalid responses that fail only on the match, and those with an invalid candidate."""
    errors = [r["error"] for r in results if r["error"]]
    match = sum("resolution" in error for error in errors)
    return {"match": match, "candidate": len(errors) - match}


def direct_candidate_effects(run: Run, direct_rows: list[dict]) -> dict:
    """What the first variant changes besides moving the decision into Python."""
    results = direct_candidate_results(run)
    rescored = {c["id"]: run.score(c, results[c["id"]]) for c in run.cases}
    before = {r["case_id"]: r for r in direct_rows}
    invalid = [c["id"] for c in run.cases if run.first[c["id"], "direct"]["error"]]
    lost = [i for i in rescored if before[i]["correct_write"] and not rescored[i]["correct_write"]]
    by_id = {c["id"]: c for c in run.cases}
    for case_id in lost:
        # Each loss: the model stated an organization and the CRM record has none.
        prediction = results[case_id]["prediction"]
        assert prediction["reason"] == "ambiguous_identity"
        assert prediction["candidate"]["organization"]
        assert not by_id[case_id]["crm"][0].get("organization")
    return {
        "became_valid": sum(rescored[i]["pipeline_ok"] for i in invalid),
        "unsafe_accepted_from_them": unsafe_accepted([rescored[i] for i in invalid]),
        "lost_useful": len(lost),
        "gained_useful": sum(
            rescored[i]["correct_write"] and not before[i]["correct_write"] for i in rescored
        ),
    }


def extra_stops_with_staged_extraction(run: Run) -> dict:
    """Why cases accepted on direct's candidates are stopped on staged's extraction."""
    on_direct, on_staged = direct_candidate_results(run), staged_extraction_results(run)
    stops = Counter(
        on_staged[c["id"]]["prediction"]["reason"]
        for c in run.cases
        if run.needs_withholding(c)
        and on_direct[c["id"]]["prediction"]["decision"] == "accept"
        and on_staged[c["id"]]["prediction"]["decision"] != "accept"
    )
    return dict(stops.most_common())


def wrong_writes_verifier_supported(run: Run, staged_rows: list[dict]) -> int:
    """Check the failure groups against the saved run, and count what the verifier let through."""
    wrong = sorted(r["case_id"] for r in staged_rows if r["accepted"] and not r["correct_write"])
    missed = sorted(
        r["case_id"]
        for r in staged_rows
        if r["expected_decision"] == "accept" and not r["accepted"]
    )
    assert wrong == sorted(i for g in STAGED_FAILURES.values() for i in g["wrong"])
    assert missed == sorted(i for g in STAGED_FAILURES.values() for i in g["missed"])

    def support(case_id):
        stages = run.first[case_id, "staged"]["stages"]
        return next(s["output"] for s in stages if s["stage"] == "verification")["support"]

    return sum(support(i) == "supported" for i in wrong)


def same_responses(first: dict, second: dict) -> bool:
    return [c["text"] for c in first["calls"]] == [c["text"] for c in second["calls"]]


def same_outcome(first: dict, second: dict) -> bool:
    """The same validity, candidate, record match, and decision. Free-text reasons may differ."""
    a, b = first["prediction"], second["prediction"]
    return (
        (first["error"] is None) == (second["error"] is None)
        and a.get("candidate") == b.get("candidate")
        and a["decision"] == b["decision"]
        and all(a["resolution"].get(k) == b["resolution"].get(k) for k in ("status", "entity_id"))
    )


def consistency(saved: list[dict], rerun: list[dict]) -> dict:
    def by_key(results):
        return {(r["case_id"], r["strategy"], r["repeat"]): r for r in results}

    def repeats_same(runs):
        repeated = [r for key, r in runs.items() if key[2] == 1]
        return sum(same_responses(r, runs[r["case_id"], r["strategy"], 0]) for r in repeated)

    first, second = by_key(saved), by_key(rerun)
    return {
        "repeated_executions": sum(key[2] == 1 for key in first),
        "repeats_same_first_run": repeats_same(first),
        "repeats_same_second_run": repeats_same(second),
        "executions": len(first),
        "same_responses": sum(same_responses(r, second[k]) for k, r in first.items()),
        "same_outcomes": sum(same_outcome(r, second[k]) for k, r in first.items()),
    }


def main():
    answers = read_jsonl(RUN / "reviewed/answers.jsonl")
    run = Run(RUN, answers)
    configuration = json.loads((RUN / "run.json").read_text())["configuration"]
    summary, all_rows = evaluate(run.saved, run.cases, answers, configuration)
    rows = {m: [r for r in all_rows if r["repeat"] == 0 and r["strategy"] == m] for m in METHODS}
    by_id = {c["id"]: c for c in run.cases}

    check = read_jsonl(VERIFIER_CHECK / "predictions.jsonl")
    check_summary, check_rows = evaluate(check, run.cases, answers)
    review_reject, other_stops = review_reject_table(run, {r["case_id"]: r for r in check})

    second = Run(SECOND_RUN, read_jsonl(SECOND_RUN / "answers.jsonl"))
    second_scores = json.loads((SECOND_RUN / "summary.json").read_text())["overall"]
    original = json.loads((RUN / "summary.json").read_text())["overall"]

    analysis = {
        "main": main_measures(summary, rows, answers),
        "paired": paired_measures(summary),
        "stages": step_measures(summary),
        "fields": {m: field_table(rows[m], by_id) for m in METHODS},
        "origins": origin_counts(summary, run),
        "direct_choices": direct_choices(run),
        "invalid_kinds": {
            m: invalid_kinds([run.first[c["id"], m] for c in run.cases]) for m in METHODS
        },
        "from_direct_candidates": direct_candidate_effects(run, rows["direct"]),
        "extra_stops_with_staged_extraction": extra_stops_with_staged_extraction(run),
        "wrong_writes_verifier_called_supported": wrong_writes_verifier_supported(
            run, rows["staged"]
        ),
        "original_answer_key": {m: original[m]["correct_accepted_updates"] for m in METHODS},
        "variants": stage_chain(run),
        "variants_second_run": stage_chain(second),
        "verifier_check": {
            **variant_row("Answer-key candidate, model verifier, Python steps", check_rows),
            "model_calls": check_summary["overall"]["staged"]["model_calls"],
        },
        "answer_key_check": variant_row(
            "Answer-key candidate and flags, Python steps",
            [run.score(c, from_answer_key(c, run.gold[c["id"]])) for c in run.cases],
        ),
        "review_reject": review_reject,
        "other_stops": other_stops,
        "staged_failures": STAGED_FAILURES,
        "consistency": consistency(run.saved, second.saved),
        "second_run": {
            m: {
                "correct": second_scores[m]["correct_accepted_updates"],
                "accepted": second_scores[m]["accepted_updates"],
                "seconds": second_scores[m]["latency_mean_seconds"],
            }
            for m in METHODS
        },
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "development.json").write_text(json.dumps(analysis, indent=2) + "\n")
    (OUTPUT / "development.md").write_text(markdown(analysis))
    print(f"Wrote {OUTPUT.relative_to(ROOT)}/development.json and development.md.")


def table(header: list[str], rows: list[list]) -> list[str]:
    def line(cells):
        return "| " + " | ".join(str(c) for c in cells) + " |"

    return [line(header), line(["---"] + ["---:"] * (len(header) - 1)), *map(line, rows), ""]


def markdown(a: dict) -> str:
    def rate(row):
        return f"{row['count']}/{row['total']} ({row['low']:.0%}–{row['high']:.0%})"

    def main_row(name, key):
        return [name, *(rate(a["main"][m][key]) for m in METHODS)]

    def fraction(method, name, total):
        field = a["fields"][method][name]
        return f"{field['correct']}/{field[total]}"

    def variant_cells(row):
        return [
            row["name"],
            f"{row['correct']}/{row['accepted']}",
            f"{row['correct']}/38",
            f"{row['unsafe_accepted']}/28",
            f"{row['decisions']}/66",
            row["invalid"],
        ]

    variant_header = [
        "Variant",
        "Correct writes / accept decisions",
        "Useful updates written",
        "Review/reject cases accepted",
        "Correct decisions",
        "Invalid responses",
    ]
    c = a["consistency"]
    return "\n".join(
        [
            "# Development analysis",
            "",
            "Written by `scripts/analyze_development.py` from the saved runs.",
            "",
            "## Main measures, with 95% Wilson intervals",
            "",
            *table(
                ["Measure", "Direct", "Staged"],
                [
                    main_row("Correct writes / accept decisions", "accepted_accuracy"),
                    main_row("Useful updates written", "useful_coverage"),
                    main_row("Review/reject cases accepted", "unsafe_accepted"),
                    main_row("Correct decisions", "decisions"),
                    ["Invalid responses", *(a["main"][m]["invalid"] for m in METHODS)],
                ],
            ),
            "## Paired by case, exact McNemar test",
            "",
            *table(
                ["Outcome", "Direct only", "Staged only", "p"],
                [
                    [name, row["direct_only"], row["staged_only"], f"{row['p']:.4f}"]
                    for name, row in (
                        ("Correct decision", a["paired"]["decision"]),
                        ("Accepted a review/reject case", a["paired"]["unsafe"]),
                        ("Wrote a useful update", a["paired"]["useful"]),
                    )
                ],
            ),
            "## Fields",
            "",
            *table(
                ["Field", "Direct precision", "Direct recall", "Staged precision", "Staged recall"],
                [
                    [
                        name,
                        fraction("direct", name, "extracted"),
                        fraction("direct", name, "expected"),
                        fraction("staged", name, "extracted"),
                        fraction("staged", name, "expected"),
                    ]
                    for name in a["fields"]["direct"]
                ],
            ),
            "## What each stage contributes",
            "",
            "Python steps means matching and the decision rules.",
            "",
            *table(
                variant_header,
                [
                    *map(variant_cells, a["variants"]),
                    variant_cells(a["verifier_check"]),
                    variant_cells(a["answer_key_check"]),
                ],
            ),
            "The same steps on the second Mac:",
            "",
            *table(variant_header, list(map(variant_cells, a["variants_second_run"]))),
            "## Review/reject cases",
            "",
            *table(
                [
                    "Kind of case",
                    "Cases",
                    "Direct accepted",
                    "Staged accepted",
                    "Stopped by the intended rule",
                    "Same, on answer-key candidates",
                ],
                [
                    [
                        name.replace("_", " "),
                        r["cases"],
                        r["direct_accepted"],
                        r["staged_accepted"],
                        r["intended"],
                        r["checked"],
                    ]
                    for name, r in a["review_reject"].items()
                ],
            ),
            "Other rules that stopped a case: "
            + ", ".join(f"{k} ({v})" for k, v in a["other_stops"].items())
            + ".",
            "",
            "## Staged failures on useful cases",
            "",
            *table(
                ["Group", "Wrong writes", "Missed updates", "Example", "Cases"],
                [
                    [
                        name,
                        len(g["wrong"]),
                        len(g["missed"]),
                        g["example"],
                        ", ".join(f"`{i}`" for i in g["wrong"] + g["missed"]),
                    ]
                    for name, g in a["staged_failures"].items()
                ],
            ),
            "## Consistency",
            "",
            f"Repeated executions matched their first response in {c['repeats_same_first_run']} "
            f"of {c['repeated_executions']} on the first Mac and {c['repeats_same_second_run']} "
            f"of {c['repeated_executions']} on the second. Across the two Macs, "
            f"{c['same_responses']} of {c['executions']} executions gave identical responses, and "
            f"{c['same_outcomes']} gave the same candidate, match, and decision.",
            "",
        ]
    )


if __name__ == "__main__":
    main()
