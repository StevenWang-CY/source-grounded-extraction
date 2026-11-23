# CRM workflow comparison

66 cases; split: test2.

## Primary executions

| Measure | guided |
| --- | ---: |
| Correct writes / accept decisions | 26/51 (51.0%) |
| Useful updates written | 26/38 (68.4%) |
| Exact candidate acceptance | 25/51 (49.0%) |
| Correct decisions | 47/66 (71.2%) |
| Entity resolution | 51/66 (77.3%) |
| Evidence flags right on correct candidates | n/a (0/0) |
| Field precision | 343/365 (94.0%) |
| Field recall | 343/376 (91.2%) |
| Review/reject cases withheld | 12/28 (42.9%) |
| Quotation found in the cited source | 60/60 (100.0%) |
| Accepted updates from allowed sources | 49/51 (96.1%) |
| Cases | 66 |
| Model calls (attempted) | 66 |
| Input tokens | 115656 |
| Output tokens | 8992 |
| Invalid responses | 1 |
| Mean time per case, seconds | 1.62 |

Writes are scored from the saved CRM state. Candidate scores cover extracted fields, quote matching checks the cited text, and verification scores check support/date/conflict flags on correct candidates.

## Public and synthetic cases

| Origin | Method | Cases | Correct writes / accept decisions | Useful updates written |
| --- | --- | ---: | ---: | ---: |
| fewrel_adapted | guided | 30 | 15/26 (57.7%) | 15/24 (62.5%) |
| synthetic | guided | 36 | 11/25 (44.0%) | 11/14 (78.6%) |

## Fresh repeats and overhead

- guided: repeat agreement 6/6 (100.0%); 0 repeated pair(s) with an invalid response, which count as disagreements. Billed API cost: 0.0 USD.

66 primary executions and 6 fresh repeats. Main measures use primary executions.

## Failure analysis

| Method | Failure type | Count |
| --- | --- | ---: |
| guided | decision | 19 |
| guided | entity_resolution | 15 |
| guided | extraction | 18 |
| guided | incorrect_acceptance | 25 |
| guided | permission | 2 |
| guided | response_error | 1 |
| guided | write_error | 2 |

Counts can overlap. See `errors.jsonl` for affected cases, `paired_cases.csv` for the comparison, and `crm-study inspect` for the original trace. Inputs, answers, responses, and model settings are saved with the run.
