# FewRel source files

These files come from [THUNLP FewRel](https://github.com/thunlp/FewRel/tree/master/data), the
dataset of [Han et al., EMNLP 2018](https://aclanthology.org/D18-1514/).

| File | Contents |
| --- | --- |
| `selected.json` | The 60 selected records from `train_wiki.json`, with original tokens, spans, and row indices |
| `LICENSE` | The upstream MIT license |

The selection and the accepted answer forms are in
[`data/curation/fewrel_selection.json`](../../curation/fewrel_selection.json).
`scripts/collect_fewrel.py` downloads `train_wiki.json` and extracts the same records again.
