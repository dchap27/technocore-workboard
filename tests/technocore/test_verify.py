from __future__ import annotations

import base64

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from technocore_workboard.domain.events import serialize_event
from technocore_workboard.technocore.verify import (
    SignatureVerificationError,
    signing_bytes,
    verify_signed_event,
)

BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def base58_encode(value: bytes) -> str:
    number = int.from_bytes(value, "big")
    result = ""
    while number:
        number, remainder = divmod(number, 58)
        result = BASE58_ALPHABET[remainder] + result
    return "1" * (len(value) - len(value.lstrip(b"\x00"))) + (result or "1")


def signed_task() -> tuple[str, str, str, str, str]:
    private_key = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    public_key = private_key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    did = "did:key:z" + base58_encode(b"\xed\x01" + public_key)
    room = "workboard-v1"
    nonce = "1727000000000"
    text = serialize_event(
        {
            "v": 1,
            "type": "task",
            "id": "wb-8f01a9bc2d3e",
            "title": "Protocol explainer",
            "summary": "Write a concise protocol explainer.",
            "acceptance": ["Includes tests"],
        }
    )
    signature = base64.urlsafe_b64encode(private_key.sign(signing_bytes(room, nonce, text))).decode().rstrip("=")
    return room, did, signature, nonce, text


def test_verifies_a_canonical_signed_event() -> None:
    room, did, signature, nonce, text = signed_task()

    verified = verify_signed_event(
        room=room, did=did, signature=signature, nonce=nonce, text=text
    )

    assert verified.did == did
    assert verified.event["type"] == "task"
    assert verified.event["id"] == "wb-8f01a9bc2d3e"


def test_rejects_a_modified_event() -> None:
    room, did, signature, nonce, text = signed_task()

    with pytest.raises(SignatureVerificationError, match="does not match"):
        verify_signed_event(
            room=room,
            did=did,
            signature=signature,
            nonce=nonce,
            text=text.replace("explainer", "guide"),
        )


def test_rejects_noncanonical_json_before_signature_verification() -> None:
    room, did, signature, nonce, text = signed_task()
    noncanonical = text.replace(",", ", ")

    with pytest.raises(SignatureVerificationError, match="not canonical"):
        verify_signed_event(
            room=room, did=did, signature=signature, nonce=nonce, text=noncanonical
        )


@pytest.mark.parametrize(
    ("field", "replacement", "message"),
    [
        ("did", "did:key:znot-base58-0", "DID cannot"),
        ("signature", "a" * 86, "does not match"),
        ("nonce", "not-a-nonce", "nonce must"),
    ],
)
def test_rejects_invalid_signed_envelope(field: str, replacement: str, message: str) -> None:
    room, did, signature, nonce, text = signed_task()
    values = {"room": room, "did": did, "signature": signature, "nonce": nonce, "text": text}
    values[field] = replacement

    with pytest.raises(SignatureVerificationError, match=message):
        verify_signed_event(**values)
