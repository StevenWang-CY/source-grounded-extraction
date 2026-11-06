"""Command line interface: validate, run, score, inspect, replay, and replay-check."""

import argparse
import json
import os
import random
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .backends import HTTPBackend, MLXBackend, ReplayBackend
from .data import audit_split
from .evaluation import (
    SCORING_VERSION,
    evaluate,
    execution_schedule,
    validate_results,
    write_scores,
)
from .pipeline import WORKFLOW_VERSION, run_case
from .prompts import PROMPT_VERSION
from .schema import read_jsonl, write_jsonl

DEFAULT_CASES = "data/processed/cases.jsonl"
DEFAULT_LABELS = "data/labels/answers.jsonl"
DEFAULT_MODEL = "mlx-community/Qwen3-4B-4bit"


def positive(text: str) -> int:
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return value


def now() -> str:
    return datetime.now(ZoneInfo("America/New_York")).isoformat()


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")


def read_checkpoint(path: Path) -> list[dict]:
    """Saved executions; a last line cut off by an interruption is dropped and rerun."""
    if not path.exists():
        return []
    data = path.read_bytes()
    complete = data[: data.rfind(b"\n") + 1]
    if complete != data:
        path.write_bytes(complete)
    return [json.loads(line) for line in complete.splitlines()]


def validate(args):
    print(json.dumps(audit_split(read_jsonl(args.cases), read_jsonl(args.labels)), indent=2))


def run(args):
    cases = [c for c in read_jsonl(args.cases) if args.split == "all" or c["split"] == args.split]
    if args.case_ids:
        cases = [c for c in cases if c["id"] in args.case_ids]
        if {c["id"] for c in cases} != set(args.case_ids):
            raise SystemExit("Some requested case IDs are not in the selected split")
    cases = cases[: args.limit]
    if not cases:
        raise SystemExit("No cases selected")
    if args.repeat_case_ids and not set(args.repeat_case_ids) <= {c["id"] for c in cases}:
        raise SystemExit("Repeated cases must be among the selected cases")
    strategies = ["direct", "staged"] if args.strategy == "both" else [args.strategy]
    random.Random(args.order_seed).shuffle(cases)
    config = {
        "prompt_version": PROMPT_VERSION,
        "workflow_version": WORKFLOW_VERSION,
        "backend": args.backend,
        "model": args.model,
        "max_tokens": args.max_tokens,
        "temperature": args.temperature,
        "case_ids": [c["id"] for c in cases],
        "strategies": strategies,
        "repeats": args.repeats,
        "repeat_case_ids": args.repeat_case_ids or [c["id"] for c in cases],
        "order_seed": args.order_seed,
        "dataset_versions": sorted({c.get("dataset_version", "1") for c in cases}),
    }
    if args.backend == "http":
        config["base_url"] = args.base_url.rstrip("/")

    args.out.mkdir(parents=True, exist_ok=True)
    manifest_path, output = args.out / "run.json", args.out / "predictions.jsonl"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if not args.resume or manifest["configuration"] != config:
            raise SystemExit("Choose a new output directory, or resume with the same configuration")
        if read_jsonl(args.out / "cases.jsonl") != cases:
            raise SystemExit("The input cases changed; choose a new output directory")
    else:
        manifest = {
            "started": now(),
            "configuration": config,
            "description": "Live model outputs; cases reset between runs; no answer keys provided to inference",
        }
        write_jsonl(args.out / "cases.jsonl", cases)
        write_json(manifest_path, manifest)

    saved = read_checkpoint(output)
    validate_results(saved, config, complete=False)
    schedule = execution_schedule(config)
    remaining = schedule - {(r["case_id"], r["strategy"], r["repeat"]) for r in saved}
    # Method order alternates from case to case and is reversed for repeats.
    pending = [
        (case, strategy, repeat)
        for repeat in range(args.repeats)
        for i, case in enumerate(cases)
        for strategy in (strategies if (i + repeat) % 2 == 0 else strategies[::-1])
        if (case["id"], strategy, repeat) in remaining
    ]
    if pending:
        if args.backend == "mlx":
            backend = MLXBackend(args.model, args.max_tokens, args.temperature)
        else:
            backend = HTTPBackend(args.model, args.base_url, args.max_tokens, args.temperature)
        with output.open("a", encoding="utf-8") as stream:
            for number, (case, strategy, repeat) in enumerate(pending, len(saved) + 1):
                result = run_case(case, strategy, backend) | {"repeat": repeat}
                stream.write(json.dumps(result, ensure_ascii=False) + "\n")
                stream.flush()
                status = f" ERROR {result['error']}" if result["error"] else ""
                print(
                    f"[{number}/{len(schedule)}] {case['id']} {strategy}: "
                    f"{result['prediction']['decision']} ({result['latency_seconds']:.1f}s){status}",
                    flush=True,
                )
        settings = backend.settings
    else:
        print(f"All {len(schedule)} scheduled executions are already saved.")
        if "completed" in manifest:
            return
        settings = saved[-1]["model_settings"]
    manifest |= {"completed": now(), "model_settings": settings}
    write_json(manifest_path, manifest)


