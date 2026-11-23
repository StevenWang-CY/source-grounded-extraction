# CRM workflow comparison

66 cases; split: test2.

## Primary executions

| Measure | guided |
| --- | ---: |
| Correct writes / accept decisions | 6/26 (23.1%) |
| Useful updates written | 6/38 (15.8%) |
| Exact candidate acceptance | 6/26 (23.1%) |
| Correct decisions | 41/66 (62.1%) |
| Entity resolution | 23/66 (34.8%) |
| Evidence flags right on correct candidates | n/a (0/0) |
| Field precision | 312/324 (96.3%) |
| Field recall | 312/376 (83.0%) |
| Review/reject cases withheld | 19/28 (67.9%) |
| Quotation found in the cited source | 53/53 (100.0%) |
| Accepted updates from allowed sources | 24/26 (92.3%) |
| Cases | 66 |
| Model calls (attempted) | 66 |
| Input tokens | 115656 |
| Output tokens | 11915 |
| Invalid responses | 10 |
| Mean time per case, seconds | 2.87 |

Writes are scored from the saved CRM state. Candidate scores cover extracted fields, quote matching checks the cited text, and verification scores check support/date/conflict flags on correct candidates.

## Public and synthetic cases

| Origin | Method | Cases | Correct writes / accept decisions | Useful updates written |
| --- | --- | ---: | ---: | ---: |
| fewrel_adapted | guided | 30 | 1/18 (5.6%) | 1/24 (4.2%) |
| synthetic | guided | 36 | 5/8 (62.5%) | 5/14 (35.7%) |

## Fresh repeats and overhead

- guided: repeat agreement 5/6 (83.3%); 1 repeated pair(s) with an invalid response, which count as disagreements. Billed API cost: 0.0 USD.

66 primary executions and 6 fresh repeats. Main measures use primary executions.

## Failure analysis

| Method | Failure type | Count |
| --- | --- | ---: |
| guided | decision | 25 |
| guided | entity_resolution | 43 |
| guided | extraction | 22 |
| guided | incorrect_acceptance | 20 |
| guided | permission | 2 |
| guided | response_error | 10 |
| guided | write_error | 1 |

Counts can overlap. See `errors.jsonl` for affected cases, `paired_cases.csv` for the comparison, and `crm-study inspect` for the original trace. Inputs, answers, responses, and model settings are saved with the run.
