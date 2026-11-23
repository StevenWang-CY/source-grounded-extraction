# CRM workflow comparison

66 cases; split: test.

## Primary executions

| Measure | direct | staged |
| --- | ---: | ---: |
| Correct writes / accept decisions | 27/59 (45.8%) | 30/37 (81.1%) |
| Useful updates written | 27/38 (71.1%) | 30/38 (78.9%) |
| Exact candidate acceptance | 20/59 (33.9%) | 27/37 (73.0%) |
| Correct decisions | 38/66 (57.6%) | 59/66 (89.4%) |
| Entity resolution | 48/66 (72.7%) | 61/66 (92.4%) |
| Evidence flags right on correct candidates | n/a (0/0) | 44/48 (91.7%) |
| Field precision | 358/398 (89.9%) | 353/373 (94.6%) |
| Field recall | 358/376 (95.2%) | 353/376 (93.9%) |
| Review/reject cases withheld | 0/28 (0.0%) | 26/28 (92.9%) |
| Quotation found in the cited source | 65/66 (98.5%) | 61/63 (96.8%) |
| Accepted updates from allowed sources | 54/59 (91.5%) | 37/37 (100.0%) |
| Cases | 66 | 66 |
| Model calls (attempted) | 66 | 129 |
| Input tokens | 56869 | 62988 |
| Output tokens | 8778 | 11549 |
| Invalid responses | 7 | 0 |
| Mean time per case, seconds | 1.18 | 1.54 |

Writes are scored from the saved CRM state. Candidate scores cover extracted fields, quote matching checks the cited text, and verification scores check support/date/conflict flags on correct candidates.

## Public and synthetic cases

| Origin | Method | Cases | Correct writes / accept decisions | Useful updates written |
| --- | --- | ---: | ---: | ---: |
| fewrel_adapted | direct | 30 | 18/30 (60.0%) | 18/24 (75.0%) |
| synthetic | direct | 36 | 9/29 (31.0%) | 9/14 (64.3%) |
| fewrel_adapted | staged | 30 | 16/21 (76.2%) | 16/24 (66.7%) |
| synthetic | staged | 36 | 14/16 (87.5%) | 14/14 (100.0%) |

## Paired outcomes

| Outcome | Cases | Both | Direct only | Staged only | Neither |
| --- | ---: | ---: | ---: | ---: | ---: |
| Wrote a useful update | 38 | 24 | 3 | 6 | 5 |
| Correct decision | 66 | 35 | 3 | 24 | 4 |
| Accepted a review/reject case | 28 | 2 | 19 | 0 | 7 |

## Fresh repeats and overhead

- direct: repeat agreement 5/6 (83.3%); 1 repeated pair(s) with an invalid response, which count as disagreements. Billed API cost: 0.0 USD.
- staged: repeat agreement 6/6 (100.0%); 0 repeated pair(s) with an invalid response, which count as disagreements. Billed API cost: 0.0 USD.

132 primary executions and 12 fresh repeats. Main measures use primary executions.

## Failure analysis

| Method | Failure type | Count |
| --- | --- | ---: |
| direct | decision | 28 |
| direct | entity_resolution | 18 |
| direct | extraction | 23 |
| direct | incorrect_acceptance | 32 |
| direct | permission | 5 |
| direct | quote | 1 |
| direct | response_error | 7 |
| direct | write_error | 2 |
| staged | decision | 7 |
| staged | entity_resolution | 5 |
| staged | extraction | 17 |
| staged | incorrect_acceptance | 7 |
| staged | quote | 2 |
| staged | verification | 4 |

Counts can overlap. See `errors.jsonl` for affected cases, `paired_cases.csv` for the comparison, and `crm-study inspect` for the original trace. Inputs, answers, responses, and model settings are saved with the run.
