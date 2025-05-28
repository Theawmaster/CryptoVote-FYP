from flask import Blueprint, request, jsonify
from models.db import db
from models.issued_token import IssuedToken
from models.encrypted_candidate_vote import EncryptedCandidateVote
from utilities.blind_signature_utils import load_public_key as load_rsa_pubkey
from utilities.paillier_utils import load_public_key as load_paillier_public_key
from utilities.verification.vote_verification_utils import (
    validate_vote_request,
    parse_and_verify_signature,
    is_token_used
)
import hashlib
from datetime import datetime

cast_vote_bp = Blueprint('cast_vote', __name__)
CANDIDATE_IDS = ["alice", "bob", "charlie"]

@cast_vote_bp.route('/cast-vote', methods=['POST'])
def cast_vote():
    data = request.get_json()

    # ✅ 1. Validate vote request
    ok, response, status = validate_vote_request(data)
    if not ok:
        return response, status

    token = data["token"]
    signature_hex = data["signature"]
    candidate_id = data["candidate_id"]

    # ✅ 2. Verify blind signature on token
    valid_sig, signature_int, error_response = parse_and_verify_signature(token, signature_hex, load_rsa_pubkey())
    if not valid_sig:
        return error_response if isinstance(error_response, tuple) else (jsonify({"error": str(error_response)}), 400)

    # ✅ 3. Check for token reuse
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    if is_token_used(token_hash):
        return jsonify({"error": "Token has already been used"}), 403

    # ✅ 4. Encrypt one vote per candidate using Paillier
    public_key = load_paillier_public_key()
    for cid in CANDIDATE_IDS:
        value = 1 if cid == candidate_id else 0
        enc = public_key.encrypt(value)

        encrypted_vote = EncryptedCandidateVote(
            candidate_id=cid,
            vote_ciphertext=str(enc.ciphertext()),
            vote_exponent=enc.exponent,
            token_hash=token_hash,
            cast_at=datetime.utcnow()
        )
        db.session.add(encrypted_vote)

    # ✅ 5. Mark token as used
    used_token = IssuedToken.query.filter_by(token_hash=token_hash).first()
    if used_token:
        used_token.used = True

    db.session.commit()

    return jsonify({"message": "✅ Vote cast successfully."}), 200
