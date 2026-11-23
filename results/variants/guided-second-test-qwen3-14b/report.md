# CRM workflow comparison

66 cases; split: test2.

## Primary executions

| Measure | guided |
| --- | ---: |
| Correct writes / accept decisions | 26/35 (74.3%) |
| Useful updates written | 26/38 (68.4%) |
| Exact candidate acceptance | 26/35 (74.3%) |
| Correct decisions | 56/66 (84.8%) |
| Entity resolution | 59/66 (89.4%) |
| Evidence flags right on correct candidates | n/a (0/0) |
| Field precision | 352/362 (97.2%) |
| Field recall | 352/376 (93.6%) |
| Review/reject cases withheld | 25/28 (89.3%) |
| Quotation found in the cited source | 61/61 (100.0%) |
| Accepted updates from allowed sources | 35/35 (100.0%) |
| Cases | 66 |
| Model calls (attempted) | 66 |
| Input tokens | 115656 |
| Output tokens | 10575 |
| Invalid responses | 2 |
| Mean time per case, seconds | 4.98 |

Writes are scored from the saved CRM state. Candidate scores cover extracted fields, quote matching checks the cited text, and verification scores check support/date/conflict flags on correct candidates.

## Public and synthetic cases

| Origin | Method | Cases | Correct writes / accept decisions | Useful updates written |
| --- | --- | ---: | ---: | ---: |
| fewrel_adapted | guided | 30 | 16/22 (72.7%) | 16/24 (66.7%) |
| synthetic | guided | 36 | 10/13 (76.9%) | 10/14 (71.4%) |

## Fresh repeats and overhead

- guided: repeat agreement 6/6 (100.0%); 0 repeated pair(s) with an invalid response, which count as disagreements. Billed API cost: 0.0 USD.

66 primary executions and 6 fresh repeats. Main measures use primary executions.

## Failure analysis

| Method | Failure type | Count |
| --- | --- | ---: |
| guided | decision | 10 |
| guided | entity_resolution | 7 |
| guided | extraction | 10 |
| guided | incorrect_acceptance | 9 |
| guided | response_error | 2 |

Counts can overlap. See `errors.jsonl` for affected cases, `paired_cases.csv` for the comparison, and `crm-study inspect` for the original trace. Inputs, answers, responses, and model settings are saved with the run.
