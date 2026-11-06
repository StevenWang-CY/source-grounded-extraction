# Design memo

This memo describes how the two workflows work, how they are scored, and which earlier work
the design draws on. Numbers in brackets refer to the references at the end.

Each case gives a query, source documents, an as-of date, and a small CRM. The CRM is
simulated in memory.

## The two workflows

```text
Direct: sources + CRM -> one model response (fact, match, decision) -> CRM writer
Staged: sources -> model extraction -> Python matching against the CRM
        -> model evidence check -> Python decision rules -> CRM writer
```

Both workflows get the same extraction instructions and the same update policy. Direct is
asked to follow the policy in its one response, and staged applies it in Python. In staged,
the extractor and the verifier read only the sources, while matching and the decision rules
also read the CRM.

Splitting a task into chained steps with visible results comes from Wu et al. [1], and Khot
et al. [2] show that a step can be ordinary code instead of a model.

## What the model extracts

A candidate update has an entity type, a subject, an attribute, a value, an organization, an
effective date, a source ID, and an exact quotation from that source. The attributes are a
person's role and employer, a company's headquarters and owner, and the company on a deal. A
date the source does not state stays null.

## Matching a record

Matching uses normalized names, declared aliases, and a person's organization. One match
selects the record, and several matches go to review. A name with no match can create a new
record. A name match also goes to review when the organization on the CRM record differs from
the stated one or is missing.

These outcomes (matched, ambiguous, new) mirror the link, possible link, and non-link of
Fellegi and Sunter [3], and ambiguous cases go to a reviewer. Christophides et al. [4] survey
the wider entity-resolution problem.

## Checking the evidence and deciding

The verifier labels the claim supported, uncertain, or contradicted, much as FEVER [5] labels
claims against evidence. It also says whether the date is supported and whether allowed
sources disagree. It runs as its own call, like the verification step in Chain-of-Verification
[6]. The decision rules then combine its answer with the source permissions and the existing
CRM facts.

| Situation | Decision |
| --- | --- |
| Supported fact, allowed source, exact quote, clear identity | Accept |
| Missing candidate, source, or quote, disallowed source, or explicit denial | Reject |
| Ambiguous identity, subject absent from the source, uncertain support, or source conflict | Review |
| Effective date older than the existing fact | Reject |
| Conflicting values with equal or missing dates | Review |
| Undated update that would replace a dated fact | Review |
| Future appointment, or a current role with no organization | Review |

Requiring an exact quotation is a simple, checkable form of the attribution that Rashkin et
al. [7] and Gao et al. [8] measure in generated text. Facts change over time [9], so a
publication date and an effective date are separate fields. Sources can disagree [10], which
the verifier reports. In historical tasks, the relationship stated in the passage is what
counts, and an explicit later correction can replace an earlier statement.

Sending a doubtful case to review is a reject option in the sense of Chow [11]. The balance
between accuracy on the accepted cases and coverage of the useful ones resembles the tradeoff
studied in selective classification [12].

The writer copies the initial CRM, checks the record type, and stores an accepted value with
its date, source, and quote. Other records and facts stay as they were. Every execution starts
from the same original CRM, and an invalid response writes nothing.

## Running and saving

The runner alternates which method goes first, saves each execution as it finishes, and can
resume after an interruption. Each saved trace has the messages, responses, intermediate
steps, CRM changes, timing, and token counts, so saved responses can run through the Python
steps again without the model. The answer keys are used only for scoring, after the model has
run. The first scoring of a run saves the answers it used, and a later change to the answer
keys goes to a separate analysis folder.

The model is Qwen3-4B [13] in 4-bit form on MLX [14], with temperature 0 (greedy decoding),
thinking turned off, and a 512-token limit. Cases run in an order shuffled with seed 17.

Each run records the versions it used. The numbers count the changes made during development,
and they are now dataset 2, prompt 4, workflow 3, and scoring 4. Keeping them with the saved
runs stops results from different versions being mixed by accident.

## Measures

| Measure | What it counts |
| --- | --- |
| Correct writes / accept decisions | Correct saved CRM writes over accept decisions, also called accepted-update accuracy |
| Useful updates written | Correct saved CRM writes over cases with a valid update |
| Review/reject cases accepted | Accept decisions on cases that should go to review or be rejected |
| Correct decisions | Correct accept, review, or reject, with invalid responses counted as wrong |
| Invalid responses | Responses that fail validation and write nothing |
| Field precision and recall | Matching non-null fields of the extracted candidate |
| Entity resolution | Correct matched, new, or ambiguous status and record ID |
| Quotation and permission | Quote found in its cited source, and the source allowed |
| Evidence flags | Correct support, date, and conflict flags on correctly extracted candidates |
| Consistency and cost | Agreement across repeats, time, calls, tokens, and API cost |

