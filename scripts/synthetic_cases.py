"""Authored CRM scenarios in four document forms.

Forms 0 and 1 are development and forms 2 and 3 are test, so a form never crosses the
split. Both splits share the scenario categories; entities, source text, and wording
differ.
"""

from copy import deepcopy

CATEGORIES = (
    "supported",
    "organization_alias",
    "ambiguous_identity",
    "context_resolution",
    "stale_update",
    "conflicting_sources",
    "disallowed_source",
    "tentative_claim",
    "explicit_denial",
    "duplicate_records",
    "new_entity",
    "future_update",
    "undated_conflict",
    "deal_relationship",
    "same_date_conflict",
    "explicit_correction",
    "employer",
    "irrelevant_document",
)
FIRST_NAMES = """Elena Julian Celia Dorian Anika Bruno Cora Darius Eliza Fabian Greta Hugo
Imani Jasper Keira Leon Maelle Nikhil Opal Pavel Quinn Rhea Stefan Uma Vera Wesley Xenia
Yara Zane Alina Benedict Camille Desmond Emilia Florian Giselle Henrik Ingrid Jonas
Karina Lorenzo Marisol Nikolai Odette Pascal Romina Soren Tatiana Ulrich Valeria Wilfred
Xander Yvette Zora Amelie Bastian Carina Dominic Estelle Frederick Gemma Hector Isobel
Joelle Kieran Luciana Matteo Nadine Orlando Paloma Quentin Rosalie""".split()
SURNAMES = "Voss Reeve Laurent Bhat Mensah Kovacs Duarte Okafor Petrov".split()
BRANDS = ["Alder", "Beacon", "Cypress", "Driftwood"]
BUSINESSES = """Photonics Logistics Materials Research Mobility Software Instruments
Storage Packaging Diagnostics Manufacturing Wireless Computing Studios Automation
Consulting Networks Ventures""".split()
FORMS = ["announcement", "staff_record", "meeting_minutes", "correspondence"]


def record(record_id, name, entity_type="person", organization=None, aliases=None, facts=None):
    return {
        "id": record_id,
        "name": name,
        "entity_type": entity_type,
        "organization": organization,
        "aliases": aliases or [],
        "facts": facts or {},
    }


def source(text, source_id="s1", allowed=True, source_date="2026-10-12", kind="document"):
    return {
        "id": source_id,
        "text": text,
        "allowed": allowed,
        "source_date": source_date,
        "kind": kind,
    }


def fact(
    subject,
    value,
    evidence,
    organization=None,
    effective_date="2026-09-08",
    source_id="s1",
    entity_type="person",
    attribute="role",
):
    return {
        "entity_type": entity_type,
        "subject": subject,
        "attribute": attribute,
        "value": value,
        "organization": organization,
        "effective_date": effective_date,
        "source_id": source_id,
        "evidence": evidence,
    }


