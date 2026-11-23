# CRM workflow comparison

66 cases; split: test.

## Primary executions

| Measure | guided |
| --- | ---: |
| Correct writes / accept decisions | 24/51 (47.1%) |
| Useful updates written | 24/38 (63.2%) |
| Exact candidate acceptance | 21/51 (41.2%) |
| Correct decisions | 45/66 (68.2%) |
| Entity resolution | 51/66 (77.3%) |
| Evidence flags right on correct candidates | n/a (0/0) |
| Field precision | 337/365 (92.3%) |
| Field recall | 337/376 (89.6%) |
| Review/reject cases withheld | 10/28 (35.7%) |
| Quotation found in the cited source | 60/60 (100.0%) |
| Accepted updates from allowed sources | 50/51 (98.0%) |
| Cases | 66 |
| Model calls (attempted) | 66 |
| Input tokens | 115543 |
| Output tokens | 9049 |
| Invalid responses | 5 |
| Mean time per case, seconds | 1.30 |

Writes are scored from the saved CRM state. Candidate scores cover extracted fields, quote matching checks the cited text, and verification scores check support/date/conflict flags on correct candidates.

## Public and synthetic cases

| Origin | Method | Cases | Correct writes / accept decisions | Useful updates written |
| --- | --- | ---: | ---: | ---: |
| fewrel_adapted | guided | 30 | 13/24 (54.2%) | 13/24 (54.2%) |
| synthetic | guided | 36 | 11/27 (40.7%) | 11/14 (78.6%) |

## Fresh repeats and overhead

- guided: repeat agreement 6/6 (100.0%); 0 repeated pair(s) with an invalid response, which count as disagreements. Billed API cost: 0.0 USD.

66 primary executions and 6 fresh repeats. Main measures use primary executions.

## Failure analysis

| Method | Failure type | Count |
| --- | --- | ---: |
| guided | decision | 21 |
| guided | entity_resolution | 15 |
| guided | extraction | 22 |
| guided | incorrect_acceptance | 27 |
| guided | permission | 1 |
| guided | response_error | 5 |
| guided | write_error | 2 |

Counts can overlap. See `errors.jsonl` for affected cases, `paired_cases.csv` for the comparison, and `crm-study inspect` for the original trace. Inputs, answers, responses, and model settings are saved with the run.
