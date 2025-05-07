import hashlib, secrets
from flask import jsonify
from models.voter import Voter
from models.db import db
from services.email_service import send_verification_email

def handle_registration(email: str):
    if not email.endswith("@e.ntu.edu.sg"):
        return jsonify({"error": "Invalid email domain"}), 400

    email_hash = hashlib.sha256(email.encode()).hexdigest()
    voter = Voter.query.filter_by(email_hash=email_hash).first()

    if voter:
        if voter.is_verified:
            return jsonify({"message": "Email already verified. Please proceed to login."}), 200
        else:
            # Update token and resend
            try:
                voter.verification_token = secrets.token_urlsafe(32)
                db.session.commit()
                send_verification_email(email, voter.verification_token)
                return jsonify({"message": "Email already registered but not verified. New verification sent."}), 200
            except Exception as e:
                db.session.rollback()
                print(f"[ERROR] Failed to update or send verification: {e}")
                return jsonify({"error": "Internal error occurred"}), 500

    # Register new voter
    token = secrets.token_urlsafe(32)
    new_voter = Voter(email_hash=email_hash, verification_token=token)

    try:
        db.session.add(new_voter)
        db.session.commit()
        send_verification_email(email, token)
        return jsonify({"message": "Verification email sent."}), 201
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Failed to register voter or send email: {e}")
        return jsonify({"error": "Internal error occurred"}), 500
