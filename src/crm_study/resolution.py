"""Resolve against this case's CRM, using names, aliases, and organization context."""

from .schema import Candidate, normalize, record_names


def ambiguous(candidates: list[str]) -> dict:
    return {"status": "ambiguous", "entity_id": None, "candidates": candidates}


def canonical_organization(name: str | None, records: list[dict]) -> str | None:
    if name is None:
        return None
    matches = {
        normalize(r["name"])
        for r in records
        if r["entity_type"] == "company" and normalize(name) in map(normalize, record_names(r))
    }
    return matches.pop() if len(matches) == 1 else normalize(name)


def resolve(candidate: Candidate, records: list[dict]) -> dict:
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
        if matches and not contextual:
            # A name match with inconsistent context is not a new identity.
            return ambiguous(name_matches)
        matches = contextual
    if len(matches) == 1:
        return {"status": "matched", "entity_id": matches[0]["id"], "candidates": name_matches}
    if matches:
        return ambiguous(name_matches)
    return {"status": "new", "entity_id": None, "candidates": []}
