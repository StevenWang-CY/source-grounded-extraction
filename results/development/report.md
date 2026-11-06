# CRM workflow comparison

66 cases; split: development.

## Primary executions

| Measure | direct | staged |
| --- | ---: | ---: |
| Correct writes / accept decisions | 27/57 (47.4%) | 23/31 (74.2%) |
| Useful updates written | 27/38 (71.1%) | 23/38 (60.5%) |
| Exact candidate acceptance | 19/57 (33.3%) | 23/31 (74.2%) |
| Correct decisions | 36/66 (54.5%) | 55/66 (83.3%) |
| Entity resolution | 48/66 (72.7%) | 57/66 (86.4%) |
| Evidence flags right on correct candidates | n/a (0/0) | 37/39 (94.9%) |
| Field precision | 358/388 (92.3%) | 322/333 (96.7%) |
| Field recall | 358/376 (95.2%) | 322/376 (85.6%) |
| Review/reject cases withheld | 0/28 (0.0%) | 27/28 (96.4%) |
| Quotation found in the cited source | 63/64 (98.4%) | 56/56 (100.0%) |
| Accepted updates from allowed sources | 53/57 (93.0%) | 31/31 (100.0%) |
| Cases | 66 | 66 |
| Model calls (attempted) | 66 | 122 |
| Input tokens | 56462 | 58936 |
| Output tokens | 8393 | 10255 |
| Invalid responses | 9 | 4 |
| Mean time per case, seconds | 6.17 | 7.14 |

Writes are scored from the saved CRM state. Candidate scores cover extracted fields, quote matching checks the cited text, and verification scores check support/date/conflict flags on correct candidates.

## Public and synthetic cases

| Origin | Method | Cases | Correct writes / accept decisions | Useful updates written |
| --- | --- | ---: | ---: | ---: |
| fewrel_adapted | direct | 30 | 18/28 (64.3%) | 18/24 (75.0%) |
| synthetic | direct | 36 | 9/29 (31.0%) | 9/14 (64.3%) |
| fewrel_adapted | staged | 30 | 13/18 (72.2%) | 13/24 (54.2%) |
| synthetic | staged | 36 | 10/13 (76.9%) | 10/14 (71.4%) |

## Paired outcomes

| Outcome | Cases | Both | Direct only | Staged only | Neither |
| --- | ---: | ---: | ---: | ---: | ---: |
| Wrote a useful update | 38 | 19 | 8 | 4 | 7 |
| Correct decision | 66 | 30 | 6 | 25 | 5 |
| Accepted a review/reject case | 28 | 0 | 21 | 0 | 7 |

## Fresh repeats and overhead

- direct: repeat agreement 5/6 (83.3%); 1 repeated pair(s) with an invalid response, which count as disagreements. Billed API cost: 0.0 USD.
- staged: repeat agreement 5/6 (83.3%); 1 repeated pair(s) with an invalid response, which count as disagreements. Billed API cost: 0.0 USD.

132 primary executions and 12 fresh repeats. Main measures use primary executions.

## Failure analysis

| Method | Failure type | Count |
| --- | --- | ---: |
| direct | decision | 30 |
| direct | entity_resolution | 18 |
| direct | extraction | 20 |
| direct | incorrect_acceptance | 30 |
| direct | permission | 4 |
| direct | quote | 1 |
| direct | response_error | 9 |
| direct | write_error | 2 |
| staged | decision | 11 |
| staged | entity_resolution | 9 |
| staged | extraction | 25 |
| staged | incorrect_acceptance | 8 |
| staged | response_error | 4 |
| staged | verification | 2 |

Counts can overlap. See `errors.jsonl` for affected cases, `paired_cases.csv` for the comparison, and `crm-study inspect` for the original trace. Inputs, answers, responses, and model settings are saved with the run.
