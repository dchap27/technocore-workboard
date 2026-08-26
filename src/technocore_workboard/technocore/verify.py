"""Offline verification of signed Technocore Workboard events."""

from __future__ import annotations

import base64
import binascii
import re
from dataclasses import dataclass
from typing import Any

from cryptography.exceptions import InvalidSignature

from technocore_workboard.domain.events import EventValidationError, parse_event, serialize_event
from technocore_workboard.identity.did import DIDError, public_key_from_did

ROOM_PATTERN = re.compile(r"[a-z0-9][a-z0-9_-]{0,47}\Z")
NONCE_PATTERN = re.compile(r"[0-9]{1,19}\Z")
SIGNATURE_PATTERN = re.compile(r"[A-Za-z0-9_-]{86}\Z")


class SignatureVerificationError(ValueError):
    """Raised when a signed Technocore event cannot be independently verified."""


@dataclass(frozen=True, slots=True)
class VerifiedEvent:
    """A canonical Workboard event whose public Technocore signature verified."""

    room: str
    did: str
    nonce: str
    signature: str
    text: str
    event: dict[str, Any]


def signing_bytes(room: str, nonce: str | int, text: str) -> bytes:
    """Build the exact UTF-8 byte sequence signed by Technocore."""
    if not isinstance(room, str) or not ROOM_PATTERN.fullmatch(room):
        raise SignatureVerificationError("room is not a valid Technocore room name")
    normalized_nonce = str(nonce)
    if not NONCE_PATTERN.fullmatch(normalized_nonce):
        raise SignatureVerificationError("nonce must contain 1 to 19 digits")
    if not isinstance(text, str):
        raise SignatureVerificationError("text must be a string")
    return f"{room}|{normalized_nonce}|{text}".encode("utf-8")


def _decode_signature(signature: str) -> bytes:
    if not isinstance(signature, str) or not SIGNATURE_PATTERN.fullmatch(signature):
        raise SignatureVerificationError("signature must be an unpadded 86-character base64url value")
    try:
        decoded = base64.b64decode(signature + "==", altchars=b"-_", validate=True)
    except (ValueError, binascii.Error) as error:
        raise SignatureVerificationError("signature is not valid base64url") from error
    if len(decoded) != 64:
        raise SignatureVerificationError("signature must decode to 64 bytes")
    return decoded


def verify_signed_event(
    *, room: str, did: str, signature: str, nonce: str | int, text: str
) -> VerifiedEvent:
    """Validate canonical event text and verify its Technocore Ed25519 signature.

    This function performs no network requests and never accepts a private key.
    ``text`` must already be the exact stored event text, because Technocore
    signs the post-normalization text rather than a pre-normalized input.
    """
    try:
        event = parse_event(text)
        canonical_text = serialize_event(event)
    except EventValidationError as error:
        raise SignatureVerificationError("text is not a valid Workboard event") from error
    if text != canonical_text:
        raise SignatureVerificationError("text is valid JSON but not canonical Workboard event text")

    try:
        key = public_key_from_did(did)
    except DIDError as error:
        raise SignatureVerificationError("DID cannot be decoded as an Ed25519 did:key") from error

    signature_bytes = _decode_signature(signature)
    payload = signing_bytes(room, nonce, text)
    try:
        key.verify(signature_bytes, payload)
    except InvalidSignature as error:
        raise SignatureVerificationError("signature does not match room, nonce, DID, and text") from error

    return VerifiedEvent(
        room=room,
        did=did,
        nonce=str(nonce),
        signature=signature,
        text=text,
        event=event,
    )
