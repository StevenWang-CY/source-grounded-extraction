"""Build the analysis behind the reports from the saved runs.

Nothing here calls the model. It writes one JSON file and one page of tables per split in
results/analysis (development, test, second-test), and comparisons.json with the runs that
cut across splits: the fixes, the model sizes, and the one-call variants.
"""

import json
import re
from collections import Counter
from pathlib import Path

from crm_study.evaluation import evaluate, score_one, summarize
from crm_study.schema import parse_json_response, read_jsonl
from crm_study.stats import exact_mcnemar, paired_difference_interval, wilson_interval
from crm_study.variants import candidate_only, from_answer_key, lenient_match, without_verifier

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
OUTPUT = RESULTS / "analysis"
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

# Staged failures, grouped by reading each saved trace. "wrong" lists accept decisions that
# did not produce a correct write, and "missed" lists useful updates that were not accepted.
FAILURES = {
    "development": {
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
    },
    "test": {
        "Value includes extra words": {
            "wrong": [
                "fewrel-p127-0035",
                "fewrel-p127-0060",
                "fewrel-p127-0085",
                "fewrel-p159-0174",
            ],
            "missed": [],
            "example": "“Tata Motors of India” stored as the owner",
        },
        "Effective date not stated in the source": {
            "wrong": ["fewrel-p39-0025", "scenario-14-4"],
            "missed": ["fewrel-p127-0037", "fewrel-p127-0103", "fewrel-p127-0114"],
            "example": "“in 1972” stored as 1972-01-01",
        },
        "Identity matching": {
            "wrong": ["fewrel-p159-0041"],
            "missed": ["fewrel-p39-0022", "fewrel-p39-0035", "fewrel-p39-0040"],
            "example": "“Yingke Law Firm” added beside the Yingke record",
        },
        "Conflicting sources not detected": {
            "wrong": ["scenario-06-3", "scenario-06-4"],
            "missed": [],
            "example": "Two allowed sources give different roles from the same date",
        },
        "Quotation altered": {
            "wrong": [],
            "missed": ["fewrel-p39-0024"],
            "example": "“Hafez al - Assad” respelled inside the quotation",
        },
    },
    "second-test": {
        "Value includes extra words": {
            "wrong": ["fewrel-p127-0172", "fewrel-p39-0066"],
            "missed": [],
            "example": "“South African group Steinhoff International” stored as the owner",
        },
        "Wrong subject": {
            "wrong": ["fewrel-p39-0057", "fewrel-p39-0064"],
            "missed": ["fewrel-p39-0061"],
            "example": "The doctor “Adamidi” extracted instead of Abbas II of Egypt",
        },
        "Conflicting sources not detected": {
            "wrong": ["scenario-06-5"],
            "missed": [],
            "example": "A newsletter and a staff directory give different roles",
        },
        "Entity type does not fit the attribute": {
            "wrong": [],
            "missed": [
                "fewrel-p127-0173",
                "fewrel-p127-0186",
                "fewrel-p159-0457",
                "fewrel-p159-0458",
                "fewrel-p159-0522",
            ],
            "example": "“organization” returned as the entity type of the Arab League",
        },
        "No candidate returned": {
            "wrong": [],
            "missed": ["fewrel-p127-0175", "fewrel-p39-0060"],
            "example": "No owner found in “taken over by Virgin Money”",
        },
        "Organization left out": {
            "wrong": [],
            "missed": ["scenario-16-6"],
            "example": "“Fernhill Consulting” not returned as Ivo Duarte's organization",
        },
    },
}

