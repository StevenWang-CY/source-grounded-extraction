# CRM workflow comparison

66 cases; split: development.

## Primary executions

| Measure | guided |
| --- | ---: |
| Correct writes / accept decisions | 24/46 (52.2%) |
| Useful updates written | 24/38 (63.2%) |
| Exact candidate acceptance | 23/46 (50.0%) |
| Correct decisions | 45/66 (68.2%) |
| Entity resolution | 49/66 (74.2%) |
| Evidence flags right on correct candidates | n/a (0/0) |
| Field precision | 330/344 (95.9%) |
| Field recall | 330/376 (87.8%) |
| Review/reject cases withheld | 13/28 (46.4%) |
| Quotation found in the cited source | 55/57 (96.5%) |
| Accepted updates from allowed sources | 45/46 (97.8%) |
| Cases | 66 |
| Model calls (attempted) | 66 |
| Input tokens | 115136 |
| Output tokens | 8503 |
| Invalid responses | 2 |
| Mean time per case, seconds | 1.34 |

Writes are scored from the saved CRM state. Candidate scores cover extracted fields, quote matching checks the cited text, and verification scores check support/date/conflict flags on correct candidates.

## Public and synthetic cases

| Origin | Method | Cases | Correct writes / accept decisions | Useful updates written |
| --- | --- | ---: | ---: | ---: |
| fewrel_adapted | guided | 30 | 13/22 (59.1%) | 13/24 (54.2%) |
| synthetic | guided | 36 | 11/24 (45.8%) | 11/14 (78.6%) |

## Fresh repeats and overhead

- guided: repeat agreement 6/6 (100.0%); 0 repeated pair(s) with an invalid response, which count as disagreements. Billed API cost: 0.0 USD.

66 primary executions and 6 fresh repeats. Main measures use primary executions.

## Failure analysis

| Method | Failure type | Count |
| --- | --- | ---: |
| guided | decision | 21 |
| guided | entity_resolution | 17 |
| guided | extraction | 17 |
| guided | incorrect_acceptance | 22 |
| guided | permission | 1 |
| guided | quote | 2 |
| guided | response_error | 2 |
| guided | write_error | 2 |

Counts can overlap. See `errors.jsonl` for affected cases, `paired_cases.csv` for the comparison, and `crm-study inspect` for the original trace. Inputs, answers, responses, and model settings are saved with the run.
