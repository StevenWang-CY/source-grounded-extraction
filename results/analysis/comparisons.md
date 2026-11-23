# Comparisons across runs

Written by `scripts/analyze.py` from the saved runs.

## The staged workflow before and after the four fixes

Before is workflow 3 and after is workflow 4, on the same machine. Development and test are the cases the fixes were written from, and the second test set was built afterwards. Development before the fixes is the rerun on the M5 Max, so it differs slightly from the October run in the development table.

| Staged | Correct writes / accept decisions | Useful updates written | Review/reject cases accepted | Correct decisions | Invalid responses |
| --- | ---: | ---: | ---: | ---: | ---: |
| Development, before | 25/30 | 25/38 | 0/28 | 54/66 | 4 |
| Development, after | 29/30 | 29/38 | 0/28 | 54/66 | 4 |
| Test, before | 24/33 | 24/38 | 2/28 | 55/66 | 3 |
| Test, after | 30/37 | 30/38 | 2/28 | 59/66 | 0 |
| Second test, before | 21/29 | 21/38 | 1/28 | 53/66 | 6 |
| Second test, after | 25/30 | 25/38 | 1/28 | 54/66 | 5 |

Development: 3 wrong write to correct write, 1 not written to correct write, 1 wrong write to withheld. Correct writes gained 4, lost 0 (exact McNemar p = 0.125).
Test: 4 not written to correct write, 1 not written to wrong write, 2 wrong write to correct write, 1 wrong write to withheld. Correct writes gained 6, lost 0 (exact McNemar p = 0.031).
Second test: 2 wrong write to correct write, 1 wrong write to withheld, 2 not written to correct write. Correct writes gained 4, lost 0 (exact McNemar p = 0.125).

## Model size, on the second test set

| Variant | Correct writes / accept decisions | Useful updates written | Review/reject cases accepted | Correct decisions | Invalid responses | Mean seconds per case |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen3-1.7B, direct | 23/64 (25%–48%) | 23/38 (45%–74%) | 28/28 (88%–100%) | 36/66 (43%–66%) | 2 | 0.67 |
| Qwen3-1.7B, guided direct | 14/61 (14%–35%) | 14/38 (23%–53%) | 26/28 (77%–98%) | 37/66 (44%–67%) | 3 | 0.91 |
| Qwen3-1.7B, staged | 20/40 (35%–65%) | 20/38 (37%–68%) | 7/28 (13%–43%) | 54/66 (71%–89%) | 2 | 0.80 |
| Qwen3-4B, direct | 23/53 (31%–57%) | 23/38 (45%–74%) | 19/28 (49%–82%) | 34/66 (40%–63%) | 13 | 1.04 |
| Qwen3-4B, guided direct | 26/51 (38%–64%) | 26/38 (53%–81%) | 16/28 (39%–73%) | 47/66 (59%–81%) | 1 | 1.62 |
| Qwen3-4B, staged | 25/30 (66%–93%) | 25/38 (50%–79%) | 1/28 (1%–18%) | 54/66 (71%–89%) | 5 | 1.23 |
| Qwen3-8B, direct | 19/32 (42%–74%) | 19/38 (35%–65%) | 9/28 (18%–51%) | 26/66 (29%–51%) | 19 | 1.94 |
| Qwen3-8B, guided direct | 6/26 (11%–42%) | 6/38 (7%–30%) | 3/28 (4%–27%) | 41/66 (50%–73%) | 10 | 2.87 |
| Qwen3-8B, staged | 25/36 (53%–82%) | 25/38 (50%–79%) | 1/28 (1%–18%) | 61/66 (83%–97%) | 0 | 2.16 |
| Qwen3-14B, direct | 18/31 (41%–74%) | 18/38 (32%–63%) | 6/28 (10%–40%) | 28/66 (31%–54%) | 31 | 3.70 |
| Qwen3-14B, guided direct | 26/35 (58%–86%) | 26/38 (53%–81%) | 2/28 (2%–23%) | 56/66 (74%–92%) | 2 | 4.98 |
| Qwen3-14B, staged | 31/36 (71%–94%) | 31/38 (67%–91%) | 0/28 (0%–12%) | 61/66 (83%–97%) | 5 | 4.12 |

