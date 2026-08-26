"""Validation and canonical serialization for Workboard v1 events."""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Mapping
from typing import Any

PROTOCOL_VERSION = 1
EVENT_ID_PATTERN = re.compile(r"wb-[a-z0-9]{12,64}\Z")
EVENT_TYPES = frozenset({"task", "claim", "submission"})
COMMON_FIELDS = frozenset({"v", "type", "id"})
TYPE_FIELDS = {
    "task": frozenset({"title", "summary", "acceptance", "artifact_url"}),
    "claim": frozenset({"task_id", "note"}),
    "submission": frozenset({"task_id", "result_url", "summary"}),
}
REQUIRED_FIELDS = {
    "task": frozenset({"title", "summary", "acceptance"}),
    "claim": frozenset({"task_id"}),
    "submission": frozenset({"task_id", "result_url", "summary"}),
}


class EventValidationError(ValueError):
    """Raised when a payload is not a valid Workboard v1 event."""


def _invalid(message: str) -> None:
    raise EventValidationError(message)


def _validate_string(value: Any, field: str, maximum: int) -> str:
    if not isinstance(value, str):
        _invalid(f"{field} must be a string")
    if value != value.strip() or not value:
        _invalid(f"{field} must be non-empty and trimmed")
    if len(value) > maximum:
        _invalid(f"{field} exceeds {maximum} characters")
    if any(unicodedata.category(char).startswith(("C",)) for char in value):
        _invalid(f"{field} contains a control or format character")
    return value


def _validate_event_id(value: Any, field: str = "id") -> str:
    value = _validate_string(value, field, 67)
    if not EVENT_ID_PATTERN.fullmatch(value):
        _invalid(f"{field} must match wb-[a-z0-9]{{12,64}}")
    return value


def parse_event(payload: str | bytes | bytearray | Mapping[str, Any]) -> dict[str, Any]:
    """Parse, validate, and return a normalized Workboard v1 event mapping."""
    if isinstance(payload, (str, bytes, bytearray)):
        try:
            decoded = json.loads(payload)
        except (TypeError, json.JSONDecodeError) as error:
            raise EventValidationError("payload is not valid JSON") from error
    elif isinstance(payload, Mapping):
        decoded = dict(payload)
    else:
        _invalid("payload must be a JSON object or mapping")

    if not isinstance(decoded, dict):
        _invalid("payload must be a JSON object")
    if decoded.get("v") != PROTOCOL_VERSION:
        _invalid("v must be 1")

    event_type = decoded.get("type")
    if event_type not in EVENT_TYPES:
        _invalid("type must be task, claim, or submission")

    allowed = COMMON_FIELDS | TYPE_FIELDS[event_type]
    unknown = set(decoded) - allowed
    missing = (COMMON_FIELDS | REQUIRED_FIELDS[event_type]) - set(decoded)
    if unknown:
        _invalid(f"unknown fields: {', '.join(sorted(unknown))}")
    if missing:
        _invalid(f"missing fields: {', '.join(sorted(missing))}")

    normalized: dict[str, Any] = {
        "v": PROTOCOL_VERSION,
        "type": event_type,
        "id": _validate_event_id(decoded["id"]),
    }

    if event_type == "task":
        normalized["title"] = _validate_string(decoded["title"], "title", 160)
        normalized["summary"] = _validate_string(decoded["summary"], "summary", 2000)
        acceptance = decoded["acceptance"]
        if not isinstance(acceptance, list) or not 1 <= len(acceptance) <= 10:
            _invalid("acceptance must contain 1 to 10 items")
        normalized["acceptance"] = [
            _validate_string(item, "acceptance item", 500) for item in acceptance
        ]
        if "artifact_url" in decoded:
            normalized["artifact_url"] = _validate_url(decoded["artifact_url"], "artifact_url")
    elif event_type == "claim":
        normalized["task_id"] = _validate_event_id(decoded["task_id"], "task_id")
        if "note" in decoded:
            normalized["note"] = _validate_string(decoded["note"], "note", 500)
    else:
        normalized["task_id"] = _validate_event_id(decoded["task_id"], "task_id")
        normalized["result_url"] = _validate_url(decoded["result_url"], "result_url")
        normalized["summary"] = _validate_string(decoded["summary"], "summary", 2000)

    return normalized


def _validate_url(value: Any, field: str) -> str:
    value = _validate_string(value, field, 2000)
    if not value.startswith(("https://", "http://")):
        _invalid(f"{field} must start with http:// or https://")
    return value


def serialize_event(payload: str | bytes | bytearray | Mapping[str, Any]) -> str:
    """Return the sole canonical JSON representation accepted by v1."""
    return json.dumps(
        parse_event(payload),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
