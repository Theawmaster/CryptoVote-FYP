from flask import Blueprint, request, jsonify
from models.voter import Voter
from models.db import db
import hashlib

logout_bp = Blueprint('logout', __name__)

@logout_bp.route('/', methods=['POST'])
def logout():
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email is required"}), 400

    email_hash = hashlib.sha256(email.encode()).hexdigest()
    voter = Voter.query.filter_by(email_hash=email_hash).first()

    if not voter or not voter.logged_in:
        return jsonify({"error": "User not logged in or does not exist"}), 403

    voter.logged_in = False
    db.session.commit()

    return jsonify({"message": "Logout successful."}), 200