def score(args):
    """Score a run; the first scoring saves the answer keys it used, and later ones must match."""
    # This is the first time any labels enter the experiment workflow.
    destination = args.analysis_out or args.run
    answers_path = destination / "answers.jsonl"
    configuration = json.loads((args.run / "run.json").read_text())["configuration"]
    selected = set(configuration["case_ids"])
    labels_path = args.labels or (answers_path if answers_path.exists() else DEFAULT_LABELS)
    labels = [g for g in read_jsonl(labels_path) if g["case_id"] in selected]
    if answers_path.exists() and labels != read_jsonl(answers_path):
        raise SystemExit(
            "Answer keys differ from the saved scoring snapshot; use a separate --analysis-out"
        )
    results = read_jsonl(args.run / "predictions.jsonl")
    cases = read_jsonl(args.run / "cases.jsonl")
    summary, rows = evaluate(results, cases, labels, configuration)
    source_run = os.path.relpath(args.run.resolve(), destination.resolve())
    analysis_path = destination / "analysis.json"
    if args.analysis_out and analysis_path.exists():
        if json.loads(analysis_path.read_text())["source_run"] != source_run:
            raise SystemExit("This analysis directory belongs to another run")
    destination.mkdir(parents=True, exist_ok=True)
    if args.analysis_out:
        analysis = {
            "source_run": source_run,
            "fresh_inference": False,
            "scoring_version": SCORING_VERSION,
            "description": "Re-scoring the source run's saved live executions; no additional model executions or samples",
        }
        write_json(analysis_path, analysis)
    if not answers_path.exists():
        write_jsonl(answers_path, labels)
    write_scores(destination, summary, rows)
    print(json.dumps(summary["overall"], indent=2))


def saved_execution(args) -> dict:
    key = (args.case_id, args.strategy, args.repeat)
    for row in read_jsonl(args.run / "predictions.jsonl"):
        if (row["case_id"], row["strategy"], row["repeat"]) == key:
            return row
    raise SystemExit("No matching saved execution")


def replay_execution(case: dict, saved: dict) -> tuple[dict, dict]:
    """Run saved model responses through the current Python stages and compare outcomes."""
    backend = ReplayBackend(saved)
    replayed = run_case(case, saved["strategy"], backend)
    return replayed, {
        "all_saved_calls_used": backend.position == len(backend.calls),
        "same_prediction": replayed["prediction"] == saved["prediction"],
        "same_crm": replayed["stages"][-1]["output"] == saved["stages"][-1]["output"],
        "same_error": replayed["error"] == saved["error"],
    }


def inspect(args):
    print(json.dumps(saved_execution(args), indent=2, ensure_ascii=False))


