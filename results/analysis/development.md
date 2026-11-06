# Development analysis

Written by `scripts/analyze_development.py` from the saved runs.

## Main measures, with 95% Wilson intervals

| Measure | Direct | Staged |
| --- | ---: | ---: |
| Correct writes / accept decisions | 29/57 (38%–63%) | 26/31 (67%–93%) |
| Useful updates written | 29/38 (61%–87%) | 26/38 (53%–81%) |
| Review/reject cases accepted | 21/28 (57%–87%) | 0/28 (0%–12%) |
| Correct decisions | 36/66 (43%–66%) | 55/66 (73%–90%) |
| Invalid responses | 9 | 4 |

## Paired by case, exact McNemar test

| Outcome | Direct only | Staged only | p |
| --- | ---: | ---: | ---: |
| Correct decision | 6 | 25 | 0.0009 |
| Accepted a review/reject case | 21 | 0 | 0.0000 |
| Wrote a useful update | 8 | 5 | 0.5811 |

## Fields

| Field | Direct precision | Direct recall | Staged precision | Staged recall |
| --- | ---: | ---: | ---: | ---: |
| Names | 62/64 | 62/64 | 55/56 | 55/64 |
| Roles | 37/41 | 37/40 | 36/36 | 36/40 |
| Relationships | 19/23 | 19/24 | 19/20 | 19/24 |
| Organizations | 30/42 | 30/30 | 22/24 | 22/30 |
| Effective dates | 26/26 | 26/26 | 26/29 | 26/26 |

## What each stage contributes

Python steps means matching and the decision rules.

| Variant | Correct writes / accept decisions | Useful updates written | Review/reject cases accepted | Correct decisions | Invalid responses |
| --- | ---: | ---: | ---: | ---: | ---: |
| Direct | 29/57 | 29/38 | 21/28 | 36/66 | 9 |
| Direct's candidate, Python steps, no verifier | 25/37 | 25/38 | 7/28 | 51/66 | 1 |
| Staged extraction, Python steps, no verifier | 26/33 | 26/38 | 2/28 | 53/66 | 4 |
| Full staged workflow | 26/31 | 26/38 | 0/28 | 55/66 | 4 |
| Answer-key candidate, model verifier, Python steps | 38/39 | 38/38 | 1/28 | 65/66 | 0 |
| Answer-key candidate and flags, Python steps | 38/38 | 38/38 | 0/28 | 66/66 | 0 |

The same steps on the second Mac:

| Variant | Correct writes / accept decisions | Useful updates written | Review/reject cases accepted | Correct decisions | Invalid responses |
| --- | ---: | ---: | ---: | ---: | ---: |
| Direct | 28/59 | 28/38 | 23/28 | 36/66 | 7 |
| Direct's candidate, Python steps, no verifier | 24/37 | 24/38 | 7/28 | 51/66 | 1 |
| Staged extraction, Python steps, no verifier | 25/32 | 25/38 | 2/28 | 52/66 | 4 |
| Full staged workflow | 25/30 | 25/38 | 0/28 | 54/66 | 4 |

## Review/reject cases

| Kind of case | Cases | Direct accepted | Staged accepted | Stopped by the intended rule | Same, on answer-key candidates |
| --- | ---: | ---: | ---: | ---: | ---: |
| ambiguous identity | 2 | 2 | 0 | 2 | 2 |
| conflicting sources | 2 | 2 | 0 | 1 | 2 |
| disallowed source | 5 | 4 | 0 | 5 | 5 |
| duplicate records | 5 | 5 | 0 | 2 | 5 |
| explicit denial | 2 | 0 | 0 | 0 | 2 |
| future update | 2 | 2 | 0 | 2 | 2 |
| irrelevant document | 2 | 1 | 0 | 2 | 2 |
| same date conflict | 2 | 2 | 0 | 1 | 2 |
| stale update | 2 | 2 | 0 | 2 | 2 |
| tentative claim | 2 | 1 | 0 | 1 | 1 |
| undated conflict | 2 | 0 | 0 | 1 | 2 |

Other rules that stopped a case: missing_organization (7), no_candidate (1), pipeline_error (1).

## Staged failures on useful cases

| Group | Wrong writes | Missed updates | Example | Cases |
| --- | ---: | ---: | ---: | ---: |
| Effective date not stated in the source | 3 | 0 | “August 2015” stored as 2015-08-01 | `fewrel-p127-0072`, `scenario-14-1`, `scenario-14-2` |
| Duplicate identity | 1 | 0 | “UAL Corporation” added beside the UAL record | `fewrel-p159-0303` |
| Wrong attribute | 1 | 0 | “working” stored as a role for an employer update | `scenario-17-1` |
| Entity type does not fit the attribute | 0 | 3 | “organization” returned as the entity type of a company | `fewrel-p127-0102`, `fewrel-p159-0287`, `fewrel-p159-0317` |
| No candidate returned | 0 | 3 | No role found in “Attorney General Jeff Sessions” | `fewrel-p39-0030`, `fewrel-p39-0032`, `fewrel-p39-0039` |
| Organization left out | 0 | 1 | “BL” not returned as Pavel Reeve's organization | `scenario-02-2` |

## Consistency

Repeated executions matched their first response in 12 of 12 on the first Mac and 12 of 12 on the second. Across the two Macs, 98 of 144 executions gave identical responses, and 136 gave the same candidate, match, and decision.
