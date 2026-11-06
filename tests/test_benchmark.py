"""Benchmark split, experiment scheduling, scoring snapshots, and regression contracts."""

import json
import sys
from copy import deepcopy
from io import BytesIO
from pathlib import Path

import pytest

from crm_study.backends import Call, HTTPBackend
from crm_study.cli import main, read_checkpoint
from crm_study.data import audit_split, grouped_split
from crm_study.evaluation import SCORING_VERSION, evaluate, execution_schedule, score_one
from crm_study.pipeline import run_case
from crm_study.policy import apply_update, decide
from crm_study.resolution import resolve
from crm_study.schema import Candidate, read_jsonl
from crm_study.stats import exact_mcnemar, paired_difference_interval, wilson_interval
from crm_study.variants import candidate_only, from_answer_key, without_verifier

ROOT = Path(__file__).resolve().parents[1]
CASES = read_jsonl(ROOT / "data/processed/cases.jsonl")
LABELS = {g["case_id"]: g for g in read_jsonl(ROOT / "data/labels/answers.jsonl")}


def test_benchmark_is_balanced_and_its_splits_are_disjoint():
    report = audit_split(CASES, list(LABELS.values()))
    assert report["cases"] == 132
    for split in report["splits"].values():
        assert split["cases"] == 66
        assert split["decisions"] == {"accept": 38, "review": 17, "reject": 11}
        assert split["origins"] == {"fewrel_adapted": 30, "synthetic": 36}


@pytest.mark.parametrize("kind", ["template", "identity", "source"])
def test_split_audit_rejects_leakage_even_with_different_case_ids(kind):
    cases = deepcopy(CASES)
    first = next(c for c in cases if c["split"] == "dev")
    second = next(c for c in cases if c["split"] == "test")
    if kind == "template":
        first["split_keys"].append("template:leaked")
        second["split_keys"].append("template:leaked")
    elif kind == "identity":
        second["crm"][0]["aliases"].append(first["crm"][0]["name"])
    else:
        second["sources"][0]["text"] = first["sources"][0]["text"]
    with pytest.raises(ValueError):
        audit_split(cases, list(LABELS.values()))


def test_group_assignment_keeps_transitively_connected_entities_together():
    cases = [
        {"id": str(i), "split_keys": keys, "provenance": {"relation": "ownership"}}
        for i, keys in enumerate([["a"], ["a", "b"], ["b"], ["c"], ["d"], ["e"]])
    ]
    split = grouped_split(cases)
    assert split["0"] == split["1"] == split["2"]
    assert set(split.values()) == {"dev", "test"}
    assert grouped_split(list(reversed(cases))) == split


def test_authored_stage_labels_agree_with_policy_and_simulated_writes():
    # This checks the deterministic contract, not model performance or independent annotation quality.
    for case in CASES:
        gold = LABELS[case["id"]]
        for expected in gold["candidates"] or [None]:
            candidate = Candidate.from_dict(expected) if expected else None
            resolution = (
                resolve(candidate, case["crm"])
                if candidate
                else {"status": "ambiguous", "entity_id": None}
            )
            assert {k: resolution[k] for k in ("status", "entity_id")} == gold["resolution"], case[
                "id"
            ]
            decision = decide(case, candidate, resolution, gold["verification"])
            assert decision["decision"] == gold["decision"], case["id"]
            prediction = {"candidate": expected, "resolution": resolution, **decision}
            result = apply_update(case, prediction)
            assert result["applied"] == (gold["decision"] == "accept"), case["id"]
            if gold["decision"] != "accept":
                assert result["crm"] == case["crm"]


def test_ambiguous_company_alias_cannot_select_the_first_company():
    case = deepcopy(next(c for c in CASES if c["id"] == "scenario-01-1"))
    candidate = Candidate.from_dict(LABELS[case["id"]]["candidates"][0])
    case["crm"][0]["aliases"] = ["Shared"]
    case["crm"].append(
        {
            "id": "org-2",
            "entity_type": "company",
            "name": "Different company",
            "aliases": ["Shared"],
        }
    )
    candidate.organization = "Shared"
    assert resolve(candidate, case["crm"])["status"] == "ambiguous"