Direct again, reading any match that names a record ID as that record. This gives direct the benefit of the doubt on responses the workflow treats as invalid:

| Model | Correct writes / accept decisions | Useful updates written | Review/reject cases accepted | Correct decisions | Invalid responses |
| --- | ---: | ---: | ---: | ---: | ---: |
| Qwen3-1.7B | 23/64 (25%–48%) | 23/38 (45%–74%) | 28/28 (88%–100%) | 36/66 (43%–66%) | 2 |
| Qwen3-4B | 24/57 (30%–55%) | 24/38 (47%–77%) | 22/28 (60%–90%) | 37/66 (44%–67%) | 5 |
| Qwen3-8B | 21/37 (41%–71%) | 21/38 (40%–70%) | 12/28 (27%–61%) | 36/66 (43%–66%) | 3 |
| Qwen3-14B | 26/54 (35%–61%) | 26/38 (53%–81%) | 17/28 (42%–76%) | 47/66 (59%–81%) | 0 |

What the direct responses chose:

- Qwen3-1.7B: invalid accept (2), valid accept (64)
- Qwen3-4B: invalid accept (6), invalid reject (7), valid accept (53)
- Qwen3-8B: invalid accept (8), invalid reject (2), invalid review (9), valid accept (32), valid reject (13), valid review (2)
- Qwen3-14B: invalid accept (23), invalid reject (3), invalid review (5), valid accept (31), valid reject (2), valid review (2)

What the guided direct responses chose:

- Qwen3-1.7B: invalid accept (3), valid accept (61), valid reject (2)
- Qwen3-4B: invalid accept (1), valid accept (51), valid reject (9), valid review (5)
- Qwen3-8B: invalid accept (3), invalid review (7), valid accept (26), valid reject (14), valid review (16)
- Qwen3-14B: invalid accept (1), invalid reject (1), valid accept (35), valid reject (11), valid review (18)

Guided direct against staged with the same model, paired by case (exact McNemar test):

| Model and outcome | Guided direct only | Staged only | p |
| --- | ---: | ---: | ---: |
| Qwen3-1.7B: correct decision | 5 | 22 | 0.0015 |
| Qwen3-1.7B: accepted a review/reject case | 19 | 0 | 0.0000 |
| Qwen3-1.7B: wrote a useful update | 5 | 11 | 0.2101 |
| Qwen3-4B: correct decision | 9 | 16 | 0.2295 |
| Qwen3-4B: accepted a review/reject case | 15 | 0 | 0.0001 |
| Qwen3-4B: wrote a useful update | 6 | 5 | 1.0000 |
| Qwen3-8B: correct decision | 1 | 21 | 0.0000 |
| Qwen3-8B: accepted a review/reject case | 2 | 0 | 0.5000 |
| Qwen3-8B: wrote a useful update | 1 | 20 | 0.0000 |
| Qwen3-14B: correct decision | 3 | 8 | 0.2266 |
| Qwen3-14B: accepted a review/reject case | 2 | 0 | 0.5000 |
| Qwen3-14B: wrote a useful update | 2 | 7 | 0.1797 |

The steps from direct to staged, for each model:

Qwen3-1.7B

| Variant | Correct writes / accept decisions | Useful updates written | Review/reject cases accepted | Correct decisions | Invalid responses |
| --- | ---: | ---: | ---: | ---: | ---: |
| Direct | 23/64 | 23/38 | 28/28 | 36/66 | 2 |
| Direct's candidate, Python steps, no verifier | 27/45 | 27/38 | 8/28 | 57/66 | 1 |
| Staged extraction, Python steps, no verifier | 20/42 | 20/38 | 8/28 | 54/66 | 2 |
| Full staged workflow | 20/40 | 20/38 | 7/28 | 54/66 | 2 |

Qwen3-4B

| Variant | Correct writes / accept decisions | Useful updates written | Review/reject cases accepted | Correct decisions | Invalid responses |
| --- | ---: | ---: | ---: | ---: | ---: |
| Direct | 23/53 | 23/38 | 19/28 | 34/66 | 13 |
| Direct's candidate, Python steps, no verifier | 27/43 | 27/38 | 7/28 | 56/66 | 0 |
| Staged extraction, Python steps, no verifier | 25/31 | 25/38 | 2/28 | 53/66 | 5 |
| Full staged workflow | 25/30 | 25/38 | 1/28 | 54/66 | 5 |

