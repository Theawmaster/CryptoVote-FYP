from flask import Blueprint, request, jsonify, session
from models.voter import Voter
from models.db import db
import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo

SGT = ZoneInfo("Asia/Singapore")

logout_bp = Blueprint('logout', __name__)

@logout_bp.route('/', methods=['POST'])
def logout():
    data = request.get_json()
    email = data.get("email")

    # Clear session if admin
    if session.get("role") == "admin":
        session.clear()
        print(f"🔓 Admin logout at {datetime.now(SGT)}")
        return jsonify({"message": "Admin logout successful."}), 200

    # Else handle voter logout
    if not email:
        return jsonify({"error": "Email is required"}), 400

    email_hash = hashlib.sha256(email.encode()).hexdigest()
    voter = Voter.query.filter_by(email_hash=email_hash).first()

    if not voter:
        return jsonify({"error": "User not found"}), 404

    if not voter.logged_in:
        return jsonify({"message": "User already logged out."}), 200

    try:
        voter.logged_in = False
        voter.logged_in_2fa = False
        db.session.commit()
        print(f"🔓 Voter logout for {email_hash} at {datetime.now(SGT)}")
        return jsonify({"message": "Logout successful."}), 200
    except Exception as e:
        db.session.rollback()
        print(f"❌ Logout DB update failed: {e}")
        return jsonify({"error": "Logout failed due to server error."}), 500
