# Experiments

The question is whether the staged workflow produces more reliable CRM updates, and what it
costs in useful updates and time.

## Setup

| Item | Setting |
| --- | --- |
| Dataset | 132 cases, 66 development and 66 test |
| Model | Qwen3-4B, 4-bit, on MLX, with thinking turned off |
| Generation | Temperature 0 (greedy), up to 512 output tokens |
| Comparison | Both methods on every case, with the same inputs and initial CRM |
| Repeats | Six cases per split run a second time under both methods |
| Order | Cases shuffled with seed 17, method order alternating |

That makes 144 executions per split, 132 main ones and 12 repeats. `configs/experiment.json`
stores these settings and the repeated case IDs. The scores use the main executions only.

```bash
.venv/bin/python scripts/run_experiment.py --split dev --out results/my-run
```

Add `--resume` after an interruption. Each run keeps its inputs, settings, answers, and
responses together. A split takes under four minutes on an M5 Max.

## Saved runs

This repository has two runs of the development split, on two Macs, and a smaller check of the
verifier. The [results guide](../results/README.md) says what is in each folder. The 66 test
cases are kept for the final comparison, which the final report will cover.

## Rescoring parts of the workflow

To see where the gain comes from, `scripts/analyze_development.py` runs the Python steps again
on saved responses with parts of the workflow removed. Only the verifier check needs new model
calls, and `scripts/check_verifier.py` makes those.

| Variant | How it is built |
| --- | --- |
| Direct | The saved direct responses |
| Direct's candidate, Python steps, no verifier | The candidate from each direct response, then matching and decision rules, treating the evidence as supported |
| Staged extraction, Python steps, no verifier | The saved extraction responses, then the same steps |
| Full staged workflow | The saved staged responses |
| Answer-key candidate, model verifier, Python steps | The answer key's candidate, with a live verification call |
| Answer-key candidate and flags, Python steps | Both from the answer key |

The last two rows use the answer key on purpose, to separate extraction errors from the later
steps. They test parts of the workflow and are not workflows anyone would use. The results are
in the [analysis tables](../results/analysis/development.md).

To run saved responses through the Python steps again without the model:

```bash
.venv/bin/crm-study replay-check results/development
```
