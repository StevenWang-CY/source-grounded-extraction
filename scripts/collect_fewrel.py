"""Download the upstream FewRel file and extract the reviewed records into selected.json.

The dataset build reads selected.json offline; the selection itself is listed by hand in
data/curation/fewrel_selection.json.
"""

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    plan = json.loads((ROOT / "data/curation/fewrel_selection.json").read_text())
    raw = ROOT / "data/raw/fewrel"
    raw.mkdir(parents=True, exist_ok=True)
    download = raw / "train_wiki.json"
    if not download.exists():
        urllib.request.urlretrieve(plan["source_url"], download)
    corpus = json.loads(download.read_text())
    records = [
        {"relation": relation, "row_index": index, "record": corpus[relation][index]}
        for relation, indices in plan["selections"].items()
        for index in indices
    ]
    (raw / "selected.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n")
    if not (raw / "LICENSE").exists():
        urllib.request.urlretrieve(plan["license_url"], raw / "LICENSE")
    print(f"Retained {len(records)} reviewed records from {sum(map(len, corpus.values()))}.")


if __name__ == "__main__":
    main()
