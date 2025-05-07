import hashlib, secrets
from flask import jsonify
from models.voter import Voter
from models.db import db
from services.email_service import send_verification_email
from services.crypto_utils import generate_rsa_key_pair

def handle_registration(email: str):
    if not email.endswith("@e.ntu.edu.sg"):
        return jsonify({"error": "Invalid email domain"}), 400

    email_hash = hashlib.sha256(email.encode()).hexdigest()
    voter = Voter.query.filter_by(email_hash=email_hash).first()

    # Case 1: Already registered
    if voter:
        if voter.is_verified:
            return jsonify({"message": "Email already verified. Please proceed to login."}), 200
        else:
            try:
                voter.verification_token = secrets.token_urlsafe(32)
                db.session.commit()
                send_verification_email(email, voter.verification_token)
                return jsonify({
                    "message": "Email already registered but not verified. A new verification token has been sent."
                }), 200
            except Exception as e:
                db.session.rollback()
                print(f"[ERROR] Failed to resend verification: {e}")
                return jsonify({"error": "Internal error occurred"}), 500

    # Case 2: New registration
    try:
        public_key, private_key = generate_rsa_key_pair()
        token = secrets.token_urlsafe(32)

        new_voter = Voter(
            email_hash=email_hash,
            verification_token=token,
            public_key=public_key
        )

        db.session.add(new_voter)
        db.session.commit()
        send_verification_email(email, token)

        return jsonify({
            "message": "Verification email sent. Please securely store your private key.",
            "private_key": private_key  # Frontend should prompt user to save this
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Failed to register new voter: {e}")
        return jsonify({"error": "Internal error occurred"}), 500
