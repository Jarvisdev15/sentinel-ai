from __future__ import annotations

import base64
import copy
import hashlib
import json
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
)


def serialize_incident(incident: dict[str, Any]) -> bytes:
    """
    Convert an incident dictionary into deterministic bytes.

    Sorting the keys ensures the same incident always produces
    the same byte representation before signing and verification.
    """
    return json.dumps(
        incident,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


def create_keypair() -> tuple[
    Ed25519PrivateKey,
    Ed25519PublicKey,
]:
    """Create an Ed25519 private/public key pair."""
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    return private_key, public_key


def sign_incident(
    incident: dict[str, Any],
    private_key: Ed25519PrivateKey,
) -> bytes:
    """Sign an incident using the Ed25519 private key."""
    incident_bytes = serialize_incident(incident)

    return private_key.sign(incident_bytes)


def verify_incident(
    incident: dict[str, Any],
    signature: bytes,
    public_key: Ed25519PublicKey,
) -> bool:
    """
    Verify that an incident has not changed since it was signed.

    Returns True when valid and False when the incident has been
    modified or the signature is invalid.
    """
    incident_bytes = serialize_incident(incident)

    try:
        public_key.verify(
            signature,
            incident_bytes,
        )
        return True

    except InvalidSignature:
        return False


def tamper_incident(
    incident: dict[str, Any],
) -> dict[str, Any]:
    """
    Return a modified copy of an incident.

    The original incident remains unchanged. The final score is
    deliberately altered to demonstrate verification failure.
    """
    tampered = copy.deepcopy(incident)

    original_score = float(
        tampered["result"]["final_score"]
    )

    if original_score < 100:
        changed_score = min(
            original_score + 5,
            100,
        )
    else:
        changed_score = original_score - 5

    tampered["result"]["final_score"] = round(
        changed_score,
        2,
    )

    return tampered


def signature_to_text(signature: bytes) -> str:
    """Convert a binary signature into readable Base64 text."""
    return base64.b64encode(signature).decode("utf-8")


def public_key_fingerprint(
    public_key: Ed25519PublicKey,
) -> str:
    """
    Produce a short SHA-256 fingerprint of the public verification key.
    """
    public_key_bytes = public_key.public_bytes(
        encoding=Encoding.Raw,
        format=PublicFormat.Raw,
    )

    digest = hashlib.sha256(
        public_key_bytes
    ).hexdigest()

    return ":".join(
        digest[index:index + 2]
        for index in range(0, 24, 2)
    )