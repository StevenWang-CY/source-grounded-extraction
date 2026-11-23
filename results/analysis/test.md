# Test analysis

Written by `scripts/analyze.py` from the saved run in `results/test/` (workflow 3).

## Main measures, with 95% Wilson intervals

| Measure | Direct | Staged |
| --- | ---: | ---: |
| Correct writes / accept decisions | 27/59 (34%–58%) | 24/33 (56%–85%) |
| Useful updates written | 27/38 (55%–83%) | 24/38 (47%–77%) |
| Review/reject cases accepted | 21/28 (57%–87%) | 2/28 (2%–23%) |
| Correct decisions | 38/66 (46%–69%) | 55/66 (73%–90%) |
| Invalid responses | 7 | 3 |

## Paired by case, exact McNemar test

| Outcome | Direct only | Staged only | p |
| --- | ---: | ---: | ---: |
| Correct decision | 7 | 24 | 0.0033 |
| Accepted a review/reject case | 19 | 0 | 0.0000 |
| Wrote a useful update | 8 | 5 | 0.5811 |

## Fields

| Field | Direct precision | Direct recall | Staged precision | Staged recall |
| --- | ---: | ---: | ---: | ---: |
| Names | 62/66 | 62/64 | 57/60 | 57/64 |
| Roles | 36/42 | 36/40 | 36/39 | 36/40 |
| Relationships | 17/24 | 17/24 | 17/21 | 17/24 |
| Organizations | 30/44 | 30/30 | 27/33 | 27/30 |
| Effective dates | 24/24 | 24/26 | 26/28 | 26/26 |

## Steps and cost

| Measure | Direct | Staged |
| --- | ---: | ---: |
| Entity resolution | 48/66 | 54/66 |
| Quotation found in the cited source | 65/66 | 59/60 |
| Accepted updates from allowed sources | 54/59 | 33/33 |
| Evidence flags right on correct candidates | n/a | 40/44 |
| Model calls | 66 | 126 |
| Input tokens | 56869 | 61615 |
| Output tokens | 8778 | 11326 |
| Mean seconds per case | 1.23 | 1.56 |

What the direct responses chose: invalid accept (5), invalid reject (2), valid accept (59).

## What each stage contributes

Python steps means matching and the decision rules.

| Variant | Correct writes / accept decisions | Useful updates written | Review/reject cases accepted | Correct decisions | Invalid responses |
| --- | ---: | ---: | ---: | ---: | ---: |
| Direct | 27/59 | 27/38 | 21/28 | 38/66 | 7 |
| Direct's candidate, Python steps, no verifier | 25/41 | 25/38 | 9/28 | 51/66 | 0 |
| Staged extraction, Python steps, no verifier | 24/34 | 24/38 | 3/28 | 55/66 | 3 |
| Full staged workflow | 24/33 | 24/38 | 2/28 | 55/66 | 3 |
| Answer-key candidate, model verifier, Python steps | 38/40 | 38/38 | 2/28 | 63/66 | 0 |
| Answer-key candidate and flags, Python steps | 38/38 | 38/38 | 0/28 | 66/66 | 0 |

## Review/reject cases

| Kind of case | Cases | Direct accepted | Staged accepted | Stopped by the intended rule | Same, on answer-key candidates |
| --- | ---: | ---: | ---: | ---: | ---: |
| ambiguous identity | 2 | 2 | 0 | 2 | 2 |
| conflicting sources | 2 | 2 | 2 | 0 | 0 |
| disallowed source | 5 | 5 | 0 | 5 | 5 |
| duplicate records | 5 | 5 | 0 | 5 | 5 |
| explicit denial | 2 | 0 | 0 | 0 | 2 |
| future update | 2 | 1 | 0 | 1 | 1 |
| irrelevant document | 2 | 2 | 0 | 1 | 2 |
| same date conflict | 2 | 2 | 0 | 2 | 2 |
| stale update | 2 | 2 | 0 | 2 | 2 |
| tentative claim | 2 | 0 | 0 | 1 | 2 |
| undated conflict | 2 | 0 | 0 | 2 | 2 |

Other rules that stopped a case: missing_organization (2), no_candidate (2), claim_contradicted (1).

## Staged failures

Wrong writes are accept decisions that did not produce a correct write. Missed updates are useful updates that were not accepted.

| Group | Wrong writes | Missed updates | Example | Cases |
| --- | ---: | ---: | ---: | ---: |
| Value includes extra words | 4 | 0 | “Tata Motors of India” stored as the owner | `fewrel-p127-0035`, `fewrel-p127-0060`, `fewrel-p127-0085`, `fewrel-p159-0174` |
| Effective date not stated in the source | 2 | 3 | “in 1972” stored as 1972-01-01 | `fewrel-p39-0025`, `scenario-14-4`, `fewrel-p127-0037`, `fewrel-p127-0103`, `fewrel-p127-0114` |
| Identity matching | 1 | 3 | “Yingke Law Firm” added beside the Yingke record | `fewrel-p159-0041`, `fewrel-p39-0022`, `fewrel-p39-0035`, `fewrel-p39-0040` |
| Conflicting sources not detected | 2 | 0 | Two allowed sources give different roles from the same date | `scenario-06-3`, `scenario-06-4` |
| Quotation altered | 0 | 1 | “Hafez al - Assad” respelled inside the quotation | `fewrel-p39-0024` |

## Consistency

Repeated executions matched their first response in 12 of 12.
