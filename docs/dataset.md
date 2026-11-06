# Dataset

The dataset has **132 cases**, 60 based on FewRel passages and 72 synthetic. Each case asks
for one fact and comes with documents, a simulated CRM, and a separate answer key.

| Split | Public | Synthetic | Accept | Review | Reject | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Development | 30 | 36 | 38 | 17 | 11 | 66 |
| Test | 30 | 36 | 38 | 17 | 11 | 66 |

## Public passages

The source is [FewRel 1.0](https://github.com/thunlp/FewRel) (MIT license), described in
[Han et al., EMNLP 2018](https://aclanthology.org/D18-1514/). Its Wikipedia sentences were
aligned with [Wikidata](https://doi.org/10.1145/2629489) facts by
[distant supervision](https://aclanthology.org/P09-1113/) and then filtered by crowdworkers. I
use 20 passages each for position held (P39), owned by (P127), and headquarters location
(P159) from `train_wiki.json`.

A passage has to state the relationship explicitly for the requested subject. That rules out
ownership inferred from a CEO mention, unfinished acquisitions, and city mentions that do not
establish a headquarters. Cleaning only joins tokens and normalizes Unicode and punctuation
spacing. The original tokens, entity spans, and row indices are kept in
`data/raw/fewrel/selected.json`, next to the license.

Queries ask for the historical relationship stated in the passage. Unknown publication and
effective dates stay null. A headquarters answer can use the stated city or facility, with
optional region or country detail. The accepted forms are listed in
`data/curation/fewrel_selection.json`.

The CRM records and permission labels were built for this project. In each split and relation
group, eight passages have a unique CRM record, one has duplicate records, and one is marked as
not allowed for writing. Each uses a different passage.

[DocRED](https://aclanthology.org/P19-1074/) and
[CrossRE](https://aclanthology.org/2022.findings-emnlp.263/) were also options. FewRel's short
passages with entity spans fit the one-fact task, while DocRED's multi-sentence documents and
CrossRE's generic relation types would need more adaptation.

## Synthetic cases

Eighteen scenario families appear in four document forms, which gives 72 cases.

- Supported appointments, company aliases, ambiguous identities, and context matching.
- Stale facts, conflicting sources, denied or tentative claims, and disallowed sources.
- New and duplicate records, future appointments, undated or same-date conflicts, and corrections.
- Employer extraction, deal and company association, and irrelevant documents.

Announcements and staff records form the development split, and meeting minutes and
correspondence form the test split. Names, organizations, roles, and dates vary. The text, CRM
records, and answer keys were written for this project.

## The split

Public cases are grouped by target and owner identity and by source record, then assigned with
a fixed seed so the relations stay balanced. Synthetic identities and document forms stay within
one split. The dataset build fails if a passage or a target identity appears in both splits.
Shared cities and job titles are allowed. Development guides the design, and the test split is
kept for the final comparison.

## Answer key review

Reading the development outputs turned up three valid value forms that were missing from the
answer key. Revision 2 adds them, and the saved responses were scored again.

| Case | Added form | Reason |
| --- | --- | --- |
| `fewrel-p159-0026` | the town of Cognac, in the department of Charente, France | Full headquarters phrase in the source |
| `fewrel-p159-0252` | Midtown West in Tokyo Midtown, Akasaka, Minato, Tokyo | Full location phrase in the source |
| `fewrel-p39-0026` | former Attorney General | The source's title includes the qualifier |

The `former` rule applies wherever that exact title phrase occurs, in both splits. Inputs,
expected decisions, and model responses did not change.

| Measure | Direct, original | Direct, reviewed | Staged, original | Staged, reviewed |
| --- | ---: | ---: | ---: | ---: |
| Correct writes / accept decisions | 27/57 | 29/57 | 23/31 | 26/31 |
| Useful updates written | 27/38 | 29/38 | 23/38 | 26/38 |

The reports use the reviewed answers, which are in `results/development/reviewed/`. The original
answers and scores stay in `results/development/`.

## Files

| Path | Contents |
| --- | --- |
| `data/processed/cases.jsonl` | Model inputs and case details |
| `data/labels/answers.jsonl` | Expected facts, matches, decisions, and reasons |
| `data/curation/fewrel_selection.json` | The selected passages, exclusions, and accepted value forms |
| `data/raw/fewrel/` | The selected FewRel records and the license |

`scripts/build_dataset.py` builds the cases and answers from these files.
`scripts/collect_fewrel.py` downloads the upstream file and extracts the selected records again.
