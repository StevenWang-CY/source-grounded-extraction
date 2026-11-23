# CRM workflow comparison

66 cases; split: test2.

## Primary executions

| Measure | direct | staged |
| --- | ---: | ---: |
| Correct writes / accept decisions | 23/64 (35.9%) | 20/40 (50.0%) |
| Useful updates written | 23/38 (60.5%) | 20/38 (52.6%) |
| Exact candidate acceptance | 20/64 (31.2%) | 9/40 (22.5%) |
| Correct decisions | 36/66 (54.5%) | 54/66 (81.8%) |
| Entity resolution | 50/66 (75.8%) | 54/66 (81.8%) |
| Evidence flags right on correct candidates | n/a (0/0) | 21/24 (87.5%) |
| Field precision | 343/388 (88.4%) | 322/402 (80.1%) |
| Field recall | 343/376 (91.2%) | 322/376 (85.6%) |
| Review/reject cases withheld | 0/28 (0.0%) | 21/28 (75.0%) |
| Quotation found in the cited source | 64/64 (100.0%) | 64/64 (100.0%) |
| Accepted updates from allowed sources | 59/64 (92.2%) | 40/40 (100.0%) |
| Cases | 66 | 66 |
| Model calls (attempted) | 66 | 130 |
| Input tokens | 56982 | 63791 |
| Output tokens | 11695 | 13762 |
| Invalid responses | 2 | 2 |
| Mean time per case, seconds | 0.67 | 0.80 |

Writes are scored from the saved CRM state. Candidate scores cover extracted fields, quote matching checks the cited text, and verification scores check support/date/conflict flags on correct candidates.

## Public and synthetic cases

| Origin | Method | Cases | Correct writes / accept decisions | Useful updates written |
| --- | --- | ---: | ---: | ---: |
| fewrel_adapted | direct | 30 | 17/29 (58.6%) | 17/24 (70.8%) |
| synthetic | direct | 36 | 6/35 (17.1%) | 6/14 (42.9%) |
| fewrel_adapted | staged | 30 | 14/21 (66.7%) | 14/24 (58.3%) |
| synthetic | staged | 36 | 6/19 (31.6%) | 6/14 (42.9%) |

## Paired outcomes

| Outcome | Cases | Both | Direct only | Staged only | Neither |
| --- | ---: | ---: | ---: | ---: | ---: |
| Wrote a useful update | 38 | 15 | 8 | 5 | 10 |
| Correct decision | 66 | 31 | 5 | 23 | 7 |
| Accepted a review/reject case | 28 | 7 | 21 | 0 | 0 |

## Fresh repeats and overhead

- direct: repeat agreement 6/6 (100.0%); 0 repeated pair(s) with an invalid response, which count as disagreements. Billed API cost: 0.0 USD.
- staged: repeat agreement 6/6 (100.0%); 0 repeated pair(s) with an invalid response, which count as disagreements. Billed API cost: 0.0 USD.

132 primary executions and 12 fresh repeats. Main measures use primary executions.

## Failure analysis

| Method | Failure type | Count |
| --- | --- | ---: |
| direct | decision | 30 |
| direct | entity_resolution | 16 |
| direct | extraction | 26 |
| direct | incorrect_acceptance | 41 |
| direct | permission | 5 |
| direct | response_error | 2 |
| direct | write_error | 7 |
| staged | decision | 12 |
| staged | entity_resolution | 12 |
| staged | extraction | 42 |
| staged | incorrect_acceptance | 20 |
| staged | response_error | 2 |
| staged | verification | 3 |

Counts can overlap. See `errors.jsonl` for affected cases, `paired_cases.csv` for the comparison, and `crm-study inspect` for the original trace. Inputs, answers, responses, and model settings are saved with the run.
