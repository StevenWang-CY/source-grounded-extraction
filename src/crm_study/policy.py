"""The staged workflow's decision rules and the shared CRM writer."""

from copy import deepcopy

from .schema import Candidate, normalize, normalize_fact_value, quote_in_source


def decide(
    case: dict, candidate: Candidate | None, resolution: dict, semantic: dict | None
) -> dict:
    """Accept, review, or reject a candidate given its match and the verifier's checks."""
    if candidate is None:
        return {"decision": "reject", "reason": "no_candidate", "checks": {}}
    sources = {source["id"]: source for source in case["sources"]}
    source = sources.get(candidate.source_id)
    checks = {
        "source_exists": source is not None,
        "source_allowed": bool(source and source["allowed"]),
        "quote_matches": bool(source and quote_in_source(candidate.evidence, source["text"])),
        "subject_stated": bool(
            source and normalize(candidate.subject) in normalize(source["text"])
        ),
        "semantic_support": semantic["support"],
        "date_supported": semantic["date_supported"],
        "conflicting_sources": semantic["conflicting_sources"],
        "resolution": resolution["status"],
    }
    for key, reason in (
        ("source_exists", "unknown_source"),
        ("source_allowed", "source_not_allowed"),
        ("quote_matches", "evidence_not_in_source"),
    ):
        if not checks[key]:
            return {"decision": "reject", "reason": reason, "checks": checks}
    if not checks["subject_stated"]:
        return {"decision": "review", "reason": "subject_not_in_source", "checks": checks}
    current = case["time_scope"] == "current"
    if (
        current
        and candidate.entity_type == "person"
        and candidate.attribute == "role"
        and not candidate.organization
    ):
        return {"decision": "review", "reason": "missing_organization", "checks": checks}
    if semantic["conflicting_sources"]:
        return {"decision": "review", "reason": "conflicting_sources", "checks": checks}
    if semantic["support"] == "contradicted":
        return {"decision": "reject", "reason": "claim_contradicted", "checks": checks}
    if semantic["support"] != "supported":
        return {"decision": "review", "reason": "support_uncertain", "checks": checks}
    if not semantic["date_supported"]:
        return {"decision": "review", "reason": "date_not_supported", "checks": checks}
    if resolution["status"] == "ambiguous":
        return {"decision": "review", "reason": "ambiguous_identity", "checks": checks}
    if current:
        effective = candidate.effective_date
        if effective and effective > case["as_of"]:
            return {"decision": "review", "reason": "future_update", "checks": checks}
        record = next((r for r in case["crm"] if r["id"] == resolution["entity_id"]), None)
        old = record["facts"].get(candidate.attribute) if record else None
        if old:
            old_date = old.get("effective_date")
            # Even the same value must not replace newer provenance with an older or
            # unknown effective date. Publication time is deliberately not used here.
            if old_date and effective and effective < old_date:
                return {"decision": "reject", "reason": "stale_update", "checks": checks}
            different = normalize_fact_value(
                candidate.attribute, old["value"]
            ) != normalize_fact_value(candidate.attribute, candidate.value)
            if different and (not effective or not old_date):
                return {"decision": "review", "reason": "undated_conflict", "checks": checks}
            if old_date and not effective:
                return {"decision": "review", "reason": "undated_update", "checks": checks}
            if different and effective == old_date:
                return {"decision": "review", "reason": "same_date_conflict", "checks": checks}
    return {"decision": "accept", "reason": "supported_update", "checks": checks}


def apply_update(case: dict, prediction: dict) -> dict:
    """Write an accepted update into a copy of the case's initial CRM."""
    crm = deepcopy(case["crm"])
    if prediction["decision"] != "accept" or not prediction.get("candidate"):
        return {"applied": False, "record_id": None, "crm": crm}
    candidate, resolution = prediction["candidate"], prediction["resolution"]

    def refused(error):
        return {"applied": False, "record_id": None, "crm": crm, "error": error}

    if resolution["status"] == "new":
        record = {
            "id": f"new-{case['id']}",
            "entity_type": candidate["entity_type"],
            "name": candidate["subject"],
            "aliases": [],
            "organization": candidate.get("organization"),
            "facts": {},
        }
        crm.append(record)
    elif resolution["status"] == "matched":
        record = next((r for r in crm if r["id"] == resolution["entity_id"]), None)
        if record is None:
            return refused("unknown_record")
        if record["entity_type"] != candidate["entity_type"]:
            return refused("record_type_mismatch")
    else:
        return refused("unresolved_identity")
    record["facts"][candidate["attribute"]] = {
        "value": candidate["value"],
        "effective_date": candidate.get("effective_date"),
        "source_id": candidate["source_id"],
        "evidence": candidate["evidence"],
    }
    return {"applied": True, "record_id": record["id"], "crm": crm}
