# CRM workflow comparison

66 cases; split: development.

## Primary executions

| Measure | direct | staged |
| --- | ---: | ---: |
| Correct writes / accept decisions | 28/59 (47.5%) | 25/30 (83.3%) |
| Useful updates written | 28/38 (73.7%) | 25/38 (65.8%) |
| Exact candidate acceptance | 20/59 (33.9%) | 25/30 (83.3%) |
| Correct decisions | 36/66 (54.5%) | 54/66 (81.8%) |
| Entity resolution | 49/66 (74.2%) | 56/66 (84.8%) |
| Evidence flags right on correct candidates | n/a (0/0) | 39/41 (95.1%) |
| Field precision | 359/388 (92.5%) | 325/334 (97.3%) |
| Field recall | 359/376 (95.5%) | 325/376 (86.4%) |
| Review/reject cases withheld | 0/28 (0.0%) | 27/28 (96.4%) |
| Quotation found in the cited source | 63/64 (98.4%) | 56/56 (100.0%) |
| Accepted updates from allowed sources | 54/59 (91.5%) | 30/30 (100.0%) |
| Cases | 66 | 66 |
| Model calls (attempted) | 66 | 122 |
| Input tokens | 56462 | 58926 |
| Output tokens | 8364 | 10278 |
| Invalid responses | 7 | 4 |
| Mean time per case, seconds | 1.25 | 1.53 |

Writes are scored from the saved CRM state. Candidate scores cover extracted fields, quote matching checks the cited text, and verification scores check support/date/conflict flags on correct candidates.

## Public and synthetic cases

| Origin | Method | Cases | Correct writes / accept decisions | Useful updates written |
| --- | --- | ---: | ---: | ---: |
| fewrel_adapted | direct | 30 | 19/29 (65.5%) | 19/24 (79.2%) |
| synthetic | direct | 36 | 9/30 (30.0%) | 9/14 (64.3%) |
| fewrel_adapted | staged | 30 | 15/17 (88.2%) | 15/24 (62.5%) |
| synthetic | staged | 36 | 10/13 (76.9%) | 10/14 (71.4%) |

## Paired outcomes

| Outcome | Cases | Both | Direct only | Staged only | Neither |
| --- | ---: | ---: | ---: | ---: | ---: |
| Wrote a useful update | 38 | 20 | 8 | 5 | 5 |
| Correct decision | 66 | 29 | 7 | 25 | 5 |
| Accepted a review/reject case | 28 | 0 | 23 | 0 | 5 |

## Fresh repeats and overhead

- direct: repeat agreement 6/6 (100.0%); 0 repeated pair(s) with an invalid response, which count as disagreements. Billed API cost: 0.0 USD.
- staged: repeat agreement 5/6 (83.3%); 1 repeated pair(s) with an invalid response, which count as disagreements. Billed API cost: 0.0 USD.

132 primary executions and 12 fresh repeats. Main measures use primary executions.

## Failure analysis

| Method | Failure type | Count |
| --- | --- | ---: |
| direct | decision | 30 |
| direct | entity_resolution | 17 |
| direct | extraction | 19 |
| direct | incorrect_acceptance | 31 |
| direct | permission | 5 |
| direct | quote | 1 |
| direct | response_error | 7 |
| direct | write_error | 2 |
| staged | decision | 12 |
| staged | entity_resolution | 10 |
| staged | extraction | 23 |
| staged | incorrect_acceptance | 5 |
| staged | response_error | 4 |
| staged | verification | 2 |

Counts can overlap. See `errors.jsonl` for affected cases, `paired_cases.csv` for the comparison, and `crm-study inspect` for the original trace. Inputs, answers, responses, and model settings are saved with the run.
