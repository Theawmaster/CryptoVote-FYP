from flask import Blueprint, request, jsonify
from models.db import db
from models.encrypted_vote import EncryptedVote
from models.issued_token import IssuedToken
from services.blind_signature_utils import load_public_key, verify_signed_token
import hashlib
from datetime import datetime

cast_vote_bp = Blueprint('cast_vote', __name__)

def is_valid_hex(s):
    try:
        int(s, 16)
        return True
    except ValueError:
        return False

@cast_vote_bp.route('/cast-vote', methods=['POST'])
def cast_vote():
    data = request.get_json()
    token = data.get("token")
    signature_hex = data.get("signature")
    ciphertext = data.get("ciphertext")
    exponent = data.get("exponent")

    if not token or not signature_hex or not ciphertext or exponent is None:
        return jsonify({"error": "Missing fields"}), 400

    signature_hex = signature_hex.strip()
    if not is_valid_hex(signature_hex):
        return jsonify({"error": "Signature must be a valid hex string"}), 400

    try:
        signature_int = int(signature_hex, 16)
    except ValueError:
        return jsonify({"error": "Failed to parse signature as hex"}), 400

    token_bytes = token.encode()
    token_hash = hashlib.sha256(token_bytes).hexdigest()

    # Step 1: Verify signature
    pubkey = load_public_key()
    is_valid = verify_signed_token(pubkey, token_bytes, signature_int)
    if not is_valid:
        return jsonify({"error": "Invalid signature"}), 403

    # Step 2: Check if this token has been used before
    existing = IssuedToken.query.filter_by(token_hash=token_hash).first()
    if existing:
        return jsonify({"error": "Token has already been used"}), 403

    # Step 3: Save the vote
    vote = EncryptedVote(
        token_hash=token_hash,
        vote_ciphertext=ciphertext,
        vote_exponent=exponent,
        cast_at=datetime.utcnow()
    )
    db.session.add(vote)

    # Step 4: Log this token hash as now used (no link to email!)
    issued = IssuedToken(              # Privacy preserved
        token_hash=token_hash,
        used=True,
        issued_at=datetime.utcnow()
    )
    db.session.add(issued)

    db.session.commit()

    return jsonify({"message": "✅ Vote cast successfully."}), 200

# For postman testing
# {
#   "token": "original_random_token",  // used to derive token_hash
#   "signature": "deadbeef...",        // hex of signed token (r from blind.py)
#   "ciphertext": "99326490234823048230423...", // paillier ciphertext (// from encrypt_demo.py but run generate_paiallier_keypair.py first)  
#   "exponent": .. // from encrypt_demo.py
# }