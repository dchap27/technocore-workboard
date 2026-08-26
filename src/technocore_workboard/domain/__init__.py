"""Protocol-domain validation and canonical encoding."""

from technocore_workboard.domain.events import EventValidationError, parse_event, serialize_event

__all__ = ["EventValidationError", "parse_event", "serialize_event"]
