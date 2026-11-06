# Saved results

| Folder | What it is |
| --- | --- |
| `development/` | The development comparison, run on October 17. The `reviewed/` folder inside has the scores used in the reports |
| `development-rerun/` | The same schedule on an M5 Max, to see how far results move between the two Macs |
| `verifier-check/` | The verifier alone on the answer key's candidates, 64 model calls |
| `analysis/` | Intervals, paired tests, workflow variants, and failure groups built from the runs above |

A good place to start is [`analysis/development.md`](analysis/development.md), then
[`development/reviewed/report.md`](development/reviewed/report.md).

`development/` and `development-rerun/` have these files. `verifier-check/` has the same kinds
of files, except that it reuses the development inputs and answers.

| File | Contents |
| --- | --- |
| `cases.jsonl` | The inputs for the run |
| `predictions.jsonl` | Every execution, with the model's responses and each step's output |
| `answers.jsonl` | The answer key used for scoring |
| `run.json`, `environment.json`, `experiment_plan.json` | Dates, settings, and package versions |
| `summary.json`, `scores.csv`, `paired_cases.csv`, `errors.jsonl` | The scores, overall and case by case |
| `report.md` | A readable summary of the scores |
