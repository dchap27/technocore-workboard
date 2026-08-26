"""Offline parsing for Ed25519 ``did:key`` identifiers."""

from __future__ import annotations

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
BASE58_INDEX = {character: index for index, character in enumerate(BASE58_ALPHABET)}
ED25519_MULTICODEC_PREFIX = bytes((0xED, 0x01))
DID_KEY_PREFIX = "did:key:z"


class DIDError(ValueError):
    """Raised when a DID is not a supported Ed25519 did:key identifier."""


def base58_decode(value: str) -> bytes:
    """Decode unambiguous base58 without introducing another dependency."""
    if not value:
        raise DIDError("base58 value must not be empty")

    number = 0
    for character in value:
        try:
            digit = BASE58_INDEX[character]
        except KeyError as error:
            raise DIDError("base58 value contains an invalid character") from error
        number = number * 58 + digit

    leading_zeroes = len(value) - len(value.lstrip("1"))
    encoded = number.to_bytes((number.bit_length() + 7) // 8, "big")
    return b"\x00" * leading_zeroes + encoded


def public_key_from_did(did: str) -> Ed25519PublicKey:
    """Return the Ed25519 public key embedded in a Technocore DID.

    Technocore accepts only ``did:key:z...`` multibase/base58btc identifiers
    whose decoded bytes are the Ed25519 multicodec prefix (``ed01``) followed
    by a 32-byte raw public key.
    """
    if not isinstance(did, str) or not did.startswith(DID_KEY_PREFIX):
        raise DIDError("DID must start with did:key:z")

    decoded = base58_decode(did[len(DID_KEY_PREFIX) :])
    expected_length = len(ED25519_MULTICODEC_PREFIX) + 32
    if len(decoded) != expected_length:
        raise DIDError("DID must contain one 32-byte Ed25519 public key")
    if not decoded.startswith(ED25519_MULTICODEC_PREFIX):
        raise DIDError("DID is not an Ed25519 did:key identifier")

    try:
        return Ed25519PublicKey.from_public_bytes(decoded[len(ED25519_MULTICODEC_PREFIX) :])
    except ValueError as error:  # Defensive: the length is checked above.
        raise DIDError("DID contains an invalid Ed25519 public key") from error