def test_repeat_subset_counts_fresh_executions_without_inflating_primary_sample():
    config = {
        "case_ids": ["a", "b"],
        "repeat_case_ids": ["b"],
        "strategies": ["direct", "staged"],
        "repeats": 3,
    }
    schedule = execution_schedule(config)
    assert len(schedule) == 8
    assert ("a", "direct", 0) in schedule and ("a", "direct", 1) not in schedule
    assert ("b", "staged", 2) in schedule


class FixedBackend:
    settings = {"backend": "mlx", "model": "test-model", "max_tokens": 512, "temperature": 0.0}

    def __init__(self, response):
        self.response = response

    def complete(self, messages):
        return Call(json.dumps(self.response), 5, 5, 0.01, "stop")


def test_scoring_freezes_selected_labels_and_rejects_later_answer_changes(tmp_path, monkeypatch):
    case = next(c for c in CASES if c["id"] == "scenario-01-1")
    gold = LABELS[case["id"]]
    backend = FixedBackend(
        {"candidate": gold["candidates"][0], "resolution": gold["resolution"], "decision": "accept"}
    )
    monkeypatch.setattr("crm_study.cli.MLXBackend", lambda *args: backend)
    inputs, answers, output = tmp_path / "cases.jsonl", tmp_path / "answers.jsonl", tmp_path / "run"
    inputs.write_text(json.dumps(case) + "\n")
    answers.write_text(json.dumps(gold) + "\n")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "crm-study",
            "run",
            "--cases",
            str(inputs),
            "--out",
            str(output),
            "--strategy",
            "direct",
            "--model",
            "test-model",
        ],
    )
    main()
    assert not (output / "answers.jsonl").exists()
    argv = ["crm-study", "score", str(output), "--labels", str(answers)]
    monkeypatch.setattr(sys, "argv", argv)
    main()
    assert read_jsonl(output / "answers.jsonl") == [gold]
    answers.write_text(json.dumps({**gold, "decision": "reject"}) + "\n")
    with pytest.raises(SystemExit):
        main()
    reviewed = output / "reviewed"
    monkeypatch.setattr(sys, "argv", [*argv, "--analysis-out", str(reviewed)])
    main()
    assert read_jsonl(output / "answers.jsonl") == [gold]
    assert read_jsonl(reviewed / "answers.jsonl")[0]["decision"] == "reject"
    assert not (reviewed / "predictions.jsonl").exists()
    analysis = json.loads((reviewed / "analysis.json").read_text())
    assert analysis["source_run"] == ".." and analysis["scoring_version"] == SCORING_VERSION
    (reviewed / "analysis.json").write_text(json.dumps({**analysis, "source_run": "another-run"}))
    with pytest.raises(SystemExit):
        main()  # An analysis directory is never reused for another run.


def test_missing_http_token_usage_remains_unknown(monkeypatch):
    response = {"choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}]}
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda *args, **kwargs: BytesIO(json.dumps(response).encode())
    )
    call = HTTPBackend("test", "http://localhost").complete([])
    assert call.input_tokens is None and call.output_tokens is None


def test_resume_drops_a_cut_off_last_line_but_not_a_corrupted_record(tmp_path):
    path = tmp_path / "predictions.jsonl"
    path.write_bytes(b'{"case_id":"done"}\n{"text":"\xc3')
    assert read_checkpoint(path) == [{"case_id": "done"}]
    assert path.read_text() == '{"case_id":"done"}\n'
    path.write_text('{"case_id":"done"}\nnot json\n')
    with pytest.raises(json.JSONDecodeError):
        read_checkpoint(path)