Qwen3-8B

| Variant | Correct writes / accept decisions | Useful updates written | Review/reject cases accepted | Correct decisions | Invalid responses |
| --- | ---: | ---: | ---: | ---: | ---: |
| Direct | 19/32 | 19/38 | 9/28 | 26/66 | 19 |
| Direct's candidate, Python steps, no verifier | 26/35 | 26/38 | 7/28 | 48/66 | 0 |
| Staged extraction, Python steps, no verifier | 26/41 | 26/38 | 4/28 | 61/66 | 0 |
| Full staged workflow | 25/36 | 25/38 | 1/28 | 61/66 | 0 |

Qwen3-14B

| Variant | Correct writes / accept decisions | Useful updates written | Review/reject cases accepted | Correct decisions | Invalid responses |
| --- | ---: | ---: | ---: | ---: | ---: |
| Direct | 18/31 | 18/38 | 6/28 | 28/66 | 31 |
| Direct's candidate, Python steps, no verifier | 32/42 | 32/38 | 6/28 | 58/66 | 0 |
| Staged extraction, Python steps, no verifier | 31/40 | 31/38 | 4/28 | 57/66 | 5 |
| Full staged workflow | 31/36 | 31/38 | 0/28 | 61/66 | 5 |

## One-call workflows with Qwen3-4B

Staged is the fixed workflow (workflow 4) on development and the second test set, and the workflow as tested (workflow 3) on the test set. Direct with thinking was not run on the test set.

Development

| Workflow | Correct writes / accept decisions | Useful updates written | Review/reject cases accepted | Correct decisions | Invalid responses | Input tokens | Output tokens | Mean seconds per case |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Direct | 28/59 (35%–60%) | 28/38 (58%–85%) | 23/28 (64%–92%) | 36/66 (43%–66%) | 7 | 56462 | 8364 | 0.99 |
| Direct with thinking | 19/40 (33%–63%) | 19/38 (35%–65%) | 10/28 (21%–54%) | 33/66 (38%–62%) | 21 | 56198 | 65251 | 6.62 |
| Guided direct | 24/46 (38%–66%) | 24/38 (47%–77%) | 13/28 (30%–64%) | 45/66 (56%–78%) | 2 | 115136 | 8503 | 1.34 |
| Staged | 29/30 (83%–99%) | 29/38 (61%–87%) | 0/28 (0%–12%) | 54/66 (71%–89%) | 4 | 58905 | 10246 | 1.22 |

- Direct: invalid accept (3), invalid reject (4), valid accept (59)
- Direct with thinking: invalid accept (17), invalid reject (3), invalid unreadable (1), valid accept (40), valid reject (5)
- Guided direct: invalid reject (2), valid accept (46), valid reject (12), valid review (6)

Test

| Workflow | Correct writes / accept decisions | Useful updates written | Review/reject cases accepted | Correct decisions | Invalid responses | Input tokens | Output tokens | Mean seconds per case |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Direct | 27/59 (34%–58%) | 27/38 (55%–83%) | 21/28 (57%–87%) | 38/66 (46%–69%) | 7 | 56869 | 8778 | 1.23 |
| Guided direct | 24/51 (34%–60%) | 24/38 (47%–77%) | 16/28 (39%–73%) | 45/66 (56%–78%) | 5 | 115543 | 9049 | 1.30 |
| Staged | 24/33 (56%–85%) | 24/38 (47%–77%) | 2/28 (2%–23%) | 55/66 (73%–90%) | 3 | 61615 | 11326 | 1.56 |

- Direct: invalid accept (5), invalid reject (2), valid accept (59)
- Guided direct: invalid accept (3), invalid reject (2), valid accept (51), valid reject (6), valid review (4)

Second test

