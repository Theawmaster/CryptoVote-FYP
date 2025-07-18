from flask import jsonify
from models.db import db
from models.encrypted_candidate_vote import EncryptedCandidateVote
from models.issued_token import IssuedToken
from utilities.paillier_utils import load_public_key
from datetime import datetime
import hashlib

CANDIDATE_IDS = ["adriel", "brend", "chock"]


def is_valid_hex(s):
    try:
        int(s, 16)
        return True
    except ValueError:
        return False


def validate_vote_request(data):
    required_fields = ["token", "signature", "candidate_id"]
    for field in required_fields:
        if field not in data:
            return False, jsonify({"error": f"Missing field: {field}"}), 400

    if data["candidate_id"] not in CANDIDATE_IDS:
        return False, jsonify({"error": "Invalid candidate_id"}), 400

    return True, None, None


def parse_and_verify_signature(token, signature_hex, pubkey):
    signature_hex = signature_hex.strip()
    if not is_valid_hex(signature_hex):
        return False, jsonify({"error": "Signature must be valid hex"}), 400

    try:
        signature_int = int(signature_hex, 16)
    except ValueError:
        return False, jsonify({"error": "Failed to parse signature"}), 400

    token_bytes = token.encode('utf-8')
    from ..blind_signature_utils import verify_signed_token
    is_valid = verify_signed_token(pubkey, token_bytes, signature_int)
    if not is_valid:
        return False, jsonify({"error": "Invalid signature"}), 403

    return True, signature_int, None


def is_token_used(token_hash):
    return IssuedToken.query.filter_by(token_hash=token_hash, used=True).first() is not None


def store_vote_and_token(token_hash, selected_candidate_id):
    """
    Encrypt and store one vote per candidate, and mark token as used.
    """
    from phe import paillier
    pubkey = load_public_key()

    for cid in CANDIDATE_IDS:
        value = 1 if cid == selected_candidate_id else 0
        enc = pubkey.encrypt(value)

        encrypted_vote = EncryptedCandidateVote(
            candidate_id=cid,
            vote_ciphertext=str(enc.ciphertext()),
            vote_exponent=enc.exponent,
            token_hash=token_hash,
            cast_at=datetime.utcnow()
        )
        db.session.add(encrypted_vote)

    issued = IssuedToken(
        token_hash=token_hash,
        used=True,
        issued_at=datetime.utcnow()
    )
    db.session.add(issued)
    db.session.commit()
