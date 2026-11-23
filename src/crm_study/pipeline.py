"""Run the direct or staged workflow on one case and keep each intermediate result."""

import time

from .backends import Call
from .policy import apply_update, contract_check, decide
from .prompts import (
    PROMPT_VERSION,
    direct_messages,
    extraction_messages,
    guided_messages,
    verification_messages,
)
from .resolution import ambiguous, resolve
from .schema import DECISIONS, Candidate, parse_json_response, validate_resolution

# Workflow 3 is the staged workflow as it ran in the held-out test. Workflow 4 adds the four
# fixes made after reading the test errors. Saved runs record which one they used.
WORKFLOW_VERSIONS = ("3", "4")
WORKFLOW_VERSION = "4"
# Direct and guided are one-call workflows. Guided adds explicit checks and worked examples.
STRATEGIES = ("direct", "guided", "staged")
# A failed call or an invalid response raises one of these; the case is then a pipeline error.
RESPONSE_ERRORS = (ValueError, TypeError, LookupError, RuntimeError, OSError)


class RecordedCallError(RuntimeError):
    """A failed model call whose message already names the original error type."""


def run_direct(case: dict, ask, guided: bool = False) -> dict:
    """One model response supplies the candidate, the CRM match, and the decision."""
    prediction = ask("direct", guided_messages(case) if guided else direct_messages(case))
    candidate = prediction["candidate"]
    candidate = Candidate.from_dict(candidate) if candidate is not None else None
    validate_resolution(prediction["resolution"])
    if prediction["decision"] not in DECISIONS:
        raise ValueError("Invalid decision")
    prediction["candidate"] = candidate.to_dict() if candidate else None
    return prediction


def run_staged(case: dict, ask, stages: list[dict], fixes: bool) -> dict:
    """Model extraction, Python matching, model verification, then Python decision rules."""
    extracted = ask("extraction", extraction_messages(case))
    data = extracted["candidate"]
    if fixes:
        data, changes = contract_check(case, data)
        if changes:
            stages.append({"stage": "contract_check", "output": changes})
    candidate = Candidate.from_dict(data) if data is not None else None
    resolution = resolve(candidate, case["crm"], fixes) if candidate else ambiguous([])
    stages.append({"stage": "resolution", "output": resolution})
    semantic = None
    if candidate:
        semantic = ask("verification", verification_messages(case, candidate.to_dict(), resolution))
        if semantic["support"] not in {"supported", "uncertain", "contradicted"}:
            raise ValueError("Invalid support status")
        if not all(
            isinstance(semantic[k], bool) for k in ("date_supported", "conflicting_sources")
        ):
            raise ValueError("Verification checks must be booleans")
    decision = decide(case, candidate, resolution, semantic)
    stages.append({"stage": "decision", "output": decision})
    return {
        "candidate": candidate.to_dict() if candidate else None,
        "resolution": resolution,
        **decision,
    }


def total(calls: list[dict], key: str) -> int | None:
    values = [call[key] for call in calls]
    return None if None in values else sum(values)


def run_case(case: dict, strategy: str, backend, workflow_version: str = WORKFLOW_VERSION) -> dict:
    if strategy not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {strategy}")
    if workflow_version not in WORKFLOW_VERSIONS:
        raise ValueError(f"Unknown workflow version: {workflow_version}")
    start = time.perf_counter()
    stages, calls = [], []

    def ask(name, messages):
        call_start = time.perf_counter()
        try:
            call = backend.complete(messages)
        except RESPONSE_ERRORS as exc:
            error = f"{type(exc).__name__}: {exc}"
            call = Call("", None, None, time.perf_counter() - call_start, "error", error)
        calls.append({"stage": name, "messages": messages, **call.to_dict()})
        if call.error:
            raise RecordedCallError(call.error)
        result = parse_json_response(call.text)
        stages.append({"stage": name, "output": result})
        return result

    error = None
    try:
        if strategy != "staged":
            prediction = run_direct(case, ask, guided=strategy == "guided")
        else:
            prediction = run_staged(case, ask, stages, fixes=workflow_version == "4")
        simulation = apply_update(case, prediction)
    except RESPONSE_ERRORS as exc:
        # A failed response is recorded as an error, never scored as a successful review.
        error = str(exc) if isinstance(exc, RecordedCallError) else f"{type(exc).__name__}: {exc}"
        prediction = {
            "candidate": None,
            "resolution": {"status": "ambiguous", "entity_id": None},
            "decision": "review",
            "reason": "pipeline_error",
        }
        simulation = apply_update(case, prediction)
    stages.append({"stage": "crm_update", "output": simulation})
    return {
        "case_id": case["id"],
        "dataset_version": case.get("dataset_version", "1"),
        "strategy": strategy,
        "workflow_version": workflow_version,
        "prompt_version": PROMPT_VERSION,
        "prediction": prediction,
        "stages": stages,
        "calls": calls,
        "error": error,
        "input_tokens": total(calls, "input_tokens"),
        "output_tokens": total(calls, "output_tokens"),
        "latency_seconds": time.perf_counter() - start,
        "model_settings": backend.settings,
    }
