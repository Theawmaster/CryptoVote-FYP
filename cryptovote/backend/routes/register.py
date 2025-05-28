from flask import Blueprint, request
from services.registration_service import handle_registration
from models.voter import db, Voter
from flask import jsonify
import pyotp

register_bp = Blueprint('register', __name__)

@register_bp.route('/', methods=['POST'])
def register():
    data = request.json
    email = data.get("email")
    vote_role = data.get("vote_role", "voter")
    return handle_registration(email, vote_role)

@register_bp.route('/verify-email')
def verify_email():
    token = request.args.get("token")
    if not token:
        return jsonify({"error": "Verification token is missing"}), 400

    voter = Voter.query.filter_by(verification_token=token).first()
    if not voter:
        return jsonify({"error": "Invalid or expired token"}), 404

    # Update voter verification state
    voter.is_verified = True
    voter.verification_token = None
    voter.totp_secret = pyotp.random_base32()
    db.session.commit()

    # Create TOTP provisioning URI (for Google Authenticator)
    totp_uri = pyotp.TOTP(voter.totp_secret).provisioning_uri(
        name=f"{voter.email_hash}@cryptovote",
        issuer_name="CryptoVote"
    )

    return jsonify({
        "message": "Email verified successfully.",
        "totp_uri": totp_uri
    })