def test_paired_metrics_count_case_matches_and_exclude_repeats():
    case = next(c for c in CASES if c["id"] == "scenario-01-1")
    gold = LABELS[case["id"]]
    correct = {
        "candidate": gold["candidates"][0],
        "resolution": gold["resolution"],
        "decision": "accept",
    }
    direct = run_case(case, "direct", FixedBackend(correct))
    # Use an explicit synthetic prediction fixture for the scorer, not a claimed model run.
    staged = deepcopy(direct)
    staged["strategy"] = "staged"
    staged["prediction"]["decision"] = "reject"
    staged["stages"][-1]["output"] = apply_update(case, staged["prediction"])
    repeated = {**deepcopy(direct), "repeat": 1}
    summary, _ = evaluate([direct, staged, repeated], [case], [gold])
    assert summary["overall"]["direct"]["cases"] == 1
    assert summary["paired_comparison"]["correct_write_on_useful_cases"]["direct_only"] == 1
    assert summary["consistency"]["direct"]["denominator"] == 1
    assert score_one(direct, case, gold)["correct_write"]


def test_later_error_preserves_valid_extraction_diagnostics_without_crediting_a_write():
    case = next(c for c in CASES if c["id"] == "scenario-01-1")
    gold = LABELS[case["id"]]
    malformed_resolution = {
        "candidate": gold["candidates"][0],
        "resolution": {"status": "new", "entity_id": "person-1"},
        "decision": "accept",
    }
    result = run_case(case, "direct", FixedBackend(malformed_resolution))
    row = score_one(result, case, gold)
    assert row["candidate_correct"] and row["extraction_valid"]
    assert not row["resolution_correct"] and not row["decision_correct"]
    assert not row["correct_write"] and not row["pipeline_ok"]
    assert "extraction" not in row["failures"]
    assert "response_error" in row["failures"]


def test_incorrect_verifier_flag_is_visible_even_when_the_decision_is_correct(monkeypatch):
    case = next(c for c in CASES if c["id"] == "scenario-08-1")
    gold = LABELS[case["id"]]
    replies = iter(
        [
            {"candidate": gold["candidates"][0]},
            {**gold["verification"], "date_supported": False},
        ]
    )
    backend = FixedBackend(None)
    monkeypatch.setattr(
        backend, "complete", lambda _: Call(json.dumps(next(replies)), 5, 5, 0.01, "stop")
    )
    result = run_case(case, "staged", backend)
    row = score_one(result, case, gold)
    assert row["decision_correct"] and row["candidate_correct"]
    assert row["verification_correct"] is False
    assert row["failures"] == ["verification"]


def test_wilson_interval_and_exact_mcnemar_match_known_values():
    assert wilson_interval(0, 10) == pytest.approx((0.0, 0.2775), abs=1e-4)
    assert wilson_interval(10, 10) == pytest.approx((0.7225, 1.0), abs=1e-4)
    assert wilson_interval(29, 57) == pytest.approx((0.3826, 0.6338), abs=1e-3)
    assert exact_mcnemar(6, 25) == pytest.approx(0.00088, abs=1e-5)
    assert exact_mcnemar(8, 5) == pytest.approx(0.5811, abs=1e-4)
    assert exact_mcnemar(0, 0) == 1
    assert paired_difference_interval(8, 5, 38) == pytest.approx((-4.0, 10.0), abs=0.1)


def test_python_steps_given_every_answer_reach_the_expected_decision():
    dev = [c for c in CASES if c["split"] == "dev"]
    for case in dev:
        result = from_answer_key(case, LABELS[case["id"]])
        assert result["prediction"]["decision"] == LABELS[case["id"]]["decision"], case["id"]
        assert score_one({**result, "repeat": 0}, case, LABELS[case["id"]])["decision_correct"]


def test_variant_keeps_only_the_candidate_of_a_direct_response():
    case = next(c for c in CASES if c["id"] == "scenario-05-2")
    gold = LABELS[case["id"]]
    response = json.dumps(
        {
            "candidate": gold["candidates"][0],
            "resolution": {"status": "new", "entity_id": "person-1"},
            "decision": "accept",
        }
    )
    # The model's impossible match and its acceptance are both dropped: the rules reject this stale fact.
    result = without_verifier(case, candidate_only(response))
    assert result["error"] is None and result["prediction"]["reason"] == "stale_update"
    assert without_verifier(case, candidate_only("not json"))["error"]
