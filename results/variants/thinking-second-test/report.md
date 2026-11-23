# CRM workflow comparison

66 cases; split: test2.

## Primary executions

| Measure | direct |
| --- | ---: |
| Correct writes / accept decisions | 14/34 (41.2%) |
| Useful updates written | 14/38 (36.8%) |
| Exact candidate acceptance | 6/34 (17.6%) |
| Correct decisions | 25/66 (37.9%) |
| Entity resolution | 25/66 (37.9%) |
| Evidence flags right on correct candidates | n/a (0/0) |
| Field precision | 325/352 (92.3%) |
| Field recall | 325/376 (86.4%) |
| Review/reject cases withheld | 2/28 (7.1%) |
| Quotation found in the cited source | 56/56 (100.0%) |
| Accepted updates from allowed sources | 31/34 (91.2%) |
| Cases | 66 |
| Model calls (attempted) | 66 |
| Input tokens | 56718 |
| Output tokens | 69500 |
| Invalid responses | 28 |
| Mean time per case, seconds | 11.54 |

Writes are scored from the saved CRM state. Candidate scores cover extracted fields, quote matching checks the cited text, and verification scores check support/date/conflict flags on correct candidates.

## Public and synthetic cases

| Origin | Method | Cases | Correct writes / accept decisions | Useful updates written |
| --- | --- | ---: | ---: | ---: |
| fewrel_adapted | direct | 30 | 8/19 (42.1%) | 8/24 (33.3%) |
| synthetic | direct | 36 | 6/15 (40.0%) | 6/14 (42.9%) |

## Fresh repeats and overhead

- direct: repeat agreement 2/6 (33.3%); 4 repeated pair(s) with an invalid response, which count as disagreements. Billed API cost: 0.0 USD.

66 primary executions and 6 fresh repeats. Main measures use primary executions.

## Failure analysis

| Method | Failure type | Count |
| --- | --- | ---: |
| direct | decision | 41 |
| direct | entity_resolution | 41 |
| direct | extraction | 30 |
| direct | incorrect_acceptance | 20 |
| direct | permission | 3 |
| direct | response_error | 28 |
| direct | write_error | 1 |

Counts can overlap. See `errors.jsonl` for affected cases, `paired_cases.csv` for the comparison, and `crm-study inspect` for the original trace. Inputs, answers, responses, and model settings are saved with the run.
