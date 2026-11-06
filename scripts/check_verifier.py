"""Run the evidence check on the answer key's candidates, so extraction errors cannot hide it.

This tests one stage and is not a workflow. The answer key supplies each candidate, only the
verification call goes to the model, and the Python stages make the decision as usual.
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

from run_experiment import environment

from crm_study.backends import Call, MLXBackend
from crm_study.cli import DEFAULT_MODEL
from crm_study.evaluation import evaluate, write_scores
from crm_study.pipeline import run_case
from crm_study.schema import read_jsonl, write_jsonl


class AnswerKeyExtraction:
    """Answer the extraction call from the answer key and send the rest to the model."""

    def __init__(self, backend, candidate):
        self.backend = backend
        self.extraction = json.dumps({"candidate": candidate})
        self.settings = backend.settings

    def complete(self, messages):
        if self.extraction is None:
            return self.backend.complete(messages)
        text, self.extraction = self.extraction, None
        return Call(text, 0, 0, 0.0, "answer_key")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--development-run", type=Path, default=Path("results/development"))
    parser.add_argument("--out", type=Path, default=Path("results/verifier-check"))
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()
    cases = read_jsonl(args.development_run / "cases.jsonl")
    answers = read_jsonl(args.development_run / "reviewed/answers.jsonl")
    by_id = {answer["case_id"]: answer for answer in answers}
    backend = MLXBackend(args.model)
    started = datetime.now().astimezone().isoformat()
    results = []
    for number, case in enumerate(cases, 1):
        candidates = by_id[case["id"]]["candidates"]
        extraction = AnswerKeyExtraction(backend, candidates[0] if candidates else None)
        result = run_case(case, "staged", extraction) | {"repeat": 0}
        result["calls"] = [c for c in result["calls"] if c["stage"] == "verification"]
        results.append(result)
        print(f"[{number}/{len(cases)}] {case['id']}: {result['prediction']['decision']}")
    args.out.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out / "predictions.jsonl", results)
    run = {
        "started": started,
        "completed": datetime.now().astimezone().isoformat(),
        "description": "Answer-key candidates with live verification calls; a check of one stage",
        "model_settings": backend.settings,
        "environment": environment(),
    }
    (args.out / "run.json").write_text(json.dumps(run, indent=2) + "\n")
    write_scores(args.out, *evaluate(results, cases, answers))


if __name__ == "__main__":
    main()
