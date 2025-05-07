from flask import Blueprint, request
from services.registration_service import handle_registration
from models.voter import db, Voter
from flask import jsonify

register_bp = Blueprint('register', __name__)

@register_bp.route('/', methods=['POST'])
def register():
    data = request.json
    email = data.get("email")
    return handle_registration(email)

@register_bp.route('/verify-email')
def verify_email():
    token = request.args.get("token")
    voter = Voter.query.filter_by(verification_token=token).first()
    if not voter:
        return jsonify({"error": "Invalid token"}), 400

    voter.is_verified = True
    db.session.commit()
    return jsonify({"message": "Email verified successfully."})