# Each split's main run, the answers it is scored with, and its verifier check.
SPLITS = {
    "development": {
        "title": "Development",
        "run": "development",
        "answers": "development/reviewed/answers.jsonl",
        "verifier_check": "verifier-check",
    },
    "test": {
        "title": "Test",
        "run": "test",
        "answers": "test/answers.jsonl",
        "verifier_check": "verifier-check-test",
    },
    "second-test": {
        "title": "Second test",
        "run": "second-test",
        "answers": "second-test/answers.jsonl",
        "verifier_check": "verifier-check-second-test",
    },
}
# Staged before and after the fixes, on the same machine.
FIXES = {
    "development": ("development-rerun", "fixes-development"),
    "test": ("test", "fixes-test"),
    "second-test": ("second-test-before-fixes", "second-test"),
}
MODELS = {
    "Qwen3-1.7B": "models/qwen3-1.7b",
    "Qwen3-4B": "second-test",
    "Qwen3-8B": "models/qwen3-8b",
    "Qwen3-14B": "models/qwen3-14b",
}
# One-call workflows with Qwen3-4B, as (strategy, development run, second-test run).
ONE_CALL = {
    "Direct": ("direct", "fixes-development", "second-test"),
    "Direct with thinking": (
        "direct",
        "variants/thinking-development",
        "variants/thinking-second-test",
    ),
    "Guided direct": ("guided", "variants/guided-development", "variants/guided-second-test"),
}


class Run:
    """One saved run with its answer keys. `first` holds the executions that are not repeats."""

    def __init__(self, directory: Path, answers: list[dict] | None = None):
        self.directory = directory
        self.cases = read_jsonl(directory / "cases.jsonl")
        self.answers = answers or read_jsonl(directory / "answers.jsonl")
        self.gold = {a["case_id"]: a for a in self.answers}
        self.saved = read_jsonl(directory / "predictions.jsonl")
        self.first = {(r["case_id"], r["strategy"]): r for r in self.saved if r["repeat"] == 0}
        self.workflow = self.saved[0]["workflow_version"]

    def first_response(self, case: dict, strategy: str) -> str:
        return self.first[case["id"], strategy]["calls"][0]["text"]

    def score(self, case: dict, result: dict) -> dict:
        return score_one({**result, "repeat": 0}, case, self.gold[case["id"]])

    def rows(self, strategy: str) -> list[dict]:
        return [self.score(c, self.first[c["id"], strategy]) for c in self.cases]

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


def measures(rows: list[dict]) -> dict:
    """The five main measures for one workflow's rows, with 95% Wilson intervals."""
    scores = summarize(rows)
    useful = sum(r["expected_decision"] == "accept" for r in rows)
    correct = scores["correct_accepted_updates"]
    return {
        "accepted_accuracy": with_interval(correct, scores["accepted_updates"]),
        "useful_coverage": with_interval(correct, useful),
        "unsafe_accepted": with_interval(unsafe_accepted(rows), len(rows) - useful),
        "decisions": with_interval(scores["decision_accuracy"]["numerator"], len(rows)),
        "invalid": scores["pipeline_errors"],
    }


def cost(rows: list[dict]) -> dict:
    scores = summarize(rows)
    return {
        "model_calls": scores["model_calls"],
        "input_tokens": scores["input_tokens"],
        "output_tokens": scores["output_tokens"],
        "seconds": scores["latency_mean_seconds"],
    }


def paired_measures(direct: list[dict], staged: list[dict]) -> dict:
    """Case-by-case counts where only one workflow got an outcome, with exact McNemar tests."""
    staged_by_id = {r["case_id"]: r for r in staged}
    pairs = [(d, staged_by_id[d["case_id"]]) for d in direct]

    def compare(selected, outcome):
        direct_only = sum(outcome(d) and not outcome(s) for d, s in selected)
        staged_only = sum(outcome(s) and not outcome(d) for d, s in selected)
        return {
            "direct_only": direct_only,
            "staged_only": staged_only,
            "p": exact_mcnemar(direct_only, staged_only),
            "difference_interval": paired_difference_interval(
                direct_only, staged_only, len(selected)
            ),
        }

    useful = [(d, s) for d, s in pairs if d["expected_decision"] == "accept"]
    unsafe = [(d, s) for d, s in pairs if d["expected_decision"] != "accept"]
    return {
        "decision": compare(pairs, lambda r: r["decision_correct"]),
        "unsafe": compare(unsafe, lambda r: r["accepted"]),
        "useful": compare(useful, lambda r: r["correct_write"]),
    }


