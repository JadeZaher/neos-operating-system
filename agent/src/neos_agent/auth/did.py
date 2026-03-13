"""W3C did:key utilities for Ed25519 identity verification.

Implements the did:key method (https://w3c-ccg.github.io/did-method-key/)
using Ed25519 keypairs. No blockchain or external resolver needed — the
public key is encoded directly in the DID string.
"""

from __future__ import annotations

import base58
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

# Multicodec prefix for Ed25519 public keys
_ED25519_MULTICODEC = b"\xed\x01"


def did_key_to_public_bytes(did: str) -> bytes:
    """Extract raw 32-byte Ed25519 public key from a did:key string.

    Args:
        did: A W3C DID in did:key:z... format.

    Returns:
        32 bytes of the Ed25519 public key.

    Raises:
        ValueError: If the DID format is invalid or uses an unsupported key type.
    """
    if not did.startswith("did:key:z"):
        raise ValueError("Only did:key with base58btc (z-prefix) supported")

    # Strip "did:key:z" prefix and base58-decode
    multicodec_bytes = base58.b58decode(did[9:])

    if multicodec_bytes[:2] != _ED25519_MULTICODEC:
        raise ValueError("Only Ed25519 keys supported (multicodec 0xed01)")

    pub_bytes = multicodec_bytes[2:]
    if len(pub_bytes) != 32:
        raise ValueError(f"Expected 32-byte public key, got {len(pub_bytes)}")

    return pub_bytes


def public_bytes_to_did_key(pub_bytes: bytes) -> str:
    """Construct a did:key string from raw Ed25519 public key bytes.

    Args:
        pub_bytes: 32-byte Ed25519 public key.

    Returns:
        A W3C DID string in did:key:z... format.
    """
    if len(pub_bytes) != 32:
        raise ValueError(f"Expected 32-byte public key, got {len(pub_bytes)}")

    multicodec = _ED25519_MULTICODEC + pub_bytes
    return "did:key:z" + base58.b58encode(multicodec).decode("ascii")


def verify_did_signature(did: str, challenge: str, signature_hex: str) -> bool:
    """Verify a challenge signature against a did:key identity.

    Args:
        did: The signer's DID (did:key:z...).
        challenge: The original challenge string that was signed.
        signature_hex: Hex-encoded Ed25519 signature.

    Returns:
        True if the signature is valid, False otherwise.
    """
    try:
        pub_bytes = did_key_to_public_bytes(did)
        verify_key = VerifyKey(pub_bytes)
        signature = bytes.fromhex(signature_hex)
        verify_key.verify(challenge.encode("utf-8"), signature)
        return True
    except (BadSignatureError, ValueError, Exception):
        return False
