from flask import Blueprint, request, jsonify
from models.db import db
from models.issued_token import IssuedToken
from models.voter import Voter
from utilities.blind_signature_utils import sign_blinded_token
import hashlib
from datetime import datetime

blind_sign_bp = Blueprint('blind_sign', __name__)

@blind_sign_bp.route('/blind-sign', methods=['POST'])
def blind_sign():
    data = request.get_json()
    email = data.get("email")
    blinded_token_hex = data.get("blinded_token")

    if not email or not blinded_token_hex:
        return jsonify({"error": "Email and blinded_token are required"}), 400

    email_hash = hashlib.sha256(email.encode()).hexdigest()
    voter = Voter.query.filter_by(email_hash=email_hash).first()

    if not voter or not voter.is_verified or not voter.logged_in:
        return jsonify({"error": "Unauthorized"}), 403

    # ✅ Prevent duplicate token issuance
    if voter.has_token:
        return jsonify({"error": "Token already issued for this voter"}), 403

    try:
        # Blind signature generation
        blinded_int = int(blinded_token_hex, 16)
        signed_blinded_int = sign_blinded_token(blinded_int)
        signed_blinded_hex = hex(signed_blinded_int)[2:]

        # Generate deterministic but irreversible issuance token hash
        issued_time = datetime.utcnow()
        fingerprint = email + issued_time.isoformat()
        token_hash = hashlib.sha256(fingerprint.encode()).hexdigest()

        # Update voter's status + log issuance
        voter.has_token = True
        issued = IssuedToken(
            token_hash=token_hash,
            used=False,
            issued_at=issued_time
        )
        db.session.add(issued)
        db.session.commit()

        return jsonify({"signed_blinded_token": signed_blinded_hex}), 200

    except Exception as e:
        return jsonify({"error": f"Signing failed: {str(e)}"}), 500