def synthetic_cases():
    cases, labels = [], []
    for form in range(4):
        for number, category in enumerate(CATEGORIES):
            index = form * len(CATEGORIES) + number
            name = FIRST_NAMES[index] + " " + SURNAMES[index % len(SURNAMES)]
            org = BRANDS[form] + " " + BUSINESSES[number]
            role = ["CTO", "CFO", "COO", "CEO"][(number + form) % 4]
            other = ["CTO", "CFO", "COO", "CEO"][(number + form + 1) % 4]
            day = 8 + number % 8
            date = f"2026-09-{day:02d}"
            date_text = f"September {day}, 2026"
            subject, value, context = name, role, org
            effective, attribute, entity_type = date, "role", "person"
            company = record("org-1", org, "company")
            target = record("person-1", name, organization=org)
            crm = [company, target]
            status, entity_id, decision = "matched", "person-1", "accept"
            support, conflicts = "supported", False
            source_id, allowed = "s1", True
            additional, alternatives = [], []
            text = [
                f"People announcement: {name} joined {org} as {role}, effective {date_text}.",
                f"Staff record for {org}. Name: {name}. Position: {role}. In post since {date_text}.",
                f"The board of {org} recorded that {name} took up the {role} post on {date_text}. The minutes were approved at the next meeting.",
                f"To the account team: the appointment is confirmed. From {date_text}, our {role} at {org} is {name}. Please direct scheduling requests to the office.",
            ][form]
            rationale = "An explicit appointment, known effective date, and unique record support this update."
            if category == "organization_alias":
                alias = BRANDS[form][0] + BUSINESSES[number][0]
                company["aliases"] = [alias]
                text = text.replace(org, alias)
                context = alias
                rationale = "The company alias is declared in the CRM; the source need not use its full name."
            elif category == "ambiguous_identity":
                subject = FIRST_NAMES[index]
                target["aliases"] = [subject]
                crm.append(
                    record("person-2", subject + " Bellamy", organization=org, aliases=[subject])
                )
                text = text.replace(name, subject)
                decision, status, entity_id = "review", "ambiguous", None
                rationale = "The source supplies only a first name shared by two people at the same company."
            elif category == "context_resolution":
                crm.append(record("person-2", name, organization=org + " International"))
                rationale = (
                    "Two people share a full name; the explicit employer selects one record."
                )
            elif category == "stale_update":
                effective = f"2025-09-{day:02d}"
                text = text.replace("2026", "2025")
                target["facts"] = {"role": {"value": other, "effective_date": "2026-10-01"}}
                decision = "reject"
                rationale = (
                    "Recent publication of an old appointment cannot replace a newer CRM fact."
                )
            elif category == "conflicting_sources":
                second = [
                    f"Separate personnel notice: {name} became {other} at {org} on {date_text}.",
                    f"Department register for {org}: {name}; title {other}; start date {date_text}.",
                    f"A second committee's record lists {name} as {org}'s {other} from {date_text}.",
                    f"Reply from {org}: our records say {name} has held the {other} job since {date_text}.",
                ][form]
                additional = [source(second, "s2", source_date="2026-10-13")]
                alternatives = [fact(name, other, second, org, date, "s2")]
                decision, conflicts = "review", True
                rationale = "Allowed sources give different roles for the same effective date without a correction."
            elif category == "disallowed_source":
                allowed, decision = False, "reject"
                rationale = "The source permission forbids using even an otherwise well-supported statement."
            elif category == "tentative_claim":
                text = [
                    f"Unconfirmed hiring note: {org} may appoint {name} as {role}. The appointment is still under discussion.",
                    f"Draft staff record, {org}: {name} is being considered for {role}; approval is pending.",
                    f"The committee discussed whether {name} should become {role} of {org}, but made no decision.",
                    f"Regarding {org}: I heard {name} might take the {role} job. I have no confirmation of an appointment.",
                ][form]
                effective, support, decision = None, "uncertain", "review"
                rationale = "A proposed or rumored role is a candidate claim, not an established appointment."
            elif category == "explicit_denial":
                text = [
                    f"Correction from {org}: {name} has not been appointed {role}. The circulating appointment claim is false.",
                    f"Staff verification, {org}: no {role} appointment exists for {name}; the reported appointment is denied.",
                    f"The board rejected the statement that {name} became {role} of {org}. No such appointment occurred.",
                    f"Please correct your note about {org}. {name} did not become our {role}; that information is incorrect.",
                ][form]
                effective, support, decision = None, "contradicted", "reject"
                rationale = "The exact quoted passage explicitly denies the candidate appointment."
            elif category == "duplicate_records":
                crm.append({**deepcopy(target), "id": "person-2"})
                decision, status, entity_id = "review", "ambiguous", None
                rationale = "Two indistinguishable CRM records must be reconciled before writing."
            elif category == "new_entity":
                crm = [company]
                status, entity_id = "new", None
                rationale = (
                    "A supported identity with no existing match can create a new candidate record."
                )
            elif category == "future_update":
                effective = f"2027-01-{day:02d}"
                text = [
                    f"{org} has announced that {name} will take office as {role} on January {day}, 2027.",
                    f"Future staff record for {org}: {name}, incoming {role}. The appointment starts January {day}, 2027.",
                    f"The board appointed {name} to become {org}'s {role} effective January {day}, 2027; the change has not taken effect.",
                    f"For your planning: {name} will be {role} at {org} starting January {day}, 2027. This is a future change.",
                ][form]
                decision = "review"
                rationale = "The appointment is explicit but its effective date is later than the case's as-of date."
            elif category == "undated_conflict":
                text = [
                    f"{name} is listed as {role} at {org}. This directory provides no start date.",
                    f"Staff record for {org}: {name}; current title {role}; effective date not recorded.",
                    f"The minutes identify {name} as {org}'s {role} without saying when that role began.",
                    f"Our contact {name} holds the {role} position at {org}. I do not have the appointment date.",
                ][form]
                target["facts"] = {"role": {"value": other, "effective_date": "2026-08-01"}}
                effective, decision = None, "review"
                rationale = "The conflicting role lacks an effective date needed to supersede the known fact."
            elif category == "deal_relationship":
                subject = BRANDS[form] + " renewal"
                attribute, entity_type, value, context, effective = (
                    "deal_company",
                    "deal",
                    org,
                    None,
                    None,
                )
                crm = [company, record("deal-1", subject, "deal")]
                entity_id = "deal-1"
                text = [
                    f"Opportunity note: the deal named {subject} is associated with {org}. Pricing discussions are ongoing.",
                    f"Deal register: {subject}. Customer company: {org}. Status: under discussion.",
                    f"The meeting linked the opportunity {subject} to {org}; no completion was recorded.",
                    f"Please associate {subject} with {org} in the opportunity list. The deal remains open.",
                ][form]
                rationale = "Only the explicit deal/company association is requested; no closed-deal claim is made."
            elif category == "same_date_conflict":
                target["facts"] = {"role": {"value": other, "effective_date": date}}
                decision = "review"
                rationale = (
                    "Conflicting values with the same effective date have no temporal precedence."
                )
            elif category == "explicit_correction":
                old = text.replace(role, other)
                additional = [source(old, "s1", source_date="2026-10-10")]
                text = [
                    f"Dated correction, October 12, 2026: the earlier {org} notice listed {name} as {other} in error. The correct appointment is {role}, effective {date_text}.",
                    f"Amended {org} staff record, October 12, 2026: replace the earlier {other} entry for {name}. Position: {role}; effective from {date_text}.",
                    f"On October 12, 2026, the board corrected its earlier {org} minutes: {name}'s appointment was to {role}, not {other}, on {date_text}.",
                    f"This October 12, 2026 reply supersedes our earlier message: {name} became {role} at {org} on {date_text}. Our {other} claim was a mistake.",
                ][form]
                source_id = "s2"
                rationale = (
                    "The later explicitly dated correction replaces the earlier incorrect source."
                )
            elif category == "employer":
                attribute, value, context = "employer", org, None
                text = [
                    f"Employment notice: {name} began working for {org} on {date_text}.",
                    f"Employment record: {name}. Employer: {org}. Employment start: {date_text}.",
                    f"The staffing committee confirmed that {name} started employment with {org} on {date_text}.",
                    f"For the account file: {name} joined {org} on {date_text}. The job title was not provided.",
                ][form]
                rationale = "The employer and employment start are explicit; no professional title is invented."
            elif category == "irrelevant_document":
                text = [
                    f"{org}'s office will close for maintenance. {name} is listed as an emergency contact; no title or appointment is stated.",
                    f"Delivery record for {org}. Recipient: {name}. Shipment: two replacement keyboards.",
                    f"The committee thanked {name} for attending the {org} facilities meeting. It discussed room bookings only.",
                    f"Hello {name}, your visitor pass for {org} is ready. Please collect it at reception.",
                ][form]
                decision, status, entity_id = "reject", "ambiguous", None
                rationale = "The requested role is absent; a contact name alone does not supply a candidate role."
            expected = [
                fact(subject, value, text, context, effective, source_id, entity_type, attribute)
            ]
            expected += alternatives
            if category == "organization_alias":
                expected.append({**expected[0], "organization": org})
            if category == "irrelevant_document":
                expected = []
            case_id = f"scenario-{number + 1:02d}-{form + 1}"
            sources = additional + [source(text, source_id, allowed, kind=FORMS[form])]
            # Source ordering carries no implicit authority; corrections are stated in the text.
            sources.sort(key=lambda s: s["id"])
            identity_names = {name, org, subject}
            identity_names.update(r["name"] for r in crm)
            identity_names.update(r["organization"] for r in crm if r.get("organization"))
            cases.append(
                {
                    "id": case_id,
                    "dataset_version": "2",
                    "split": "dev" if form < 2 else "test",
                    "origin": "synthetic",
                    "category": category,
                    "query": f"Extract the proposed {attribute} update for {subject}. Use only the supplied source evidence.",
                    "as_of": "2026-10-17",
                    "time_scope": "current",
                    "sources": sources,
                    "crm": crm,
                    "split_keys": [f"identity:{n.casefold()}" for n in sorted(identity_names)]
                    + [f"template:{FORMS[form]}-v2"],
                    "provenance": {
                        "kind": "authored_synthetic",
                        "template_id": FORMS[form] + "-v2",
                        "scenario": category,
                    },
                }
            )
            labels.append(
                {
                    "case_id": case_id,
                    "dataset_version": "2",
                    "decision": decision,
                    "resolution": {"status": status, "entity_id": entity_id},
                    "candidates": expected,
                    "verification": {
                        "support": support,
                        "date_supported": True,
                        "conflicting_sources": conflicts,
                    },
                    "rationale": rationale,
                    "annotation": "Project-authored scenario and answer key; not independent human annotation",
                }
            )
    return cases, labels
