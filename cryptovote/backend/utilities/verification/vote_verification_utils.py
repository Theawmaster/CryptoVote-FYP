from flask import jsonify
from models.db import db
from models.encrypted_vote import EncryptedVote
from models.issued_token import IssuedToken
import hashlib
from datetime import datetime

def is_valid_hex(s):
    try:
        int(s, 16)
        return True
    except ValueError:
        return False

def validate_vote_request(data):
    required_fields = ["token", "signature", "ciphertext", "exponent"]
    for field in required_fields:
        if field not in data:
            return False, jsonify({"error": f"Missing field: {field}"}), 400
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
    return IssuedToken.query.filter_by(token_hash=token_hash).first() is not None

def store_vote_and_token(token_hash, ciphertext, exponent):
    vote = EncryptedVote(
        token_hash=token_hash,
        vote_ciphertext=ciphertext,
        vote_exponent=exponent,
        cast_at=datetime.utcnow()
    )
    db.session.add(vote)

    issued = IssuedToken(
        token_hash=token_hash,
        used=True,
        issued_at=datetime.utcnow()
    )
    db.session.add(issued)
    db.session.commit()