def step_measures(rows: list[dict]) -> dict:
    scores = summarize(rows)
    return {
        "resolution": share(scores["entity_resolution_accuracy"]),
        "quote": share(scores["quote_match_rate"]),
        "allowed": share(scores["accepted_source_permission"]),
        "verification": share(scores["verification_accuracy_on_correct_candidates"]),
        **cost(rows),
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


def origin_counts(rows: list[dict]) -> dict:
    return {
        origin: {
            "correct": sum(r["correct_write"] for r in rows if r["origin"] == origin),
            "useful": sum(
                r["expected_decision"] == "accept" for r in rows if r["origin"] == origin
            ),
        }
        for origin in sorted({r["origin"] for r in rows})
    }


def variant_row(name: str, rows: list[dict]) -> dict:
    scores = summarize(rows)
    useful = sum(r["expected_decision"] == "accept" for r in rows)
    return {
        "name": name,
        "cases": len(rows),
        "useful": useful,
        "unsafe": len(rows) - useful,
        "accepted": scores["accepted_updates"],
        "correct": scores["correct_accepted_updates"],
        "unsafe_accepted": unsafe_accepted(rows),
        "decisions": scores["decision_accuracy"]["numerator"],
        "invalid": scores["pipeline_errors"],
    }


def lenient_rows(run: Run, strategy: str = "direct") -> list[dict]:
    """One-call responses rescored with any named record ID read as a match."""
    return [
        run.score(c, lenient_match(c, run.first_response(c, strategy), strategy)) for c in run.cases
    ]


def direct_candidate_results(run: Run) -> dict:
    return {
        c["id"]: without_verifier(c, candidate_only(run.first_response(c, "direct")), run.workflow)
        for c in run.cases
    }


def staged_extraction_results(run: Run) -> dict:
    return {
        c["id"]: without_verifier(c, run.first_response(c, "staged"), run.workflow)
        for c in run.cases
    }


def stage_chain(run: Run) -> list[dict]:
    """The steps from direct to the full staged workflow, on one run's saved responses."""

    def rows(results):
        return [run.score(c, results[c["id"]]) for c in run.cases]

    return [
        variant_row("Direct", run.rows("direct")),
        variant_row(
            "Direct's candidate, Python steps, no verifier", rows(direct_candidate_results(run))
        ),
        variant_row(
            "Staged extraction, Python steps, no verifier", rows(staged_extraction_results(run))
        ),
        variant_row("Full staged workflow", run.rows("staged")),
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
        if staged["decision"] != "accept" and staged["reason"] != intended:
            other_stops[staged["reason"]] += 1
    return dict(sorted(table.items())), dict(other_stops.most_common())


def one_call_choices(run: Run, strategy: str = "direct") -> dict:
    """What the one-call responses chose, including the ones that failed validation."""
    choices = Counter()
    for case in run.cases:
        result = run.first[case["id"], strategy]
        try:
            decision = parse_json_response(result["calls"][0]["text"]).get("decision")
        except ValueError:
            decision = None
        if decision not in ("accept", "review", "reject"):
            decision = "unreadable"
        choices[f"{'valid' if result['error'] is None else 'invalid'} {decision}"] += 1
    return dict(sorted(choices.items()))


def invalid_kinds(results: list[dict]) -> dict:
    """Invalid responses that fail only on the match, and those with an invalid candidate."""
    errors = [r["error"] for r in results if r["error"]]
    match = sum("resolution" in error for error in errors)
    return {"match": match, "candidate": len(errors) - match}


def direct_candidate_effects(run: Run) -> dict:
    """What the first variant changes besides moving the decision into Python."""
    results = direct_candidate_results(run)
    rescored = {c["id"]: run.score(c, results[c["id"]]) for c in run.cases}
    before = {r["case_id"]: r for r in run.rows("direct")}
    invalid = [c["id"] for c in run.cases if run.first[c["id"], "direct"]["error"]]
    lost = [i for i in rescored if before[i]["correct_write"] and not rescored[i]["correct_write"]]
    return {
        "became_valid": sum(rescored[i]["pipeline_ok"] for i in invalid),
        "unsafe_accepted_from_them": unsafe_accepted([rescored[i] for i in invalid]),
        "lost_useful": len(lost),
        "lost_reasons": dict(Counter(results[i]["prediction"]["reason"] for i in lost)),
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


def wrong_writes_verifier_supported(run: Run, groups: dict) -> int:
    """Check the failure groups against the saved run, and count what the verifier let through."""
    rows = run.rows("staged")
    wrong = sorted(r["case_id"] for r in rows if r["accepted"] and not r["correct_write"])
    missed = sorted(
        r["case_id"] for r in rows if r["expected_decision"] == "accept" and not r["accepted"]
    )
    assert wrong == sorted(i for g in groups.values() for i in g["wrong"]), wrong
    assert missed == sorted(i for g in groups.values() for i in g["missed"]), missed

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


def by_key(results: list[dict]) -> dict:
    return {(r["case_id"], r["strategy"], r["repeat"]): r for r in results}


def repeats(saved: list[dict]) -> dict:
    """How many repeated executions returned the same responses as their first run."""
    runs = by_key(saved)
    repeated = [r for key, r in runs.items() if key[2] == 1]
    same = sum(same_responses(r, runs[r["case_id"], r["strategy"], 0]) for r in repeated)
    return {"repeated": len(repeated), "same": same}


def across_machines(saved: list[dict], rerun: list[dict]) -> dict:
    first, second = by_key(saved), by_key(rerun)
    return {
        "executions": len(first),
        "same_responses": sum(same_responses(r, second[k]) for k, r in first.items()),
        "same_outcomes": sum(same_outcome(r, second[k]) for k, r in first.items()),
    }


def analyze_split(name: str) -> dict:
    spec = SPLITS[name]
    run = Run(RESULTS / spec["run"], read_jsonl(RESULTS / spec["answers"]))
    rows = {m: run.rows(m) for m in METHODS}
    by_id = {c["id"]: c for c in run.cases}
    check = read_jsonl(RESULTS / spec["verifier_check"] / "predictions.jsonl")
    check_summary, check_rows = evaluate(check, run.cases, run.answers)
    review_reject, other_stops = review_reject_table(run, {r["case_id"]: r for r in check})
    answer_key_rows = [
        run.score(c, from_answer_key(c, run.gold[c["id"]], run.workflow)) for c in run.cases
    ]
    analysis = {
        "split": name,
        "workflow_version": run.workflow,
        "cases": len(run.cases),
        "useful_cases": sum(not run.needs_withholding(c) for c in run.cases),
        "main": {m: measures(rows[m]) for m in METHODS},
        "paired": paired_measures(rows["direct"], rows["staged"]),
        "stages": {m: step_measures(rows[m]) for m in METHODS},
        "fields": {m: field_table(rows[m], by_id) for m in METHODS},
        "origins": {m: origin_counts(rows[m]) for m in METHODS},
        "direct_choices": one_call_choices(run),
        "invalid_kinds": {
            m: invalid_kinds([run.first[c["id"], m] for c in run.cases]) for m in METHODS
        },
        "from_direct_candidates": direct_candidate_effects(run),
        "extra_stops_with_staged_extraction": extra_stops_with_staged_extraction(run),
        "wrong_writes_verifier_called_supported": wrong_writes_verifier_supported(
            run, FAILURES[name]
        ),
        "variants": stage_chain(run),
        "verifier_check": {
            **variant_row("Answer-key candidate, model verifier, Python steps", check_rows),
            "model_calls": check_summary["overall"]["staged"]["model_calls"],
        },
        "answer_key_check": variant_row(
            "Answer-key candidate and flags, Python steps", answer_key_rows
        ),
        "review_reject": review_reject,
        "other_stops": other_stops,
        "staged_failures": FAILURES[name],
        "repeats": repeats(run.saved),
    }
    if name == "development":
        # The development split was also run on a second Mac, and its answer key was revised once.
        second = Run(RESULTS / "development-rerun")
        original = json.loads((run.directory / "summary.json").read_text())["overall"]
        analysis |= {
            "original_answer_key": {m: original[m]["correct_accepted_updates"] for m in METHODS},
            "variants_second_run": stage_chain(second),
            "second_run": {
                m: {**measures(second.rows(m)), **cost(second.rows(m))} for m in METHODS
            },
            "repeats_second_run": repeats(second.saved),
            "across_machines": across_machines(run.saved, second.saved),
        }
    return analysis


def fixes_comparison() -> dict:
    """The staged workflow before and after the four fixes, split by split."""
    table = {}
    for name, (before, after) in FIXES.items():
        answers = read_jsonl(RESULTS / SPLITS[name]["answers"])
        runs = {"before": Run(RESULTS / before, answers), "after": Run(RESULTS / after, answers)}
        assert (runs["before"].workflow, runs["after"].workflow) == ("3", "4")
        scored = {k: {r["case_id"]: r for r in run.rows("staged")} for k, run in runs.items()}
        changed = {}
        for case_id, old in scored["before"].items():
            new = scored["after"][case_id]
            if (old["correct_write"], old["accepted"]) != (new["correct_write"], new["accepted"]):
                kind = (
                    "wrong write to correct write"
                    if old["accepted"] and new["correct_write"]
                    else "not written to correct write"
                    if new["correct_write"]
                    else "wrong write to withheld"
                    if old["accepted"] and not new["accepted"]
                    else "not written to wrong write"
                )
                changed[case_id] = kind
        same_extractions = sum(
            runs["before"].first_response(c, "staged") == runs["after"].first_response(c, "staged")
            for c in runs["before"].cases
        )
        gained = sum(kind.endswith("to correct write") for kind in changed.values())
        lost = sum(
            old["correct_write"] and not scored["after"][case_id]["correct_write"]
            for case_id, old in scored["before"].items()
        )
        table[name] = {
            "before": variant_row(before, list(scored["before"].values())),
            "after": variant_row(after, list(scored["after"].values())),
            "changed": dict(sorted(changed.items())),
            "changes": dict(Counter(changed.values())),
            "correct_writes_gained": gained,
            "correct_writes_lost": lost,
            "p": exact_mcnemar(lost, gained),
            "same_extraction_responses": same_extractions,
        }
    return table


def model_comparison() -> dict:
    """Direct and staged on the second test set for each model size."""
    answers = read_jsonl(RESULTS / SPLITS["second-test"]["answers"])
    table = {}
    for name, directory in MODELS.items():
        if not (RESULTS / directory / "predictions.jsonl").exists():
            continue
        run = Run(RESULTS / directory, answers)
        rows = {m: run.rows(m) for m in METHODS}
        table[name] = {
            "model": run.saved[0]["model_settings"]["model"],
            "main": {m: measures(rows[m]) for m in METHODS},
            "direct_lenient_match": measures(lenient_rows(run)),
            "cost": {m: cost(rows[m]) for m in METHODS},
            "paired": paired_measures(rows["direct"], rows["staged"]),
            "direct_choices": one_call_choices(run),
            "invalid_kinds": {
                m: invalid_kinds([run.first[c["id"], m] for c in run.cases]) for m in METHODS
            },
            "variants": stage_chain(run),
            "repeats": repeats(run.saved),
        }
    return table


def one_call_comparison() -> dict:
    """The one-call workflows with Qwen3-4B, next to staged, on development and the second test."""
    table = {}
    for index, split in ((1, "development"), (2, "second-test")):
        answers = read_jsonl(RESULTS / SPLITS[split]["answers"])
        rows = {}
        for name, spec in ONE_CALL.items():
            if not (RESULTS / spec[index] / "predictions.jsonl").exists():
                continue
            run = Run(RESULTS / spec[index], answers)
            scored = run.rows(spec[0])
            rows[name] = {
                **measures(scored),
                **cost(scored),
                "lenient_match": measures(lenient_rows(run, spec[0])),
                "choices": one_call_choices(run, spec[0]),
                "max_tokens": run.saved[0]["model_settings"]["max_tokens"],
            }
        staged = Run(RESULTS / ONE_CALL["Direct"][index], answers).rows("staged")
        rows["Staged"] = {**measures(staged), **cost(staged)}
        table[split] = rows
    return table


def table(header: list[str], rows: list[list]) -> list[str]:
    def line(cells):
        return "| " + " | ".join(str(c) for c in cells) + " |"

    return [line(header), line(["---"] + ["---:"] * (len(header) - 1)), *map(line, rows), ""]


def with_range(row: dict) -> str:
    return f"{row['count']}/{row['total']} ({row['low']:.0%}–{row['high']:.0%})"


VARIANT_HEADER = [
    "Variant",
    "Correct writes / accept decisions",
    "Useful updates written",
    "Review/reject cases accepted",
    "Correct decisions",
    "Invalid responses",
]


def variant_cells(row: dict) -> list:
    return [
        row["name"],
        f"{row['correct']}/{row['accepted']}",
        f"{row['correct']}/{row['useful']}",
        f"{row['unsafe_accepted']}/{row['unsafe']}",
        f"{row['decisions']}/{row['cases']}",
        row["invalid"],
    ]


def split_markdown(a: dict) -> str:
    def main_row(name, key):
        return [name, *(with_range(a["main"][m][key]) for m in METHODS)]

    def fraction(method, name, total):
        field = a["fields"][method][name]
        return f"{field['correct']}/{field[total]}"

    lines = [
        f"# {SPLITS[a['split']]['title']} analysis",
        "",
        f"Written by `scripts/analyze.py` from the saved run in `results/{SPLITS[a['split']]['run']}/` "
        f"(workflow {a['workflow_version']}).",
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
        "## Steps and cost",
        "",
        *table(
            ["Measure", "Direct", "Staged"],
            [
                ["Entity resolution", *(count(a["stages"][m]["resolution"]) for m in METHODS)],
                [
                    "Quotation found in the cited source",
                    *(count(a["stages"][m]["quote"]) for m in METHODS),
                ],
                [
                    "Accepted updates from allowed sources",
                    *(count(a["stages"][m]["allowed"]) for m in METHODS),
                ],
                [
                    "Evidence flags right on correct candidates",
                    "n/a",
                    count(a["stages"]["staged"]["verification"]),
                ],
                ["Model calls", *(a["stages"][m]["model_calls"] for m in METHODS)],
                ["Input tokens", *(a["stages"][m]["input_tokens"] for m in METHODS)],
                ["Output tokens", *(a["stages"][m]["output_tokens"] for m in METHODS)],
                ["Mean seconds per case", *(f"{a['stages'][m]['seconds']:.2f}" for m in METHODS)],
            ],
        ),
        "What the direct responses chose: "
        + ", ".join(f"{k} ({v})" for k, v in a["direct_choices"].items())
        + ".",
        "",
        "## What each stage contributes",
        "",
        "Python steps means matching and the decision rules.",
        "",
        *table(
            VARIANT_HEADER,
            [
                *map(variant_cells, a["variants"]),
                variant_cells(a["verifier_check"]),
                variant_cells(a["answer_key_check"]),
            ],
        ),
    ]
    if "variants_second_run" in a:
        lines += [
            "The same steps on the second Mac:",
            "",
            *table(VARIANT_HEADER, list(map(variant_cells, a["variants_second_run"]))),
        ]
    lines += [
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
        "## Staged failures",
        "",
        "Wrong writes are accept decisions that did not produce a correct write. Missed updates are "
        "useful updates that were not accepted.",
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
        f"Repeated executions matched their first response in {a['repeats']['same']} of "
        f"{a['repeats']['repeated']}.",
    ]
    if "across_machines" in a:
        c = a["across_machines"]
        lines.append(
            f"On the second Mac the repeats matched in {a['repeats_second_run']['same']} of "
            f"{a['repeats_second_run']['repeated']}. Across the two Macs, {c['same_responses']} of "
            f"{c['executions']} executions gave identical responses, and {c['same_outcomes']} gave "
            "the same candidate, match, and decision."
        )
    return "\n".join(lines) + "\n"


def count(row: dict) -> str:
    return f"{row['count']}/{row['total']}"


def comparisons_markdown(c: dict) -> str:
    lines = [
        "# Comparisons across runs",
        "",
        "Written by `scripts/analyze.py` from the saved runs.",
        "",
        "## The staged workflow before and after the four fixes",
        "",
        "Before is workflow 3 and after is workflow 4, on the same machine. Development and test are "
        "the cases the fixes were written from, and the second test set was built afterwards. "
        "Development before the fixes is the rerun on the M5 Max, so it differs slightly from the "
        "October run in the development table.",
        "",
    ]
    fix_rows = []
    for name, f in c["fixes"].items():
        for label in ("before", "after"):
            row = variant_cells(f[label])
            fix_rows.append([f"{SPLITS[name]['title']}, {label}", *row[1:]])
    lines += table(["Staged", *VARIANT_HEADER[1:]], fix_rows)
    for name, f in c["fixes"].items():
        lines.append(
            f"{SPLITS[name]['title']}: "
            + (", ".join(f"{v} {k}" for k, v in f["changes"].items()) or "no case changed")
            + f". Correct writes gained {f['correct_writes_gained']}, lost {f['correct_writes_lost']} "
            f"(exact McNemar p = {f['p']:.3f})."
        )
    lines += ["", "## Model size, on the second test set", ""]
    model_rows = []
    for name, m in c["models"].items():
        for method in METHODS:
            main = m["main"][method]
            model_rows.append(
                [
                    f"{name}, {method}",
                    with_range(main["accepted_accuracy"]),
                    with_range(main["useful_coverage"]),
                    with_range(main["unsafe_accepted"]),
                    with_range(main["decisions"]),
                    main["invalid"],
                    f"{m['cost'][method]['seconds']:.2f}",
                ]
            )
    lines += table([*VARIANT_HEADER[:1], *VARIANT_HEADER[1:], "Mean seconds per case"], model_rows)
    lines += [
        "Direct again, reading any match that names a record ID as that record. This gives direct "
        "the benefit of the doubt on responses the workflow treats as invalid:",
        "",
        *table(
            ["Model", *VARIANT_HEADER[1:]],
            [
                [
                    name,
                    with_range(m["direct_lenient_match"]["accepted_accuracy"]),
                    with_range(m["direct_lenient_match"]["useful_coverage"]),
                    with_range(m["direct_lenient_match"]["unsafe_accepted"]),
                    with_range(m["direct_lenient_match"]["decisions"]),
                    m["direct_lenient_match"]["invalid"],
                ]
                for name, m in c["models"].items()
            ],
        ),
    ]
    lines += ["What the direct responses chose:", ""]
    lines += [
        f"- {name}: " + ", ".join(f"{k} ({v})" for k, v in m["direct_choices"].items())
        for name, m in c["models"].items()
    ]
    lines += ["", "The steps from direct to staged, for each model:", ""]
    for name, m in c["models"].items():
        lines += [f"{name}", "", *table(VARIANT_HEADER, list(map(variant_cells, m["variants"])))]
    lines += ["## One-call workflows with Qwen3-4B", ""]
    for split, rows in c["one_call"].items():
        lines += [
            SPLITS[split]["title"],
            "",
            *table(
                [
                    "Workflow",
                    *VARIANT_HEADER[1:],
                    "Input tokens",
                    "Output tokens",
                    "Mean seconds per case",
                ],
                [
                    [
                        name,
                        with_range(r["accepted_accuracy"]),
                        with_range(r["useful_coverage"]),
                        with_range(r["unsafe_accepted"]),
                        with_range(r["decisions"]),
                        r["invalid"],
                        r["input_tokens"],
                        r["output_tokens"],
                        f"{r['seconds']:.2f}",
                    ]
                    for name, r in rows.items()
                ],
            ),
        ]
        lines += [
            f"- {name}: " + ", ".join(f"{k} ({v})" for k, v in r["choices"].items())
            for name, r in rows.items()
            if "choices" in r
        ] + [""]
    return "\n".join(lines)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name in SPLITS:
        analysis = analyze_split(name)
        (OUTPUT / f"{name}.json").write_text(json.dumps(analysis, indent=2) + "\n")
        (OUTPUT / f"{name}.md").write_text(split_markdown(analysis))
    comparisons = {
        "fixes": fixes_comparison(),
        "models": model_comparison(),
        "one_call": one_call_comparison(),
    }
    (OUTPUT / "comparisons.json").write_text(json.dumps(comparisons, indent=2) + "\n")
    (OUTPUT / "comparisons.md").write_text(comparisons_markdown(comparisons))
    print(f"Wrote the analysis of {len(SPLITS)} splits and the comparisons to results/analysis.")


if __name__ == "__main__":
    main()
