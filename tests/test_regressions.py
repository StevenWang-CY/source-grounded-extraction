"""Confirmed staged failures from the saved runs, as regression tests.

Each test feeds the saved model responses of one failure through the Python stages again.
Workflow 3 reproduces the failure, and workflow 4 is expected to fix it. A saved verifier
response is reused even though the candidate it now checks may differ.
"""

from pathlib import Path

import pytest

from crm_study.backends import Call
from crm_study.evaluation import score_one
from crm_study.pipeline import run_case
from crm_study.schema import date_stated, read_jsonl

ROOT = Path(__file__).resolve().parents[1]
CASES = {c["id"]: c for c in read_jsonl(ROOT / "data/processed/cases.jsonl")}
LABELS = {g["case_id"]: g for g in read_jsonl(ROOT / "data/labels/answers.jsonl")}
SUPPORTED = '{"support": "supported", "date_supported": true, "conflicting_sources": false}'

# (run, case, what went wrong in the saved run)
WRONG_OR_MISSING_DATE = [
    ("test", "fewrel-p39-0025", "1972 became 1972-01-01"),
    ("development", "fewrel-p127-0072", "August 2015 became 2015-08-01"),
    ("test", "scenario-14-4", "publication date copied as the effective date"),
    ("development", "scenario-14-1", "publication date copied as the effective date"),
    ("test", "fewrel-p127-0037", "month-only date made the response invalid"),
]
ORGANIZATION = [
    ("test", "fewrel-p39-0035", 'organization "null" blocked the match'),
    ("test", "fewrel-p39-0040", "unknown CRM organization treated as a conflict"),
    ("test", "fewrel-p39-0022", "unknown CRM organization treated as a conflict"),
]
# Fixing the date lets these two runs continue, and each then fails for another reason.
STILL_OPEN = [
    ("test", "fewrel-p127-0114", 'owner written as "private equity group Bridgepoint Capital"'),
    ("test", "fewrel-p127-0103", "quotation shortened with an ellipsis"),
]
LONGER_NAME = [("test", "fewrel-p159-0041"), ("development", "fewrel-p159-0303")]


class SavedResponses:
    """Saved model texts in order. A run that stopped early continues with a supported check."""

    settings = {"backend": "unit_test"}

    def __init__(self, run, case_id):
        row = next(
            r
            for r in read_jsonl(ROOT / "results" / run / "predictions.jsonl")
            if r["case_id"] == case_id and r["strategy"] == "staged" and r["repeat"] == 0
        )
        self.texts = [c["text"] for c in row["calls"]]

    def complete(self, messages):
        text = self.texts.pop(0) if self.texts else SUPPORTED
        return Call(text, 1, 1, 0.01, "stop")


def writes_expected_fact(run, case_id, workflow):
    case, gold = CASES[case_id], LABELS[case_id]
    assert gold["decision"] == "accept"
    result = run_case(case, "staged", SavedResponses(run, case_id), workflow)
    return score_one({**result, "repeat": 0}, case, gold)["correct_write"]


@pytest.mark.parametrize("run,case_id,failure", WRONG_OR_MISSING_DATE + ORGANIZATION)
def test_fixed_failure_now_writes_the_expected_fact(run, case_id, failure):
    assert not writes_expected_fact(run, case_id, "3"), failure
    assert writes_expected_fact(run, case_id, "4"), failure


@pytest.mark.parametrize("run,case_id,failure", STILL_OPEN)
def test_open_failure_is_still_a_failure(run, case_id, failure):
    assert not writes_expected_fact(run, case_id, "3"), failure
    assert not writes_expected_fact(run, case_id, "4"), failure


@pytest.mark.parametrize("run,case_id", LONGER_NAME)
def test_longer_form_of_an_existing_name_is_reviewed_not_duplicated(run, case_id):
    # "Yingke Law Firm" and "UAL Corporation" were written as new duplicate records.
    before = run_case(CASES[case_id], "staged", SavedResponses(run, case_id), "3")
    assert before["prediction"]["resolution"]["status"] == "new"
    assert before["stages"][-1]["output"]["applied"]
    after = run_case(CASES[case_id], "staged", SavedResponses(run, case_id), "4")
    assert after["prediction"]["resolution"]["status"] == "ambiguous"
    assert after["prediction"]["decision"] == "review"
    assert not after["stages"][-1]["output"]["applied"]


def test_only_a_fully_written_date_counts_as_stated():
    assert date_stated("2026-09-13", "From September 13, 2026, our CTO is Frederick Kovacs.")
    assert date_stated("2026-09-13", "took up the post on 13 Sept. 2026")
    assert not date_stated("2026-09-01", "the appointment takes effect in September 2026")
    assert not date_stated("2026-09-01", "From September 13, 2026")
    assert not date_stated("1972-01-01", "When Jack Marshall became Prime Minister in 1972")
