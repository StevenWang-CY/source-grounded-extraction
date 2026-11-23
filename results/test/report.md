# CRM workflow comparison

66 cases; split: test.

## Primary executions

| Measure | direct | staged |
| --- | ---: | ---: |
| Correct writes / accept decisions | 27/59 (45.8%) | 24/33 (72.7%) |
| Useful updates written | 27/38 (71.1%) | 24/38 (63.2%) |
| Exact candidate acceptance | 20/59 (33.9%) | 23/33 (69.7%) |
| Correct decisions | 38/66 (57.6%) | 55/66 (83.3%) |
| Entity resolution | 48/66 (72.7%) | 54/66 (81.8%) |
| Evidence flags right on correct candidates | n/a (0/0) | 40/44 (90.9%) |
| Field precision | 358/398 (89.9%) | 340/361 (94.2%) |
| Field recall | 358/376 (95.2%) | 340/376 (90.4%) |
| Review/reject cases withheld | 0/28 (0.0%) | 26/28 (92.9%) |
| Quotation found in the cited source | 65/66 (98.5%) | 59/60 (98.3%) |
| Accepted updates from allowed sources | 54/59 (91.5%) | 33/33 (100.0%) |
| Cases | 66 | 66 |
| Model calls (attempted) | 66 | 126 |
| Input tokens | 56869 | 61615 |
| Output tokens | 8778 | 11326 |
| Invalid responses | 7 | 3 |
| Mean time per case, seconds | 1.23 | 1.56 |

Writes are scored from the saved CRM state. Candidate scores cover extracted fields, quote matching checks the cited text, and verification scores check support/date/conflict flags on correct candidates.

## Public and synthetic cases

| Origin | Method | Cases | Correct writes / accept decisions | Useful updates written |
| --- | --- | ---: | ---: | ---: |
| fewrel_adapted | direct | 30 | 18/30 (60.0%) | 18/24 (75.0%) |
| synthetic | direct | 36 | 9/29 (31.0%) | 9/14 (64.3%) |
| fewrel_adapted | staged | 30 | 11/17 (64.7%) | 11/24 (45.8%) |
| synthetic | staged | 36 | 13/16 (81.2%) | 13/14 (92.9%) |

## Paired outcomes

| Outcome | Cases | Both | Direct only | Staged only | Neither |
| --- | ---: | ---: | ---: | ---: | ---: |
| Wrote a useful update | 38 | 19 | 8 | 5 | 6 |
| Correct decision | 66 | 31 | 7 | 24 | 4 |
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
| staged | decision | 11 |
| staged | entity_resolution | 12 |
| staged | extraction | 21 |
| staged | incorrect_acceptance | 9 |
| staged | quote | 1 |
| staged | response_error | 3 |
| staged | verification | 4 |

Counts can overlap. See `errors.jsonl` for affected cases, `paired_cases.csv` for the comparison, and `crm-study inspect` for the original trace. Inputs, answers, responses, and model settings are saved with the run.
