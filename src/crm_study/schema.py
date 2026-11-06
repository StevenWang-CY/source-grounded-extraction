"""The small data contract shared by the two workflows."""

import json
import re
import unicodedata
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

ENTITY_ATTRIBUTES = {
    "person": {"role", "employer"},
    "company": {"headquarters", "owned_by"},
    "deal": {"deal_company"},
}
DECISIONS = {"accept", "review", "reject"}
ROLE_ALIASES = {
    "chief executive officer": "ceo",
    "chief technology officer": "cto",
    "chief financial officer": "cfo",
    "chief operating officer": "coo",
}


def normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def record_names(record: dict) -> list[str]:
    """A CRM record's name and declared aliases."""
    return [record["name"], *record["aliases"]]


def normalize_fact_value(attribute: str, value: str) -> str:
    text = normalize(value)
    if attribute == "role":
        text = text.removeprefix("the ")
        return ROLE_ALIASES.get(text, text)
    return text


def validate_resolution(resolution: dict) -> None:
    if not isinstance(resolution, dict):
        raise ValueError("resolution must be an object")
    status, entity_id = resolution.get("status"), resolution.get("entity_id")
    if status not in {"matched", "new", "ambiguous"}:
        raise ValueError("Invalid resolution status")
    if status == "matched":
        if not isinstance(entity_id, str) or not entity_id.strip():
            raise ValueError("A matched resolution needs a CRM ID")
    elif entity_id is not None:
        raise ValueError("A new or ambiguous resolution must have a null CRM ID")


def quote_in_source(quote: str, text: str) -> bool:
    # Only whitespace is normalized: case and punctuation still have to match.
    return bool(quote.strip()) and " ".join(quote.split()) in " ".join(text.split())


def validate_date(value: str | None) -> None:
    if value is not None:
        if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError("Dates must be YYYY-MM-DD or null; do not invent a day")
        date.fromisoformat(value)


@dataclass
class Candidate:
    entity_type: str
    subject: str
    attribute: str
    value: str
    source_id: str
    evidence: str
    organization: str | None = None
    effective_date: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "Candidate":
        if not isinstance(data, dict):
            raise ValueError("candidate must be an object or null")
        # Extra model fields stay in the raw trace and are ignored here.
        result = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        for field in ("entity_type", "subject", "attribute", "value", "source_id", "evidence"):
            if not isinstance(getattr(result, field), str) or not getattr(result, field).strip():
                raise ValueError(f"candidate.{field} must be a nonempty string")
        if result.attribute not in ENTITY_ATTRIBUTES.get(result.entity_type, set()):
            raise ValueError("Attribute is not valid for this entity type")
        if result.organization is not None and not isinstance(result.organization, str):
            raise ValueError("organization must be a string or null")
        validate_date(result.effective_date)
        return result

    def to_dict(self) -> dict:
        return asdict(self)


def parse_json_response(text: str) -> dict:
    """Accept a JSON object, optionally enclosed in a Markdown fence."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    result = json.loads(text)
    if not isinstance(result, dict):
        raise ValueError("The model must return a JSON object")
    return result


def read_jsonl(path: str | Path) -> list[dict]:
    with Path(path).open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def write_jsonl(path: str | Path, rows: list[dict]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
