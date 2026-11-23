# CRM workflow comparison

66 cases; split: test2.

## Primary executions

| Measure | direct | staged |
| --- | ---: | ---: |
| Correct writes / accept decisions | 18/31 (58.1%) | 31/36 (86.1%) |
| Useful updates written | 18/38 (47.4%) | 31/38 (81.6%) |
| Exact candidate acceptance | 18/31 (58.1%) | 31/36 (86.1%) |
| Correct decisions | 28/66 (42.4%) | 61/66 (92.4%) |
| Entity resolution | 23/66 (34.8%) | 60/66 (90.9%) |
| Evidence flags right on correct candidates | n/a (0/0) | 50/53 (94.3%) |
| Field precision | 364/372 (97.8%) | 352/360 (97.8%) |
| Field recall | 364/376 (96.8%) | 352/376 (93.6%) |
| Review/reject cases withheld | 3/28 (10.7%) | 25/28 (89.3%) |
| Quotation found in the cited source | 63/63 (100.0%) | 61/61 (100.0%) |
| Accepted updates from allowed sources | 30/31 (96.8%) | 36/36 (100.0%) |
| Cases | 66 | 66 |
| Model calls (attempted) | 66 | 127 |
| Input tokens | 56982 | 62270 |
| Output tokens | 10409 | 11560 |
| Invalid responses | 31 | 5 |
| Mean time per case, seconds | 3.70 | 4.12 |

Writes are scored from the saved CRM state. Candidate scores cover extracted fields, quote matching checks the cited text, and verification scores check support/date/conflict flags on correct candidates.

## Public and synthetic cases

| Origin | Method | Cases | Correct writes / accept decisions | Useful updates written |
| --- | --- | ---: | ---: | ---: |
| fewrel_adapted | direct | 30 | 7/18 (38.9%) | 7/24 (29.2%) |
| synthetic | direct | 36 | 11/13 (84.6%) | 11/14 (78.6%) |
| fewrel_adapted | staged | 30 | 17/22 (77.3%) | 17/24 (70.8%) |
| synthetic | staged | 36 | 14/14 (100.0%) | 14/14 (100.0%) |

## Paired outcomes

| Outcome | Cases | Both | Direct only | Staged only | Neither |
| --- | ---: | ---: | ---: | ---: | ---: |
| Wrote a useful update | 38 | 17 | 1 | 14 | 6 |
| Correct decision | 66 | 26 | 2 | 35 | 3 |
| Accepted a review/reject case | 28 | 0 | 6 | 0 | 22 |

## Fresh repeats and overhead

- direct: repeat agreement 3/6 (50.0%); 3 repeated pair(s) with an invalid response, which count as disagreements. Billed API cost: 0.0 USD.
- staged: repeat agreement 6/6 (100.0%); 0 repeated pair(s) with an invalid response, which count as disagreements. Billed API cost: 0.0 USD.

132 primary executions and 12 fresh repeats. Main measures use primary executions.

## Failure analysis

| Method | Failure type | Count |
| --- | --- | ---: |
| direct | decision | 38 |
| direct | entity_resolution | 43 |
| direct | extraction | 8 |
| direct | incorrect_acceptance | 13 |
| direct | permission | 1 |
| direct | response_error | 31 |
| staged | decision | 5 |
| staged | entity_resolution | 6 |
| staged | extraction | 13 |
| staged | incorrect_acceptance | 5 |
| staged | response_error | 5 |
| staged | verification | 3 |

Counts can overlap. See `errors.jsonl` for affected cases, `paired_cases.csv` for the comparison, and `crm-study inspect` for the original trace. Inputs, answers, responses, and model settings are saved with the run.
