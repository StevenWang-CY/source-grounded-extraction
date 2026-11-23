# CRM workflow comparison

66 cases; split: development.

## Primary executions

| Measure | direct |
| --- | ---: |
| Correct writes / accept decisions | 19/40 (47.5%) |
| Useful updates written | 19/38 (50.0%) |
| Exact candidate acceptance | 8/40 (20.0%) |
| Correct decisions | 33/66 (50.0%) |
| Entity resolution | 29/66 (43.9%) |
| Evidence flags right on correct candidates | n/a (0/0) |
| Field precision | 339/371 (91.4%) |
| Field recall | 339/376 (90.2%) |
| Review/reject cases withheld | 4/28 (14.3%) |
| Quotation found in the cited source | 58/59 (98.3%) |
| Accepted updates from allowed sources | 39/40 (97.5%) |
| Cases | 66 |
| Model calls (attempted) | 66 |
| Input tokens | 56198 |
| Output tokens | 65251 |
| Invalid responses | 21 |
| Mean time per case, seconds | 6.62 |

Writes are scored from the saved CRM state. Candidate scores cover extracted fields, quote matching checks the cited text, and verification scores check support/date/conflict flags on correct candidates.

## Public and synthetic cases

| Origin | Method | Cases | Correct writes / accept decisions | Useful updates written |
| --- | --- | ---: | ---: | ---: |
| fewrel_adapted | direct | 30 | 9/20 (45.0%) | 9/24 (37.5%) |
| synthetic | direct | 36 | 10/20 (50.0%) | 10/14 (71.4%) |

## Fresh repeats and overhead

- direct: repeat agreement 4/6 (66.7%); 2 repeated pair(s) with an invalid response, which count as disagreements. Billed API cost: 0.0 USD.

66 primary executions and 6 fresh repeats. Main measures use primary executions.

## Failure analysis

| Method | Failure type | Count |
| --- | --- | ---: |
| direct | decision | 33 |
| direct | entity_resolution | 37 |
| direct | extraction | 29 |
| direct | incorrect_acceptance | 21 |
| direct | permission | 1 |
| direct | quote | 1 |
| direct | response_error | 21 |
| direct | write_error | 1 |

Counts can overlap. See `errors.jsonl` for affected cases, `paired_cases.csv` for the comparison, and `crm-study inspect` for the original trace. Inputs, answers, responses, and model settings are saved with the run.
