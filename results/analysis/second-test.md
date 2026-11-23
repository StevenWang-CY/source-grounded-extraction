# Second test analysis

Written by `scripts/analyze.py` from the saved run in `results/second-test/` (workflow 4).

## Main measures, with 95% Wilson intervals

| Measure | Direct | Staged |
| --- | ---: | ---: |
| Correct writes / accept decisions | 23/53 (31%–57%) | 25/30 (66%–93%) |
| Useful updates written | 23/38 (45%–74%) | 25/38 (50%–79%) |
| Review/reject cases accepted | 19/28 (49%–82%) | 1/28 (1%–18%) |
| Correct decisions | 34/66 (40%–63%) | 54/66 (71%–89%) |
| Invalid responses | 13 | 5 |

## Paired by case, exact McNemar test

| Outcome | Direct only | Staged only | p |
| --- | ---: | ---: | ---: |
| Correct decision | 6 | 26 | 0.0005 |
| Accepted a review/reject case | 18 | 0 | 0.0000 |
| Wrote a useful update | 4 | 6 | 0.7539 |

## Fields

| Field | Direct precision | Direct recall | Staged precision | Staged recall |
| --- | ---: | ---: | ---: | ---: |
| Names | 58/63 | 58/64 | 52/55 | 52/64 |
| Roles | 33/40 | 33/40 | 30/37 | 30/40 |
| Relationships | 17/23 | 17/24 | 16/18 | 16/24 |
| Organizations | 30/45 | 30/30 | 24/29 | 24/30 |
| Effective dates | 26/29 | 26/26 | 25/25 | 25/26 |

## Steps and cost

| Measure | Direct | Staged |
| --- | ---: | ---: |
| Entity resolution | 44/66 | 54/66 |
| Quotation found in the cited source | 62/63 | 55/55 |
| Accepted updates from allowed sources | 48/53 | 30/30 |
| Evidence flags right on correct candidates | n/a | 39/41 |
| Model calls | 66 | 121 |
| Input tokens | 56982 | 59444 |
| Output tokens | 8888 | 10585 |
| Mean seconds per case | 1.04 | 1.23 |

What the direct responses chose: invalid accept (6), invalid reject (7), valid accept (53).

## What each stage contributes

Python steps means matching and the decision rules.

| Variant | Correct writes / accept decisions | Useful updates written | Review/reject cases accepted | Correct decisions | Invalid responses |
| --- | ---: | ---: | ---: | ---: | ---: |
| Direct | 23/53 | 23/38 | 19/28 | 34/66 | 13 |
| Direct's candidate, Python steps, no verifier | 27/43 | 27/38 | 7/28 | 56/66 | 0 |
| Staged extraction, Python steps, no verifier | 25/31 | 25/38 | 2/28 | 53/66 | 5 |
| Full staged workflow | 25/30 | 25/38 | 1/28 | 54/66 | 5 |
| Answer-key candidate, model verifier, Python steps | 37/38 | 37/38 | 1/28 | 64/66 | 0 |
| Answer-key candidate and flags, Python steps | 38/38 | 38/38 | 0/28 | 66/66 | 0 |

## Review/reject cases

| Kind of case | Cases | Direct accepted | Staged accepted | Stopped by the intended rule | Same, on answer-key candidates |
| --- | ---: | ---: | ---: | ---: | ---: |
| ambiguous identity | 2 | 2 | 0 | 2 | 2 |
| conflicting sources | 2 | 1 | 1 | 0 | 1 |
| disallowed source | 5 | 5 | 0 | 5 | 5 |
| duplicate records | 5 | 5 | 0 | 5 | 5 |
| explicit denial | 2 | 0 | 0 | 0 | 2 |
| future update | 2 | 2 | 0 | 1 | 2 |
| irrelevant document | 2 | 0 | 0 | 2 | 2 |
| same date conflict | 2 | 2 | 0 | 2 | 2 |
| stale update | 2 | 2 | 0 | 2 | 2 |
| tentative claim | 2 | 0 | 0 | 1 | 2 |
| undated conflict | 2 | 0 | 0 | 2 | 2 |

Other rules that stopped a case: missing_organization (3), no_candidate (2).

## Staged failures

Wrong writes are accept decisions that did not produce a correct write. Missed updates are useful updates that were not accepted.

| Group | Wrong writes | Missed updates | Example | Cases |
| --- | ---: | ---: | ---: | ---: |
| Value includes extra words | 2 | 0 | “South African group Steinhoff International” stored as the owner | `fewrel-p127-0172`, `fewrel-p39-0066` |
| Wrong subject | 2 | 1 | The doctor “Adamidi” extracted instead of Abbas II of Egypt | `fewrel-p39-0057`, `fewrel-p39-0064`, `fewrel-p39-0061` |
| Conflicting sources not detected | 1 | 0 | A newsletter and a staff directory give different roles | `scenario-06-5` |
| Entity type does not fit the attribute | 0 | 5 | “organization” returned as the entity type of the Arab League | `fewrel-p127-0173`, `fewrel-p127-0186`, `fewrel-p159-0457`, `fewrel-p159-0458`, `fewrel-p159-0522` |
| No candidate returned | 0 | 2 | No owner found in “taken over by Virgin Money” | `fewrel-p127-0175`, `fewrel-p39-0060` |
| Organization left out | 0 | 1 | “Fernhill Consulting” not returned as Ivo Duarte's organization | `scenario-16-6` |

## Consistency

Repeated executions matched their first response in 12 of 12.
