from flask import Blueprint, request, jsonify
from models.db import db
from models.encrypted_vote import EncryptedVote
from models.issued_token import IssuedToken
from utilities.blind_signature_utils import load_public_key
from utilities.verification.vote_verification_utils import (
    is_valid_hex,
    validate_vote_request,
    parse_and_verify_signature,
    is_token_used,
    store_vote_and_token
)
import hashlib

cast_vote_bp = Blueprint('cast_vote', __name__)

@cast_vote_bp.route('/cast-vote', methods=['POST'])
def cast_vote():
    data = request.get_json()

    # Validate fields
    ok, response, status = validate_vote_request(data)
    if not ok:
        return response, status

    token = data["token"]
    signature_hex = data["signature"]
    ciphertext = data["ciphertext"]
    exponent = data["exponent"]

    # Verify signature
    valid_sig, signature_int, error_response = parse_and_verify_signature(token, signature_hex, load_public_key())
    if not valid_sig:
        return error_response

    # Check if token used
    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    if is_token_used(token_hash):
        return jsonify({"error": "Token has already been used"}), 403

    # Save vote and mark token as used
    store_vote_and_token(token_hash, ciphertext, exponent)

    return jsonify({"message": "✅ Vote cast successfully."}), 200