def replay(args):
    saved = saved_execution(args)
    if saved["prompt_version"] != PROMPT_VERSION:
        raise SystemExit("This execution used another prompt version; use inspect to read it")
    case = next(c for c in read_jsonl(args.run / "cases.jsonl") if c["id"] == args.case_id)
    replayed, comparison = replay_execution(case, saved)
    write = replayed["stages"][-1]["output"]
    report = {
        "saved_workflow_version": saved.get("workflow_version", "1"),
        "current_workflow_version": WORKFLOW_VERSION,
        "prediction": replayed["prediction"],
        "write_applied": write["applied"],
        "write_error": write.get("error"),
        "error": replayed["error"],
        **comparison,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))


def replay_check(args):
    cases = {c["id"]: c for c in read_jsonl(args.run / "cases.jsonl")}
    saved = read_jsonl(args.run / "predictions.jsonl")
    if any(
        (r["prompt_version"], r.get("workflow_version")) != (PROMPT_VERSION, WORKFLOW_VERSION)
        for r in saved
    ):
        raise SystemExit(
            "This run was saved by other prompt or workflow versions; "
            "replay it with the commit that produced it"
        )
    mismatches = [
        {"case_id": row["case_id"], "strategy": row["strategy"], "repeat": row["repeat"]}
        for row in saved
        if not all(replay_execution(cases[row["case_id"]], row)[1].values())
    ]
    print(f"{len(saved) - len(mismatches)} of {len(saved)} saved executions replay the same.")
    for mismatch in mismatches:
        print("Different:", json.dumps(mismatch))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    command = commands.add_parser("validate", help="Check the cases and answer keys")
    command.add_argument("--cases", default=DEFAULT_CASES)
    command.add_argument("--labels", default=DEFAULT_LABELS)
    command.set_defaults(handler=validate)

    command = commands.add_parser("run", help="Run the workflows and save every execution")
    command.add_argument("--cases", default=DEFAULT_CASES)
    command.add_argument("--split", choices=["dev", "test", "all"], default="dev")
    command.add_argument("--case-ids", nargs="+")
    command.add_argument("--limit", type=positive)
    command.add_argument("--strategy", choices=["direct", "staged", "both"], default="both")
    command.add_argument("--backend", choices=["mlx", "http"], default="mlx")
    command.add_argument("--model", default=DEFAULT_MODEL)
    command.add_argument("--base-url", default="http://127.0.0.1:8080/v1")
    command.add_argument("--max-tokens", type=positive, default=512)
    command.add_argument("--temperature", type=float, default=0.0)
    command.add_argument("--repeats", type=positive, default=1)
    command.add_argument(
        "--repeat-case-ids", nargs="+", help="Repeat only these cases after the primary runs"
    )
    command.add_argument("--order-seed", type=int, default=17)
    command.add_argument("--out", type=Path, required=True)
    command.add_argument("--resume", action="store_true")
    command.set_defaults(handler=run)

    command = commands.add_parser("score", help="Score a saved run against the answer keys")
    command.add_argument("run", type=Path)
    command.add_argument("--labels", help="Defaults to the run's saved answers, if scored before")
    command.add_argument(
        "--analysis-out",
        type=Path,
        help="Write a revised analysis here, keeping the run's original answers and scores",
    )
    command.set_defaults(handler=score)

    for name, handler, help_text in (
        ("inspect", inspect, "Print one saved execution"),
        ("replay", replay, "Replay one saved execution through the current stages"),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("run", type=Path)
        command.add_argument("case_id")
        command.add_argument("--strategy", choices=["direct", "staged"], default="staged")
        command.add_argument("--repeat", type=int, default=0)
        command.set_defaults(handler=handler)

    command = commands.add_parser(
        "replay-check", help="Replay every saved execution and compare the outcomes"
    )
    command.add_argument("run", type=Path)
    command.set_defaults(handler=replay_check)

    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
