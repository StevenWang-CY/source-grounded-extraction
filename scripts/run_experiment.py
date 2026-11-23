"""Run and score one complete split, using the experiment plan and any overrides.

Answer keys are read only by the scoring step, after inference.
"""

import argparse
import json
import platform
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from crm_study.data import SPLITS
from crm_study.pipeline import STRATEGIES, WORKFLOW_VERSIONS
from crm_study.schema import read_jsonl

OVERRIDES = ("model", "workflow_version", "strategy", "max_tokens", "thinking")


def commands(plan, split, output, resume=False):
    cases = [c for c in read_jsonl(plan["cases"]) if c["split"] == split]
    spec = plan["splits"][split]
    if len(cases) != spec["expected_cases"]:
        raise ValueError("The dataset differs from the planned split")
    if not set(spec["repeat_case_ids"]) <= {c["id"] for c in cases}:
        raise ValueError("A repeated case is not in this split")
    cli = [sys.executable, "-m", "crm_study.cli"]
    run = cli + ["run", "--cases", plan["cases"], "--split", split]
    run += ["--strategy", plan["strategy"], "--workflow", plan["workflow_version"]]
    for field in ("backend", "model", "max_tokens", "temperature", "order_seed", "repeats"):
        run += ["--" + field.replace("_", "-"), str(plan[field])]
    if plan.get("base_url"):
        run += ["--base-url", plan["base_url"]]
    if plan.get("thinking"):
        run.append("--thinking")
    run += ["--repeat-case-ids", *spec["repeat_case_ids"], "--out", str(output)]
    if resume:
        run.append("--resume")
    score = cli + ["score", str(output), "--labels", plan["labels"]]
    return run, score


def environment() -> dict:
    packages = {}
    for package in ("mlx", "mlx-lm", "transformers", "tokenizers", "huggingface-hub"):
        try:
            packages[package] = version(package)
        except PackageNotFoundError:
            pass
    return {
        "python": platform.python_version(),
        "system": platform.system(),
        "architecture": platform.machine(),
        "packages": packages,
        "note": "Runtime used for this comparison; model loading is excluded from per-case latency.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=Path("configs/experiment.json"))
    parser.add_argument("--split", choices=SPLITS, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    changes = parser.add_argument_group("changes to the plan")
    changes.add_argument("--model")
    changes.add_argument("--workflow", dest="workflow_version", choices=WORKFLOW_VERSIONS)
    changes.add_argument("--strategy", choices=[*STRATEGIES, "both"])
    changes.add_argument("--max-tokens", type=int)
    changes.add_argument("--thinking", action="store_true", default=None)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    plan |= {k: getattr(args, k) for k in OVERRIDES if getattr(args, k) is not None}
    try:
        run, score = commands(plan, args.split, args.out, args.resume)
    except ValueError as error:
        parser.error(str(error))
    args.out.mkdir(parents=True, exist_ok=True)
    for name, data in (("experiment_plan.json", plan), ("environment.json", environment())):
        if not (args.out / name).exists():
            (args.out / name).write_text(json.dumps(data, indent=2) + "\n")
    subprocess.run(run, check=True)
    subprocess.run(score, check=True)


if __name__ == "__main__":
    main()
