"""Resolve against this case's CRM, using names, aliases, and organization context."""

import re

from .schema import Candidate, normalize, record_names


def ambiguous(candidates: list[str]) -> dict:
    return {"status": "ambiguous", "entity_id": None, "candidates": candidates}


def name_words(name: str) -> set[str]:
    return set(re.findall(r"\w+", normalize(name)))


def related_name(subject: str, record: dict) -> bool:
    """Whether one name's words include the other's, as Yingke Law Firm includes Yingke.

    A subject without name words is related to every record, so it is never a new identity.
    """
    words = name_words(subject)
    return any(words <= other or other <= words for other in map(name_words, record_names(record)))


def canonical_organization(name: str | None, records: list[dict]) -> str | None:
    if name is None:
        return None
    matches = {
        normalize(r["name"])
        for r in records
        if r["entity_type"] == "company" and normalize(name) in map(normalize, record_names(r))
    }
    return matches.pop() if len(matches) == 1 else normalize(name)


def resolve(candidate: Candidate, records: list[dict], fixes: bool = True) -> dict:
    """Match a candidate to one record, several, or none. `fixes` turns on the workflow 4 rules."""
    subject = normalize(candidate.subject)
    matches = [
        r
        for r in records
        if r["entity_type"] == candidate.entity_type and subject in map(normalize, record_names(r))
    ]
    name_matches = [r["id"] for r in matches]
    if candidate.organization and candidate.entity_type == "person":
        stated = normalize(candidate.organization)
        companies = {
            normalize(r["name"])
            for r in records
            if r["entity_type"] == "company" and stated in map(normalize, record_names(r))
        }
        if len(companies) > 1:
            # The stated organization is a shared alias of several companies.
            return ambiguous(name_matches)
        org = canonical_organization(candidate.organization, records)
        contextual = [
            r for r in matches if canonical_organization(r.get("organization"), records) == org
        ]
        if fixes:
            # An unknown CRM organization does not contradict the stated one.
            contextual = contextual or [r for r in matches if not r.get("organization")]
        if matches and not contextual:
            # A name match with inconsistent context is not a new identity.
            return ambiguous(name_matches)
        matches = contextual
    if len(matches) == 1:
        return {"status": "matched", "entity_id": matches[0]["id"], "candidates": name_matches}
    if matches:
        return ambiguous(name_matches)
    related = [
        r["id"]
        for r in records
        if r["entity_type"] == candidate.entity_type and related_name(candidate.subject, r)
    ]
    if fixes and related:
        # A shorter or longer form of an existing name is not a safe new identity.
        return ambiguous(related)
    return {"status": "new", "entity_id": None, "candidates": []}
