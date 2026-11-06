"""Behavioral checks for identity, admission, isolation, scoring, and workflow wiring."""

import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from crm_study.backends import Call, ReplayBackend
from crm_study.cli import main
from crm_study.data import validate_dataset
from crm_study.evaluation import evaluate, score_one, summarize, validate_results
from crm_study.pipeline import run_case
from crm_study.policy import apply_update, decide
from crm_study.prompts import direct_messages, extraction_messages
from crm_study.resolution import resolve
from crm_study.schema import Candidate, parse_json_response, read_jsonl

ROOT = Path(__file__).resolve().parents[1]
CASES = {c["id"]: c for c in read_jsonl(ROOT / "data/processed/cases.jsonl")}
LABELS = {g["case_id"]: g for g in read_jsonl(ROOT / "data/labels/answers.jsonl")}
SUPPORTED = {"support": "supported", "date_supported": True, "conflicting_sources": False}


def components(case_id):
    case = deepcopy(CASES[case_id])
    candidate = Candidate.from_dict(LABELS[case_id]["candidates"][0])
    return case, candidate, resolve(candidate, case["crm"])


@pytest.mark.parametrize(
    "case_id,status,record",
    [
        ("scenario-02-1", "matched", "person-1"),
        ("scenario-03-1", "ambiguous", None),
        ("scenario-04-1", "matched", "person-1"),
        ("scenario-10-1", "ambiguous", None),
        ("scenario-11-1", "new", None),
    ],
)
def test_resolution_uses_identity_context_and_preserves_ambiguity(case_id, status, record):
    _, _, resolution = components(case_id)
    assert (resolution["status"], resolution["entity_id"]) == (status, record)


@pytest.mark.parametrize(
    "case_id,decision,reason",
    [
        ("scenario-01-1", "accept", "supported_update"),
        ("scenario-03-1", "review", "ambiguous_identity"),
        ("scenario-05-1", "reject", "stale_update"),
        ("scenario-07-1", "reject", "source_not_allowed"),
        ("scenario-12-1", "review", "future_update"),
        ("scenario-13-1", "review", "undated_conflict"),
        ("scenario-15-1", "review", "same_date_conflict"),
    ],
)
def test_update_policy(case_id, decision, reason):
    case, candidate, resolution = components(case_id)
    answer = decide(case, candidate, resolution, SUPPORTED)
    assert (answer["decision"], answer["reason"]) == (decision, reason)


def test_quote_membership_is_not_semantic_support():
    case, candidate, resolution = components("scenario-09-1")
    result = decide(case, candidate, resolution, {**SUPPORTED, "support": "contradicted"})
    assert result["checks"]["quote_matches"] is True
    assert result["decision"] == "reject"
    candidate.evidence = "A quotation the source never contained"
    assert decide(case, candidate, resolution, SUPPORTED)["reason"] == "evidence_not_in_source"


def test_conflicts_and_uncertainty_do_not_silently_update_crm():
    case, candidate, resolution = components("scenario-06-1")
    assert (
        decide(case, candidate, resolution, {**SUPPORTED, "conflicting_sources": True})["decision"]
        == "review"
    )
    uncertain = decide(case, candidate, resolution, {**SUPPORTED, "support": "uncertain"})
    assert (uncertain["decision"], uncertain["reason"]) == ("review", "support_uncertain")


def test_conflicting_allowed_sources_are_reviewed_even_if_verifier_calls_it_contradicted():
    case, candidate, resolution = components("scenario-06-1")
    result = decide(
        case,
        candidate,
        resolution,
        {**SUPPORTED, "support": "contradicted", "conflicting_sources": True},
    )
    assert result["decision"] == "review"


def test_invented_full_name_cannot_resolve_a_first_name_only_source():
    case, candidate, _ = components("scenario-03-1")
    candidate.subject = "Avery Brooks"
    resolution = resolve(candidate, case["crm"])
    result = decide(case, candidate, resolution, SUPPORTED)
    assert result["decision"] == "review"
    assert result["reason"] == "subject_not_in_source"


