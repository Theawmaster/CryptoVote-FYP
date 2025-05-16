from flask import Blueprint, request, jsonify
from services.auth_service import (
    get_email_hash, request_nonce, validate_nonce, clear_nonce
)
from services.registration_service import verify_voter_signature
from models.voter import Voter
from models.db import db
from datetime import datetime

auth_bp = Blueprint('login', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    signed_nonce = data.get('signed_nonce')

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    email_hash = get_email_hash(email)
    voter = Voter.query.filter_by(email_hash=email_hash).first()

    if not voter or not voter.is_verified:
        return jsonify({'error': 'Unverified or unknown voter.'}), 403

    if not signed_nonce:
        if voter.logged_in:
            return jsonify({'message': 'You are already signed in.'}), 200

        nonce = request_nonce(email_hash)
        return jsonify({'nonce': nonce})

    # Step 2: Validate and verify
    nonce, error = validate_nonce(email_hash)
    if error:
        return jsonify({'error': error}), 403

    success, msg = verify_voter_signature(email, signed_nonce, nonce)
    if not success:
        return jsonify({'error': msg}), 401

    clear_nonce(email_hash)

    try:
        voter.logged_in = True
        voter.last_login_ip = request.remote_addr
        voter.last_login_at = datetime.utcnow()
        db.session.commit()
        print(f"✅ [{datetime.utcnow()}] Login successful for {email_hash}")
        return jsonify({'message': 'Signature verified. Login successful.'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"❌ DB update failed: {e}")
        return jsonify({'error': 'Verified but failed to update signature state.'}), 500
