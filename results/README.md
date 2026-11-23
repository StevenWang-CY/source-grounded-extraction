# Saved results

| Folder | What it is |
| --- | --- |
| `development/` | The development comparison, run on October 17. The `reviewed/` folder inside has the scores used in the reports |
| `development-rerun/` | The same schedule on an M5 Max, to see how far results move between the two Macs |
| `test/` | The held-out test comparison, run on November 2 with the workflow as tested (workflow 3) |
| `fixes-development/`, `fixes-test/` | Both sets again with the four fixes (workflow 4) |
| `second-test/` | The second test set with workflow 4 |
| `second-test-before-fixes/` | The staged workflow on the second test set with workflow 3 |
| `models/` | Both workflows on the second test set with Qwen3-1.7B, 8B, and 14B |
| `variants/` | The stronger one-call workflows. Direct with thinking ran on development and the second test set. Guided direct ran on all three sets, and on the second test set with each model size |
| `verifier-check/`, `verifier-check-test/`, `verifier-check-second-test/` | The verifier alone on the answer key's candidates, for each set |
| `analysis/` | Tables built from the runs above by `scripts/analyze.py` |

A good place to start is [`analysis/test.md`](analysis/test.md), then
[`analysis/comparisons.md`](analysis/comparisons.md). The analysis folder has one page per set
of cases and one page for the comparisons across runs.

Each run folder has the files below. A run of only one workflow has no `paired_cases.csv`.
The verifier checks reuse the inputs and answers of the run they belong to, so they keep only
`predictions.jsonl`, `run.json`, and the score files.

| File | Contents |
| --- | --- |
| `cases.jsonl` | The inputs for the run |
| `predictions.jsonl` | Every execution, with the model's responses and each step's output |
| `answers.jsonl` | The answer key used for scoring |
| `run.json`, `environment.json`, `experiment_plan.json` | Dates, settings, and package versions |
| `summary.json`, `scores.csv`, `paired_cases.csv`, `errors.jsonl` | The scores, overall and case by case |
| `report.md` | A readable summary of the scores |