def test_simulated_writes_are_isolated_and_keep_evidence():
    case, candidate, resolution = components("scenario-01-1")
    original = deepcopy(case)
    decision = decide(case, candidate, resolution, SUPPORTED)
    prediction = {"candidate": candidate.to_dict(), "resolution": resolution, **decision}
    changed = apply_update(case, prediction)
    assert case == original
    assert changed["applied"]
    assert changed["crm"][1]["facts"]["role"]["evidence"] == candidate.evidence
    prediction["decision"] = "review"
    assert apply_update(case, prediction)["crm"] == original["crm"]


def test_same_value_does_not_allow_older_or_undated_evidence_to_replace_newer_fact():
    case, candidate, resolution = components("scenario-05-1")
    record = next(r for r in case["crm"] if r["id"] == resolution["entity_id"])
    record["facts"]["role"]["value"] = "chief technology officer"
    original = deepcopy(case["crm"])
    assert decide(case, candidate, resolution, SUPPORTED)["reason"] == "stale_update"
    candidate.effective_date = None
    decision = decide(case, candidate, resolution, SUPPORTED)
    assert (decision["decision"], decision["reason"]) == ("review", "undated_update")
    result = apply_update(
        case, {"candidate": candidate.to_dict(), "resolution": resolution, **decision}
    )
    assert result["crm"] == original
    candidate.effective_date = record["facts"]["role"]["effective_date"]
    assert decide(case, candidate, resolution, SUPPORTED)["decision"] == "accept"


def test_wrong_record_type_cannot_receive_an_accepted_fact():
    case, candidate, _ = components("scenario-01-1")
    original = deepcopy(case["crm"])
    response = {
        "candidate": candidate.to_dict(),
        "resolution": {"status": "matched", "entity_id": "org-1"},
        "decision": "accept",
    }
    result = run_case(case, "direct", ScriptedBackend([response]))
    written = result["stages"][-1]["output"]
    assert written["crm"] == original and not written["applied"]
    assert written["error"] == "record_type_mismatch"
    assert not score_one(result, case, LABELS[case["id"]])["correct_write"]


def test_dataset_labels_and_inputs_are_separate():
    assert validate_dataset(list(CASES.values()), list(LABELS.values()))["cases"] == 132
    broken = deepcopy(CASES["scenario-01-1"])
    del broken["crm"][0]["aliases"]
    with pytest.raises(ValueError, match="required field"):
        validate_dataset([broken], [LABELS["scenario-01-1"]])
    case = {**CASES["scenario-01-1"], "answer": "DO_NOT_LEAK", "category": "DO_NOT_LEAK"}
    for prompt in (direct_messages(case), extraction_messages(case)):
        assert "DO_NOT_LEAK" not in json.dumps(prompt)
        assert "rationale" not in json.dumps(prompt)
    assert "crm" not in json.loads(extraction_messages(case)[-1]["content"])


def test_current_role_update_needs_organization_context():
    case, candidate, resolution = components("scenario-01-1")
    candidate.organization = None
    assert decide(case, candidate, resolution, SUPPORTED)["reason"] == "missing_organization"


def test_malformed_dates_and_output_are_visible_errors():
    data = deepcopy(LABELS["scenario-01-1"]["candidates"][0])
    data["effective_date"] = "2026-09"
    with pytest.raises(ValueError):
        Candidate.from_dict(data)
    with pytest.raises(ValueError):
        parse_json_response('An explanation first. {"candidate": null}')
    assert parse_json_response('```json\n{"candidate": null}\n```') == {"candidate": None}


def test_benign_extra_model_field_does_not_discard_a_valid_candidate():
    data = deepcopy(LABELS["scenario-01-1"]["candidates"][0])
    data["role"] = data["value"]
    assert Candidate.from_dict(data).value == data["value"]


@pytest.mark.parametrize("invalid", ["attribute", "resolution"])
def test_structurally_incompatible_model_output_is_a_visible_error(invalid):
    case, candidate, resolution = components("scenario-01-1")
    data = candidate.to_dict()
    if invalid == "attribute":
        data["entity_type"] = "company"
    else:
        resolution["entity_id"] = None
    result = run_case(
        case,
        "direct",
        ScriptedBackend([{"candidate": data, "resolution": resolution, "decision": "accept"}]),
    )
    assert result["error"]
    assert not result["stages"][-1]["output"]["applied"]


