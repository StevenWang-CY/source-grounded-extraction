# CRM workflow comparison

66 cases; split: development.

## Primary executions

| Measure | staged |
| --- | ---: |
| Correct writes / accept decisions | 38/39 (97.4%) |
| Useful updates written | 38/38 (100.0%) |
| Exact candidate acceptance | 38/39 (97.4%) |
| Correct decisions | 65/66 (98.5%) |
| Entity resolution | 66/66 (100.0%) |
| Evidence flags right on correct candidates | 58/64 (90.6%) |
| Field precision | 376/376 (100.0%) |
| Field recall | 376/376 (100.0%) |
| Review/reject cases withheld | 27/28 (96.4%) |
| Quotation found in the cited source | 64/64 (100.0%) |
| Accepted updates from allowed sources | 39/39 (100.0%) |
| Cases | 66 |
| Model calls (attempted) | 64 |
| Input tokens | 28957 |
| Output tokens | 5770 |
| Invalid responses | 0 |
| Mean time per case, seconds | 0.68 |

Writes are scored from the saved CRM state. Candidate scores cover extracted fields, quote matching checks the cited text, and verification scores check support/date/conflict flags on correct candidates.

## Public and synthetic cases

| Origin | Method | Cases | Correct writes / accept decisions | Useful updates written |
| --- | --- | ---: | ---: | ---: |
| fewrel_adapted | staged | 30 | 24/24 (100.0%) | 24/24 (100.0%) |
| synthetic | staged | 36 | 14/15 (93.3%) | 14/14 (100.0%) |

## Fresh repeats and overhead

- staged: repeat agreement n/a (0/0); 0 repeated pair(s) with an invalid response, which count as disagreements. Billed API cost: 0.0 USD.

66 primary executions and 0 fresh repeats. Main measures use primary executions.

## Failure analysis

| Method | Failure type | Count |
| --- | --- | ---: |
| staged | decision | 1 |
| staged | incorrect_acceptance | 1 |
| staged | verification | 6 |

Counts can overlap. See `errors.jsonl` for affected cases, `paired_cases.csv` for the comparison, and `crm-study inspect` for the original trace. Inputs, answers, responses, and model settings are saved with the run.
