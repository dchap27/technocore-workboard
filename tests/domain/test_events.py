from __future__ import annotations

import pytest

from technocore_workboard.domain.events import EventValidationError, parse_event, serialize_event


TASK = {
    "v": 1,
    "type": "task",
    "id": "wb-8f01a9bc2d3e",
    "title": "Protocol explainer",
    "summary": "Write a concise protocol explainer.",
    "acceptance": ["Includes tests", "Has an MIT license"],
    "artifact_url": "https://example.org/spec",
}


def test_task_is_normalized_and_canonicalized() -> None:
    serialized = serialize_event(TASK)

    assert serialized == (
        '{"acceptance":["Includes tests","Has an MIT license"],'
        '"artifact_url":"https://example.org/spec","id":"wb-8f01a9bc2d3e",'
        '"summary":"Write a concise protocol explainer.","title":"Protocol explainer",'
        '"type":"task","v":1}'
    )
    assert parse_event(serialized) == TASK


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({**TASK, "unexpected": True}, "unknown fields"),
        ({**TASK, "id": "not-an-id"}, "id must match"),
        ({**TASK, "title": " title"}, "trimmed"),
        ({**TASK, "summary": "line one\nline two"}, "control or format"),
        ({**TASK, "acceptance": []}, "1 to 10"),
        ({**TASK, "artifact_url": "ftp://example.org"}, "must start"),
    ],
)
def test_invalid_task_is_rejected(payload: dict[str, object], message: str) -> None:
    with pytest.raises(EventValidationError, match=message):
        parse_event(payload)


def test_claim_and_submission_accept_valid_payloads() -> None:
    claim = {
        "v": 1,
        "type": "claim",
        "id": "wb-9e02b8ad4c5f",
        "task_id": TASK["id"],
        "note": "I will deliver a draft and tests.",
    }
    submission = {
        "v": 1,
        "type": "submission",
        "id": "wb-0a1b2c3d4e5f",
        "task_id": TASK["id"],
        "result_url": "https://github.com/example/repo/pull/7",
        "summary": "A documented implementation with unit tests.",
    }

    assert parse_event(claim) == claim
    assert parse_event(submission) == submission