class ScriptedBackend:
    """Unit-test responses only; this backend is not available to the experiment CLI."""

    settings = {"backend": "unit_test"}

    def __init__(self, replies):
        self.replies = iter(replies)

    def complete(self, messages):
        return Call(json.dumps(next(self.replies)), 1, 1, 0.01, "stop")


def test_staged_workflow_records_resolution_verification_and_write():
    case, candidate, _ = components("scenario-01-1")
    result = run_case(
        case, "staged", ScriptedBackend([{"candidate": candidate.to_dict()}, SUPPORTED])
    )
    assert result["error"] is None
    assert result["prediction"]["decision"] == "accept"
    assert [s["stage"] for s in result["stages"]] == [
        "extraction",
        "resolution",
        "verification",
        "decision",
        "crm_update",
    ]
    assert len(result["calls"]) == 2


def test_saved_responses_replay_without_model_inference():
    case, candidate, _ = components("scenario-01-1")
    original = run_case(
        case, "staged", ScriptedBackend([{"candidate": candidate.to_dict()}, SUPPORTED])
    )
    replayed = run_case(case, "staged", ReplayBackend(original))
    assert replayed["prediction"] == original["prediction"]
    assert replayed["stages"] == original["stages"]
    assert replayed["model_settings"]["backend"] == "replay"
    assert replayed["input_tokens"] == replayed["output_tokens"] == 0


def test_metrics_require_correct_identity_and_do_not_reward_rejecting_everything():
    case, candidate, _ = components("scenario-01-1")
    result = run_case(
        case, "staged", ScriptedBackend([{"candidate": candidate.to_dict()}, SUPPORTED])
    )
    correct = score_one(result, case, LABELS[case["id"]])
    assert correct["correct_accept"]
    result["prediction"]["resolution"]["entity_id"] = "wrong-person"
    wrong = score_one(result, case, LABELS[case["id"]])
    assert wrong["accepted"] and not wrong["correct_accept"]
    result["prediction"]["decision"] = "reject"
    rejected = score_one(result, case, LABELS[case["id"]])
    summary = summarize([rejected])
    assert summary["useful_update_coverage"]["rate"] == 0
    assert summary["accepted_update_accuracy"]["rate"] is None


def test_scoring_inspects_the_written_fact_rather_than_trusting_the_applied_flag():
    case, candidate, _ = components("scenario-01-1")
    result = run_case(
        case, "staged", ScriptedBackend([{"candidate": candidate.to_dict()}, SUPPORTED])
    )
    update = result["stages"][-1]["output"]
    target = next(r for r in update["crm"] if r["id"] == update["record_id"])
    target["facts"]["role"]["value"] = "An incorrect persisted value"
    row = score_one(result, case, LABELS[case["id"]])
    assert row["candidate_correct"] and update["applied"]
    assert not row["correct_write"] and not row["correct_accept"]


def test_nonpersisted_metadata_is_separate_from_correctness_of_an_existing_record_write():
    case, candidate, resolution = components("scenario-01-1")
    candidate.organization = "Incorrect extra metadata"
    result = run_case(
        case,
        "direct",
        ScriptedBackend(
            [{"candidate": candidate.to_dict(), "resolution": resolution, "decision": "accept"}]
        ),
    )
    row = score_one(result, case, LABELS[case["id"]])
    assert row["correct_write"] and not row["candidate_correct"] and not row["correct_accept"]
    summary = summarize([row])
    assert summary["accepted_update_accuracy"]["rate"] == 1
    assert summary["accepted_candidate_accuracy"]["rate"] == 0


def test_failed_response_does_not_count_as_appropriate_review():
    case, _, _ = components("scenario-03-1")
    result = run_case(case, "staged", ScriptedBackend([{"wrong_key": 1}]))
    scored = score_one(result, case, LABELS[case["id"]])
    assert result["error"]
    assert scored["decision"] == "review" and not scored["decision_correct"]
    assert "decision" in scored["failures"]
    assert summarize([scored])["unsafe_case_withholding"]["rate"] == 0
    assert summarize([scored])["decision_confusion"] == {"review -> pipeline_error": 1}


