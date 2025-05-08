from flask import Blueprint, request, jsonify
from services.registration_service import generate_nonce, verify_voter_signature
from models.voter import Voter
from models.db import db
import hashlib
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

# In-memory nonce store (email_hash → { nonce, issued_at })
nonce_store = {}
NONCE_TTL_SECONDS = 300  # 5 minutes

@auth_bp.route('/authenticate', methods=['POST'])
def authenticate():
    data = request.get_json()
    email = data.get('email')
    signed_nonce = data.get('signed_nonce')

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    email_hash = hashlib.sha256(email.encode()).hexdigest()

    # 🔍 Check if voter exists
    voter = Voter.query.filter_by(email_hash=email_hash).first()
    if not voter or not voter.is_verified:
        return jsonify({'error': 'Unverified or unknown voter.'}), 403

    # 🧩 Step 1: Requesting nonce
    if not signed_nonce:
        if voter.is_signed:
            return jsonify({'message': 'You are already signed in.'}), 200

        nonce = generate_nonce()
        nonce_store[email_hash] = {
            'nonce': nonce,
            'issued_at': datetime.utcnow()
        }
        return jsonify({'nonce': nonce})

    # 🧩 Step 2: Verifying signed nonce
    record = nonce_store.get(email_hash)
    if not record:
        return jsonify({'error': 'Nonce not found or expired'}), 400

    if datetime.utcnow() - record['issued_at'] > timedelta(seconds=NONCE_TTL_SECONDS):
        del nonce_store[email_hash]
        return jsonify({'error': 'Nonce expired. Please retry authentication.'}), 403

    nonce = record['nonce']
    success, msg = verify_voter_signature(email, signed_nonce, nonce)

    if success:
        del nonce_store[email_hash]

        try:
            voter.is_signed = True
            db.session.commit()
            print(f"✅ [{datetime.utcnow()}] Signature verified for {email_hash}")
        except Exception as e:
            db.session.rollback()
            print(f"❌ DB update failed: {e}")
            return jsonify({'error': 'Verified but failed to update signature state.'}), 500

        return jsonify({'message': msg}), 200

    else:
        return jsonify({'error': msg}), 401
