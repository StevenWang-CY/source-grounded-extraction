# CRM workflow comparison

66 cases; split: test2.

## Primary executions

| Measure | direct | staged |
| --- | ---: | ---: |
| Correct writes / accept decisions | 19/32 (59.4%) | 25/36 (69.4%) |
| Useful updates written | 19/38 (50.0%) | 25/38 (65.8%) |
| Exact candidate acceptance | 13/32 (40.6%) | 25/36 (69.4%) |
| Correct decisions | 26/66 (39.4%) | 61/66 (92.4%) |
| Entity resolution | 33/66 (50.0%) | 63/66 (95.5%) |
| Evidence flags right on correct candidates | n/a (0/0) | 41/45 (91.1%) |
| Field precision | 297/315 (94.3%) | 349/366 (95.4%) |
| Field recall | 297/376 (79.0%) | 349/376 (92.8%) |
| Review/reject cases withheld | 5/28 (17.9%) | 27/28 (96.4%) |
| Quotation found in the cited source | 50/50 (100.0%) | 63/63 (100.0%) |
| Accepted updates from allowed sources | 29/32 (90.6%) | 36/36 (100.0%) |
| Cases | 66 | 66 |
| Model calls (attempted) | 66 | 129 |
| Input tokens | 56982 | 62957 |
| Output tokens | 9689 | 10592 |
| Invalid responses | 19 | 0 |
| Mean time per case, seconds | 1.94 | 2.16 |

Writes are scored from the saved CRM state. Candidate scores cover extracted fields, quote matching checks the cited text, and verification scores check support/date/conflict flags on correct candidates.

## Public and synthetic cases

| Origin | Method | Cases | Correct writes / accept decisions | Useful updates written |
| --- | --- | ---: | ---: | ---: |
| fewrel_adapted | direct | 30 | 10/17 (58.8%) | 10/24 (41.7%) |
| synthetic | direct | 36 | 9/15 (60.0%) | 9/14 (64.3%) |
| fewrel_adapted | staged | 30 | 18/23 (78.3%) | 18/24 (75.0%) |
| synthetic | staged | 36 | 7/13 (53.8%) | 7/14 (50.0%) |

## Paired outcomes

| Outcome | Cases | Both | Direct only | Staged only | Neither |
| --- | ---: | ---: | ---: | ---: | ---: |
| Wrote a useful update | 38 | 13 | 6 | 12 | 7 |
| Correct decision | 66 | 26 | 0 | 35 | 5 |
| Accepted a review/reject case | 28 | 1 | 8 | 0 | 19 |

## Fresh repeats and overhead

- direct: repeat agreement 4/6 (66.7%); 2 repeated pair(s) with an invalid response, which count as disagreements. Billed API cost: 0.0 USD.
- staged: repeat agreement 6/6 (100.0%); 0 repeated pair(s) with an invalid response, which count as disagreements. Billed API cost: 0.0 USD.

132 primary executions and 12 fresh repeats. Main measures use primary executions.

## Failure analysis

| Method | Failure type | Count |
| --- | --- | ---: |
| direct | decision | 40 |
| direct | entity_resolution | 33 |
| direct | extraction | 28 |
| direct | incorrect_acceptance | 13 |
| direct | permission | 3 |
| direct | response_error | 19 |
| direct | write_error | 1 |
| staged | decision | 5 |
| staged | entity_resolution | 3 |
| staged | extraction | 19 |
| staged | incorrect_acceptance | 11 |
| staged | verification | 4 |

Counts can overlap. See `errors.jsonl` for affected cases, `paired_cases.csv` for the comparison, and `crm-study inspect` for the original trace. Inputs, answers, responses, and model settings are saved with the run.