Write scoring looks at the saved CRM itself, including the target, value, date, source, quote,
and whether unrelated records stayed the same. Main results use one execution per case and
method, and repeats only measure consistency. Local inference bills no API cost.

The reports give 95% Wilson intervals [15] for rates and an exact McNemar test [16] for paired
differences. Kapoor et al. [17] argue that agent evaluations should look beyond accuracy and
work out where a gain comes from, which is why the analysis also scores parts of the workflow
separately.

## Code layout

| Module | What it does |
| --- | --- |
| `schema.py` | The candidate, normalization, and quotation checks |
| `prompts.py` | The extraction instructions, the policy text, and the three model tasks |
| `pipeline.py` | The direct and staged workflows and their traces |
| `resolution.py` | Matching a candidate to CRM records |
| `policy.py` | The decision rules and the CRM writer |
| `backends.py` | Local MLX inference, an HTTP adapter, and replay of saved responses |
| `evaluation.py`, `reporting.py` | Scoring saved runs and writing their reports |
| `variants.py`, `stats.py` | Rescoring parts of the workflow, intervals, and paired tests |
| `data.py` | Dataset checks and the grouped split |
| `cli.py` | The `crm-study` commands |

## References

1. T. Wu, M. Terry, and C. J. Cai. [AI Chains: Transparent and controllable human-AI interaction by chaining large language model prompts](https://doi.org/10.1145/3491102.3517582). CHI 2022.
2. T. Khot et al. [Decomposed prompting: A modular approach for solving complex tasks](https://arxiv.org/abs/2210.02406). ICLR 2023.
3. I. P. Fellegi and A. B. Sunter. [A theory for record linkage](https://doi.org/10.1080/01621459.1969.10501049). Journal of the American Statistical Association, 64(328), 1969.
4. V. Christophides et al. [An overview of end-to-end entity resolution for big data](https://doi.org/10.1145/3418896). ACM Computing Surveys, 53(6), 2020.
5. J. Thorne et al. [FEVER: A large-scale dataset for fact extraction and verification](https://aclanthology.org/N18-1074/). NAACL 2018.
6. S. Dhuliawala et al. [Chain-of-verification reduces hallucination in large language models](https://aclanthology.org/2024.findings-acl.212/). Findings of ACL 2024.
7. H. Rashkin et al. [Measuring attribution in natural language generation models](https://aclanthology.org/2023.cl-4.2/). Computational Linguistics, 49(4), 2023.
8. T. Gao, H. Yen, J. Yu, and D. Chen. [Enabling large language models to generate text with citations](https://aclanthology.org/2023.emnlp-main.398/). EMNLP 2023.
9. B. Dhingra et al. [Time-aware language models as temporal knowledge bases](https://aclanthology.org/2022.tacl-1.15/). Transactions of the ACL, 10, 2022.
10. H.-T. Chen, M. Zhang, and E. Choi. [Rich knowledge sources bring complex knowledge conflicts](https://aclanthology.org/2022.emnlp-main.146/). EMNLP 2022.
11. C. K. Chow. [On optimum recognition error and reject tradeoff](https://doi.org/10.1109/TIT.1970.1054406). IEEE Transactions on Information Theory, 16(1), 1970.
12. Y. Geifman and R. El-Yaniv. [Selective classification for deep neural networks](https://arxiv.org/abs/1705.08500). NeurIPS 2017.
13. A. Yang et al. [Qwen3 technical report](https://arxiv.org/abs/2505.09388). arXiv:2505.09388, 2025.
14. A. Hannun, J. Digani, A. Katharopoulos, and R. Collobert. [MLX: Efficient and flexible machine learning on Apple silicon](https://github.com/ml-explore/mlx). Software, 2023.
15. E. B. Wilson. [Probable inference, the law of succession, and statistical inference](https://doi.org/10.1080/01621459.1927.10502953). Journal of the American Statistical Association, 22(158), 1927.
16. Q. McNemar. [Note on the sampling error of the difference between correlated proportions or percentages](https://doi.org/10.1007/BF02295996). Psychometrika, 12(2), 1947.
17. S. Kapoor et al. [AI agents that matter](https://arxiv.org/abs/2407.01502). arXiv:2407.01502, 2024.
