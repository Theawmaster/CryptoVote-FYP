import hashlib, secrets, base64, os
from flask import jsonify
from models.voter import Voter
from models.db import db
from services.email_service import send_verification_email
from utilities.crypto_utils import generate_rsa_key_pair
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


def handle_registration(email: str, vote_role="voter"):

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
        private_key, public_key = generate_rsa_key_pair(save_to_disk=True)
        token = secrets.token_urlsafe(32)

        new_voter = Voter(
            email_hash=email_hash,
            verification_token=token,
            public_key=public_key,
            vote_role=vote_role
        )

        db.session.add(new_voter)
        db.session.commit()
        send_verification_email(email, token)

        return jsonify({
            "message": "Verification email sent. Please securely store your private key.",
            "private_key": private_key
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Failed to register new voter: {e}")
        return jsonify({"error": "Internal error occurred"}), 500

# Signature Verification Function
def verify_voter_signature(email: str, signed_nonce_b64: str, nonce: str):
    try:
        email_hash = hashlib.sha256(email.encode()).hexdigest()
        voter = Voter.query.filter_by(email_hash=email_hash).first()

        if not voter:
            return False, "Voter not found"

        public_key = serialization.load_pem_public_key(voter.public_key.encode())
        signed_nonce = base64.b64decode(signed_nonce_b64)

        public_key.verify(
            signed_nonce,
            nonce.encode(),
            padding.PKCS1v15(),
            hashes.SHA256()
        )

        return True, "Signature verified"

    except Exception as e:
        print(f"[AUTH ERROR] Signature verification failed: {e}")
        return False, "Invalid signature"

# Generate Nonce Function
def generate_nonce(length=32):
    return base64.b64encode(os.urandom(length)).decode('utf-8')