def test_repeats_do_not_inflate_main_sample_size():
    case, candidate, _ = components("scenario-01-1")
    first = run_case(
        case, "staged", ScriptedBackend([{"candidate": candidate.to_dict()}, SUPPORTED])
    )
    first["repeat"] = 0
    second = {**deepcopy(first), "repeat": 1}
    summary, _ = evaluate([first, second], [case], [LABELS[case["id"]]])
    assert summary["overall"]["staged"]["cases"] == 1
    assert summary["consistency"]["staged"]["rate"] == 1


def test_scoring_rejects_duplicates_mixed_workflows_and_incomplete_schedules():
    case, candidate, _ = components("scenario-01-1")
    result = run_case(
        case, "staged", ScriptedBackend([{"candidate": candidate.to_dict()}, SUPPORTED])
    )
    with pytest.raises(ValueError, match="Duplicate"):
        evaluate([result, result], [case], [LABELS[case["id"]]])
    other = {**deepcopy(result), "repeat": 1, "workflow_version": "other"}
    with pytest.raises(ValueError, match="mix"):
        evaluate([result, other], [case], [LABELS[case["id"]]])
    schedule = {"case_ids": [case["id"]], "strategies": ["direct", "staged"], "repeats": 1}
    with pytest.raises(ValueError, match="schedule"):
        validate_results([], schedule)


def test_resume_checks_input_snapshot_and_skips_model_loading_for_completed_run(
    tmp_path, monkeypatch
):
    case, candidate, resolution = components("scenario-01-1")
    inputs, output = tmp_path / "inputs.jsonl", tmp_path / "run"
    inputs.write_text(json.dumps(case) + "\n")
    backend = ScriptedBackend(
        [{"candidate": candidate.to_dict(), "resolution": resolution, "decision": "accept"}]
    )
    backend.settings = {
        "backend": "mlx",
        "model": "test-model",
        "max_tokens": 512,
        "temperature": 0.0,
    }
    monkeypatch.setattr("crm_study.cli.MLXBackend", lambda *args: backend)
    argv = [
        "crm-study",
        "run",
        "--cases",
        str(inputs),
        "--out",
        str(output),
        "--model",
        "test-model",
        "--strategy",
        "direct",
    ]
    monkeypatch.setattr(sys, "argv", argv)
    main()
    assert read_jsonl(output / "cases.jsonl") == [case]

    def unexpected_load(*args):
        pytest.fail("Completed or incompatible runs must not load a model")

    monkeypatch.setattr("crm_study.cli.MLXBackend", unexpected_load)
    monkeypatch.setattr(sys, "argv", [*argv, "--resume"])
    main()
    case["sources"][0]["text"] += " Changed input."
    inputs.write_text(json.dumps(case) + "\n")
    with pytest.raises(SystemExit):
        main()


@pytest.mark.parametrize("strategy", ["direct", "staged"])
def test_network_failure_is_recorded_without_aborting_the_experiment(strategy):
    case, candidate, _ = components("scenario-01-1")

    class UnavailableBackend:
        settings = {"backend": "unit_test"}
        calls = 0

        def complete(self, messages):
            self.calls += 1
            if strategy == "staged" and self.calls == 1:
                return Call(json.dumps({"candidate": candidate.to_dict()}), 10, 10, 0.01, "stop")
            raise OSError("Endpoint unavailable")

    result = run_case(case, strategy, UnavailableBackend())
    assert result["error"] == "OSError: Endpoint unavailable"
    assert len(result["calls"]) == (1 if strategy == "direct" else 2)
    assert result["calls"][-1]["messages"]
    assert result["calls"][-1]["error"] == result["error"]
    assert result["input_tokens"] is None and result["output_tokens"] is None
    assert not result["stages"][-1]["output"]["applied"]
    replay = ReplayBackend(result)
    replayed = run_case(case, strategy, replay)
    assert replay.position == len(result["calls"])
    assert replayed["error"] == result["error"]
    assert replayed["prediction"] == result["prediction"]
    assert replayed["stages"][-1] == result["stages"][-1]
