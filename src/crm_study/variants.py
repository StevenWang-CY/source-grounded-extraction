"""Rerun the staged Python steps on saved responses with parts of the workflow removed."""

import json

from .backends import Call
from .pipeline import run_case
from .schema import parse_json_response

TRUST_EVIDENCE = {"support": "supported", "date_supported": True, "conflicting_sources": False}


class FixedResponses:
    """Answer the staged workflow's model calls from a fixed list of response texts."""

    settings = {"backend": "replay"}

    def __init__(self, *texts: str):
        self.texts = iter(texts)

    def complete(self, messages: list[dict]) -> Call:
        return Call(next(self.texts), 0, 0, 0.0, "replayed")


def candidate_only(direct_response: str) -> str:
    """Keep the candidate of a direct response, dropping the model's own match and decision."""
    try:
        return json.dumps({"candidate": parse_json_response(direct_response)["candidate"]})
    except (ValueError, KeyError):
        return direct_response  # An unreadable response stays an invalid response.


def lenient_match(case: dict, response: str, strategy: str = "direct") -> dict:
    """A one-call response again, reading any match that names a CRM record as that record.

    Larger models often return a status of new or ambiguous together with a record ID, which
    the workflow treats as invalid. This reading gives the one-call workflow the benefit of
    the doubt.
    """
    try:
        data = parse_json_response(response)
        resolution = data["resolution"]
        if resolution["entity_id"] in {record["id"] for record in case["crm"]}:
            resolution["status"] = "matched"
        response = json.dumps(data)
    except (ValueError, KeyError, TypeError):
        pass  # An unreadable response stays an invalid response.
    return run_case(case, strategy, FixedResponses(response))


def without_verifier(case: dict, extraction: str, workflow_version: str) -> dict:
    """Python matching and decision rules on a saved extraction, trusting its evidence."""
    responses = FixedResponses(extraction, json.dumps(TRUST_EVIDENCE))
    return run_case(case, "staged", responses, workflow_version)


def from_answer_key(case: dict, answer: dict, workflow_version: str) -> dict:
    """The Python steps alone, given the answer key's candidate and evidence flags."""
    candidate = answer["candidates"][0] if answer["candidates"] else None
    responses = json.dumps({"candidate": candidate}), json.dumps(answer["verification"])
    return run_case(case, "staged", FixedResponses(*responses), workflow_version)
