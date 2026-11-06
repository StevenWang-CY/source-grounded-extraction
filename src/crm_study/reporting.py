"""Readable reports derived from the same scoring pass as JSON and CSV outputs."""

from pathlib import Path

from .schema import write_jsonl

RATES = [
    ("Correct writes / accept decisions", "accepted_update_accuracy"),
    ("Useful updates written", "useful_update_coverage"),
    ("Exact candidate acceptance", "accepted_candidate_accuracy"),
    ("Correct decisions", "decision_accuracy"),
    ("Entity resolution", "entity_resolution_accuracy"),
    ("Evidence flags right on correct candidates", "verification_accuracy_on_correct_candidates"),
    ("Field precision", "field_precision"),
    ("Field recall", "field_recall"),
    ("Review/reject cases withheld", "unsafe_case_withholding"),
    ("Quotation found in the cited source", "quote_match_rate"),
    ("Accepted updates from allowed sources", "accepted_source_permission"),
]
COUNTS = [
    ("Cases", "cases"),
    ("Model calls (attempted)", "model_calls"),
    ("Input tokens", "input_tokens"),
    ("Output tokens", "output_tokens"),
    ("Invalid responses", "pipeline_errors"),
]
PAIRED = [
    ("Wrote a useful update", "correct_write_on_useful_cases"),
    ("Correct decision", "correct_decision"),
    ("Accepted a review/reject case", "acceptance_on_unsafe_cases"),
]


def fraction(value):
    if value["rate"] is None:
        return f"n/a ({value['numerator']}/{value['denominator']})"
    return f"{value['numerator']}/{value['denominator']} ({value['rate']:.1%})"


def row(*cells) -> str:
    return "| " + " | ".join(map(str, cells)) + " |"


def write_report(directory: Path, summary: dict, rows: list[dict]) -> None:
    primary = [r for r in rows if r["repeat"] == 0]
    splits = sorted({r["split"] for r in primary})
    overall = summary["overall"]
    methods = sorted(overall)
    lines = [
        "# CRM workflow comparison",
        "",
        f"{len({r['case_id'] for r in primary})} cases; split: "
        + ", ".join("development" if s == "dev" else s for s in splits)
        + ".",
        "",
        "## Primary executions",
        "",
        row("Measure", *methods),
        row("---", *["---:"] * len(methods)),
    ]
    lines += [row(name, *(fraction(overall[m][key]) for m in methods)) for name, key in RATES]
    lines += [row(name, *(overall[m][key] for m in methods)) for name, key in COUNTS]
    latency = (f"{overall[m]['latency_mean_seconds']:.2f}" for m in methods)
    lines.append(row("Mean time per case, seconds", *latency))
    lines += [
        "",
        "Writes are scored from the saved CRM state. Candidate scores cover extracted fields, quote matching checks the cited text, and verification scores check support/date/conflict flags on correct candidates.",
        "",
        "## Public and synthetic cases",
        "",
        row(
            "Origin",
            "Method",
            "Cases",
            "Correct writes / accept decisions",
            "Useful updates written",
        ),
        row("---", "---", "---:", "---:", "---:"),
    ]
    for method in methods:
        for origin, scores in summary["by_origin"][method].items():
            lines.append(
                row(
                    origin,
                    method,
                    scores["cases"],
                    fraction(scores["accepted_update_accuracy"]),
                    fraction(scores["useful_update_coverage"]),
                )
            )
    pairs = summary["paired_comparison"]
    if pairs["status"] == "paired":
        lines += [
            "",
            "## Paired outcomes",
            "",
            row("Outcome", "Cases", "Both", "Direct only", "Staged only", "Neither"),
            row("---", *["---:"] * 5),
        ]
        for name, key in PAIRED:
            outcome = (
                pairs[key].get(k, 0) for k in ("both", "direct_only", "staged_only", "neither")
            )
            lines.append(row(name, pairs[key]["cases"], *outcome))
    lines += ["", "## Fresh repeats and overhead", ""]
    for method in methods:
        cost = summary["all_execution_overhead"][method]["estimated_api_cost_usd"]
        repeats = summary["consistency"][method]
        lines.append(
            f"- {method}: repeat agreement {fraction(repeats)}; {repeats['errored_comparisons']} repeated pair(s) with an invalid response, which count as disagreements. Billed API cost: {cost if cost is not None else 'unknown'} USD."
        )
    counts = summary["execution_counts"]
    lines += [
        "",
        f"{counts['primary']} primary executions and {counts['repeated']} fresh repeats. Main measures use primary executions.",
        "",
        "## Failure analysis",
        "",
        row("Method", "Failure type", "Count"),
        row("---", "---", "---:"),
    ]
    for method in methods:
        for failure, count in sorted(overall[method]["failure_counts"].items()):
            lines.append(row(method, failure, count))
    lines += [
        "",
        "Counts can overlap. See `errors.jsonl` for affected cases, `paired_cases.csv` for the comparison, and `crm-study inspect` for the original trace. Inputs, answers, responses, and model settings are saved with the run.",
    ]
    (directory / "report.md").write_text("\n".join(lines) + "\n")
    write_jsonl(directory / "errors.jsonl", [r for r in primary if r["failures"]])
