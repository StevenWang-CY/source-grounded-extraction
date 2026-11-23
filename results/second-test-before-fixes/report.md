# CRM workflow comparison

66 cases; split: test2.

## Primary executions

| Measure | staged |
| --- | ---: |
| Correct writes / accept decisions | 21/29 (72.4%) |
| Useful updates written | 21/38 (55.3%) |
| Exact candidate acceptance | 21/29 (72.4%) |
| Correct decisions | 53/66 (80.3%) |
| Entity resolution | 52/66 (78.8%) |
| Evidence flags right on correct candidates | 37/39 (94.9%) |
| Field precision | 307/327 (93.9%) |
| Field recall | 307/376 (81.6%) |
| Review/reject cases withheld | 27/28 (96.4%) |
| Quotation found in the cited source | 54/54 (100.0%) |
| Accepted updates from allowed sources | 29/29 (100.0%) |
| Cases | 66 |
| Model calls (attempted) | 120 |
| Input tokens | 59040 |
| Output tokens | 10517 |
| Invalid responses | 6 |
| Mean time per case, seconds | 1.34 |

Writes are scored from the saved CRM state. Candidate scores cover extracted fields, quote matching checks the cited text, and verification scores check support/date/conflict flags on correct candidates.

## Public and synthetic cases

| Origin | Method | Cases | Correct writes / accept decisions | Useful updates written |
| --- | --- | ---: | ---: | ---: |
| fewrel_adapted | staged | 30 | 9/15 (60.0%) | 9/24 (37.5%) |
| synthetic | staged | 36 | 12/14 (85.7%) | 12/14 (85.7%) |

## Fresh repeats and overhead

- staged: repeat agreement 6/6 (100.0%); 0 repeated pair(s) with an invalid response, which count as disagreements. Billed API cost: 0.0 USD.

66 primary executions and 6 fresh repeats. Main measures use primary executions.

## Failure analysis

| Method | Failure type | Count |
| --- | --- | ---: |
| staged | decision | 13 |
| staged | entity_resolution | 14 |
| staged | extraction | 25 |
| staged | incorrect_acceptance | 8 |
| staged | response_error | 6 |
| staged | verification | 2 |

Counts can overlap. See `errors.jsonl` for affected cases, `paired_cases.csv` for the comparison, and `crm-study inspect` for the original trace. Inputs, answers, responses, and model settings are saved with the run.
