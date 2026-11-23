# Experiments

The main question is whether the staged workflow produces more reliable CRM updates than the
direct workflow, and what it costs in useful updates and time. The later runs ask whether the
fixes hold on new cases, and whether the answer depends on the model or on the direct prompt.

## Setup

| Item | Setting |
| --- | --- |
| Dataset | 198 cases in three sets of 66: development, test, and second test |
| Model | Qwen3-4B, 4-bit, on MLX, with thinking turned off |
| Generation | Temperature 0 (greedy), up to 512 output tokens |
| Comparison | Both workflows on every case, with the same inputs and initial CRM |
| Repeats | Six cases per set run a second time under each workflow |
| Order | Cases shuffled with seed 17, workflow order alternating |

A run of both workflows on one set has 144 executions, 132 main ones and 12 repeats.
`configs/experiment.json` stores these settings and the repeated case IDs. The scores use the
main executions only, and the repeats only check consistency.

```bash
.venv/bin/python scripts/run_experiment.py --split test2 --out results/my-run
```

Add `--resume` after an interruption. Each run keeps its inputs, settings, answers, and
responses together. A set takes about three minutes with Qwen3-4B on an M5 Max.

## Runs

Every run below is saved in `results/`, and the [results guide](../results/README.md) says what
is in each folder. All of them ran on the same M5 Max except the first development run.

| Run | Set | What changes | Command options |
| --- | --- | --- | --- |
| `development`, `development-rerun` | Development | The workflow as tested (workflow 3), on two Macs | `--split dev --workflow 3` |
| `test` | Test | The held-out comparison, workflow 3 | `--split test --workflow 3` |
| `fixes-development`, `fixes-test` | Development, test | The four fixes (workflow 4) | `--split dev`, `--split test` |
| `second-test` | Second test | Workflow 4 on new cases | `--split test2` |
| `second-test-before-fixes` | Second test | Staged with workflow 3, to see what the fixes change | `--split test2 --workflow 3 --strategy staged` |
| `models/qwen3-1.7b`, `-8b`, `-14b` | Second test | Smaller and larger models | `--split test2 --model mlx-community/Qwen3-8B-4bit` |
| `variants/thinking-*` | Development, second test | Direct with the model's reasoning turned on | `--strategy direct --thinking --max-tokens 4096` |
| `variants/guided-*` | Development, second test | Guided direct, with checks and worked examples in the prompt | `--strategy guided` |
| `verifier-check*` | All three | The verifier alone, on the answer key's candidates | `scripts/check_verifier.py --run results/test --out ...` |

The test set was run once, on November 2, with the answer key as it stood before the run. The
fixes came from reading its errors, so `fixes-test` is not a held-out result. The second test
set was built afterwards for that reason, and neither its cases nor the workflow were changed
after its runs.

Before this dataset I ran a pilot in October with 44 smaller cases, 22 for development and 22
for test, and ran the workflows on both halves. What I learned from it went into the current
dataset and prompts. None of its source texts are in the current sets, and its runs are not
part of these results.

## Rescoring parts of the workflow

To see where the gain comes from, `scripts/analyze.py` runs the Python steps again on saved
responses with parts of the workflow removed. Only the verifier check needs new model calls.

| Variant | How it is built |
| --- | --- |
| Direct | The saved direct responses |
| Direct's candidate, Python steps, no verifier | The candidate from each direct response, then matching and decision rules, treating the evidence as supported |
| Staged extraction, Python steps, no verifier | The saved extraction responses, then the same steps |
| Full staged workflow | The saved staged responses |
| Answer-key candidate, model verifier, Python steps | The answer key's candidate, with a live verification call |
| Answer-key candidate and flags, Python steps | Both from the answer key |

The last two rows use the answer key on purpose, to separate extraction errors from the later
steps. They test parts of the workflow and are not workflows anyone would use.

## Stronger one-call workflows

With Qwen3-4B, direct never chose review or reject in a valid response, so I tried two ways
of helping it.

- **Direct with thinking** uses the same prompt and turns on the model's reasoning mode. The
  token limit goes up to 4,096 so the reasoning fits.
- **Guided direct** adds the checks that staged runs in Python to the prompt, asks the model to
  record each check before deciding, and gives three worked examples with made-up entities.

I tuned the guided prompt on the development set only, and changed it once. Its first version
had three examples that all stated a date and an organization, and the model started to invent
dates and organizations for passages that state neither. The current version has one example
with no date and no organization.

## Model sizes

The model-size runs use Qwen3-1.7B, 8B, and 14B in 4-bit form, with the same prompts and
settings as Qwen3-4B. I also tried one model each from three other families on six development
cases, which is 12 executions per model. Llama 3.2 3B returned 7 invalid responses, Phi-4-mini
returned 11, and Gemma 3 4B returned 8. The prompts were written for Qwen3, so I left these
models out instead of comparing workflows on mostly invalid output. That trial is not saved
in `results/`.

## Replaying saved runs

Every saved run can go through the Python steps again without the model:

```bash
.venv/bin/crm-study replay-check results/test
```

The results are in the [analysis tables](../results/analysis/) and the
[final report](../reports/EAS_0099_Final_Report.pdf).
