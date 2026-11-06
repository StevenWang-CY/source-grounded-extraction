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


def without_verifier(case: dict, extraction: str) -> dict:
    """Python matching and decision rules on a saved extraction, trusting its evidence."""
    return run_case(case, "staged", FixedResponses(extraction, json.dumps(TRUST_EVIDENCE)))


def from_answer_key(case: dict, answer: dict) -> dict:
    """The Python steps alone, given the answer key's candidate and evidence flags."""
    candidate = answer["candidates"][0] if answer["candidates"] else None
    responses = json.dumps({"candidate": candidate}), json.dumps(answer["verification"])
    return run_case(case, "staged", FixedResponses(*responses))
