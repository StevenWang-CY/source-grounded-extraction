# CRM workflow comparison

66 cases; split: test2.

## Primary executions

| Measure | guided |
| --- | ---: |
| Correct writes / accept decisions | 14/61 (23.0%) |
| Useful updates written | 14/38 (36.8%) |
| Exact candidate acceptance | 14/61 (23.0%) |
| Correct decisions | 37/66 (56.1%) |
| Entity resolution | 48/66 (72.7%) |
| Evidence flags right on correct candidates | n/a (0/0) |
| Field precision | 344/389 (88.4%) |
| Field recall | 344/376 (91.5%) |
| Review/reject cases withheld | 2/28 (7.1%) |
| Quotation found in the cited source | 63/63 (100.0%) |
| Accepted updates from allowed sources | 58/61 (95.1%) |
| Cases | 66 |
| Model calls (attempted) | 66 |
| Input tokens | 115656 |
| Output tokens | 14380 |
| Invalid responses | 3 |
| Mean time per case, seconds | 0.91 |

Writes are scored from the saved CRM state. Candidate scores cover extracted fields, quote matching checks the cited text, and verification scores check support/date/conflict flags on correct candidates.

## Public and synthetic cases

| Origin | Method | Cases | Correct writes / accept decisions | Useful updates written |
| --- | --- | ---: | ---: | ---: |
| fewrel_adapted | guided | 30 | 7/27 (25.9%) | 7/24 (29.2%) |
| synthetic | guided | 36 | 7/34 (20.6%) | 7/14 (50.0%) |

## Fresh repeats and overhead

- guided: repeat agreement 6/6 (100.0%); 0 repeated pair(s) with an invalid response, which count as disagreements. Billed API cost: 0.0 USD.

66 primary executions and 6 fresh repeats. Main measures use primary executions.

## Failure analysis

| Method | Failure type | Count |
| --- | --- | ---: |
| guided | decision | 29 |
| guided | entity_resolution | 18 |
| guided | extraction | 28 |
| guided | incorrect_acceptance | 47 |
| guided | permission | 3 |
| guided | response_error | 3 |
| guided | write_error | 8 |

Counts can overlap. See `errors.jsonl` for affected cases, `paired_cases.csv` for the comparison, and `crm-study inspect` for the original trace. Inputs, answers, responses, and model settings are saved with the run.