| Workflow | Correct writes / accept decisions | Useful updates written | Review/reject cases accepted | Correct decisions | Invalid responses | Input tokens | Output tokens | Mean seconds per case |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Direct | 23/53 (31%–57%) | 23/38 (45%–74%) | 19/28 (49%–82%) | 34/66 (40%–63%) | 13 | 56982 | 8888 | 1.04 |
| Direct with thinking | 14/34 (26%–58%) | 14/38 (23%–53%) | 11/28 (24%–58%) | 25/66 (27%–50%) | 28 | 56718 | 69500 | 11.54 |
| Guided direct | 26/51 (38%–64%) | 26/38 (53%–81%) | 16/28 (39%–73%) | 47/66 (59%–81%) | 1 | 115656 | 8992 | 1.62 |
| Staged | 25/30 (66%–93%) | 25/38 (50%–79%) | 1/28 (1%–18%) | 54/66 (71%–89%) | 5 | 59444 | 10585 | 1.23 |

- Direct: invalid accept (6), invalid reject (7), valid accept (53)
- Direct with thinking: invalid accept (19), invalid reject (6), invalid unreadable (3), valid accept (34), valid reject (4)
- Guided direct: invalid accept (1), valid accept (51), valid reject (9), valid review (5)

## Both test sets together

The test set and the second test set, 132 cases that were not used to build or tune any of the workflows. Staged is the workflow as tested (workflow 3) on both sets, and guided direct was tuned on the development set only.

| Workflow | Correct writes / accept decisions | Useful updates written | Review/reject cases accepted | Correct decisions | Invalid responses |
| --- | ---: | ---: | ---: | ---: | ---: |
| Direct | 50/112 (36%–54%) | 50/76 (55%–75%) | 40/56 (59%–82%) | 72/132 (46%–63%) | 20 |
| Guided direct | 50/102 (40%–59%) | 50/76 (55%–75%) | 32/56 (44%–69%) | 92/132 (61%–77%) | 6 |
| Staged | 45/62 (60%–82%) | 45/76 (48%–70%) | 3/56 (2%–15%) | 108/132 (74%–87%) | 9 |

Paired by case against staged, exact McNemar test:

| Outcome | One-call only | Staged only | p |
| --- | ---: | ---: | ---: |
| Direct: correct decision | 14 | 50 | 0.0000 |
| Direct: accepted a review/reject case | 37 | 0 | 0.0000 |
| Direct: wrote a useful update | 16 | 11 | 0.4421 |
| Guided direct: correct decision | 14 | 30 | 0.0226 |
| Guided direct: accepted a review/reject case | 29 | 0 | 0.0000 |
| Guided direct: wrote a useful update | 13 | 8 | 0.3833 |

Review/reject cases by kind. Each cell gives accepted / invalid response / held back:

| Kind of case | Should be | Cases | Direct | Guided direct | Staged |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ambiguous identity | review | 4 | 4 / 0 / 0 | 4 / 0 / 0 | 0 / 0 / 4 |
| Duplicate records | review | 10 | 10 / 0 / 0 | 10 / 0 / 0 | 0 / 0 / 10 |
| Sources that disagree | review | 4 | 3 / 1 / 0 | 3 / 0 / 1 | 3 / 0 / 1 |
| Same-date conflict with the CRM | review | 4 | 4 / 0 / 0 | 4 / 0 / 0 | 0 / 0 / 4 |
| Undated conflict with the CRM | review | 4 | 0 / 4 / 0 | 1 / 0 / 3 | 0 / 0 / 4 |
| Future appointment | review | 4 | 3 / 1 / 0 | 4 / 0 / 0 | 0 / 0 / 4 |
| Tentative claim | review | 4 | 0 / 4 / 0 | 0 / 0 / 4 | 0 / 0 / 4 |
| Older than the CRM fact | reject | 4 | 4 / 0 / 0 | 2 / 0 / 2 | 0 / 0 / 4 |
| Denied claim | reject | 4 | 0 / 4 / 0 | 0 / 2 / 2 | 0 / 0 / 4 |
| Disallowed source | reject | 10 | 10 / 0 / 0 | 3 / 0 / 7 | 0 / 0 / 10 |
| Irrelevant document | reject | 4 | 2 / 2 / 0 | 1 / 0 / 3 | 0 / 0 / 4 |
