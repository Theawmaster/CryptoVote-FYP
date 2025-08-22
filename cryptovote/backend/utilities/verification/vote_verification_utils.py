# utilities/verification/vote_verification_utils.py
from flask import jsonify

from models.issued_token import IssuedToken

HEX_CHARS = set("0123456789abcdefABCDEF")


def _is_hex(s: str) -> bool:
    return isinstance(s, str) and len(s) > 0 and all(ch in HEX_CHARS for ch in s)


def validate_vote_request(data):
    """
    Minimal schema validation only.
    Do NOT check candidate membership here; cast_vote.py will verify against DB.
    """
    if not isinstance(data, dict):
        return False, (jsonify({"error": "bad_json"}), 400), 400

    required = ["election_id", "candidate_id", "token", "signature"]
    for k in required:
        if k not in data:
            return False, (jsonify({"error": "missing_field", "field": k}), 400), 400
        if not isinstance(data[k], str) or not data[k]:
            return False, (jsonify({"error": "bad_field_type", "field": k}), 400), 400

    # light bounds
    if len(data["election_id"]) > 128:
        return False, (jsonify({"error": "election_id_too_long"}), 400), 400
    if len(data["candidate_id"]) > 128:
        return False, (jsonify({"error": "candidate_id_too_long"}), 400), 400
    if len(data["token"]) > 512:
        return False, (jsonify({"error": "token_too_long"}), 400), 400

    sig = data["signature"]
    if not _is_hex(sig) or not (64 <= len(sig) <= 2048):
        return False, (jsonify({"error": "bad_signature_format"}), 400), 400

    return True, (jsonify({"ok": True}), 200), 200


def parse_and_verify_signature(token: str, signature_hex: str, pubkey):
    """
    Convert hex -> int and verify RSA blind signature against token digest.
    `pubkey` is the RSA public key object returned by your loader.
    """
    signature_hex = signature_hex.strip()
    if not _is_hex(signature_hex):
        return False, (jsonify({"error": "signature_not_hex"}), 400), 400

    try:
        signature_int = int(signature_hex, 16)
    except ValueError:
        return False, (jsonify({"error": "signature_parse_failed"}), 400), 400

    from utilities.blind_signature_utils import verify_signed_token
    token_bytes = token.encode("utf-8")
    if not verify_signed_token(pubkey, token_bytes, signature_int):
        return False, (jsonify({"error": "invalid_signature"}), 403), 403

    return True, signature_int, None


def is_token_used(token_hash: str) -> bool:
    return (
        IssuedToken.query.filter_by(token_hash=token_hash, used=True).first()
        is not None
    )
