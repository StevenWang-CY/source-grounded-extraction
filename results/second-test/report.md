# CRM workflow comparison

66 cases; split: test2.

## Primary executions

| Measure | direct | staged |
| --- | ---: | ---: |
| Correct writes / accept decisions | 23/53 (43.4%) | 25/30 (83.3%) |
| Useful updates written | 23/38 (60.5%) | 25/38 (65.8%) |
| Exact candidate acceptance | 19/53 (35.8%) | 23/30 (76.7%) |
| Correct decisions | 34/66 (51.5%) | 54/66 (81.8%) |
| Entity resolution | 44/66 (66.7%) | 54/66 (81.8%) |
| Evidence flags right on correct candidates | n/a (0/0) | 39/41 (95.1%) |
| Field precision | 347/389 (89.2%) | 312/329 (94.8%) |
| Field recall | 347/376 (92.3%) | 312/376 (83.0%) |
| Review/reject cases withheld | 0/28 (0.0%) | 27/28 (96.4%) |
| Quotation found in the cited source | 62/63 (98.4%) | 55/55 (100.0%) |
| Accepted updates from allowed sources | 48/53 (90.6%) | 30/30 (100.0%) |
| Cases | 66 | 66 |
| Model calls (attempted) | 66 | 121 |
| Input tokens | 56982 | 59444 |
| Output tokens | 8888 | 10585 |
| Invalid responses | 13 | 5 |
| Mean time per case, seconds | 1.04 | 1.23 |

Writes are scored from the saved CRM state. Candidate scores cover extracted fields, quote matching checks the cited text, and verification scores check support/date/conflict flags on correct candidates.

## Public and synthetic cases

| Origin | Method | Cases | Correct writes / accept decisions | Useful updates written |
| --- | --- | ---: | ---: | ---: |
| fewrel_adapted | direct | 30 | 15/28 (53.6%) | 15/24 (62.5%) |
| synthetic | direct | 36 | 8/25 (32.0%) | 8/14 (57.1%) |
| fewrel_adapted | staged | 30 | 12/16 (75.0%) | 12/24 (50.0%) |
| synthetic | staged | 36 | 13/14 (92.9%) | 13/14 (92.9%) |

## Paired outcomes

| Outcome | Cases | Both | Direct only | Staged only | Neither |
| --- | ---: | ---: | ---: | ---: | ---: |
| Wrote a useful update | 38 | 19 | 4 | 6 | 9 |
| Correct decision | 66 | 28 | 6 | 26 | 6 |
| Accepted a review/reject case | 28 | 1 | 18 | 0 | 9 |

## Fresh repeats and overhead

- direct: repeat agreement 5/6 (83.3%); 1 repeated pair(s) with an invalid response, which count as disagreements. Billed API cost: 0.0 USD.
- staged: repeat agreement 6/6 (100.0%); 0 repeated pair(s) with an invalid response, which count as disagreements. Billed API cost: 0.0 USD.

132 primary executions and 12 fresh repeats. Main measures use primary executions.

## Failure analysis

| Method | Failure type | Count |
| --- | --- | ---: |
| direct | decision | 32 |
| direct | entity_resolution | 22 |
| direct | extraction | 23 |
| direct | incorrect_acceptance | 30 |
| direct | permission | 5 |
| direct | quote | 1 |
| direct | response_error | 13 |
| direct | write_error | 2 |
| staged | decision | 12 |
| staged | entity_resolution | 12 |
| staged | extraction | 23 |
| staged | incorrect_acceptance | 5 |
| staged | response_error | 5 |
| staged | verification | 2 |

Counts can overlap. See `errors.jsonl` for affected cases, `paired_cases.csv` for the comparison, and `crm-study inspect` for the original trace. Inputs, answers, responses, and model settings are saved with the run.
