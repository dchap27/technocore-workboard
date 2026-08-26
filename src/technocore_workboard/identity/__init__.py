"""Public DID parsing utilities.

This package deliberately handles public keys only. Local private-key loading
and signing will be introduced separately and never belong in an indexer.
"""

from technocore_workboard.identity.did import DIDError, public_key_from_did

__all__ = ["DIDError", "public_key_from_did"]
