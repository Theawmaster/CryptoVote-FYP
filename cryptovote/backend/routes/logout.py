# from flask import Blueprint, jsonify, session
# from models.voter import Voter
# from models.db import db

# logout_bp = Blueprint("logout", __name__)

# @logout_bp.route("", methods=["POST"])
# @logout_bp.route("/", methods=["POST"])
# def logout():
#     """
#     Idempotent logout:
#     - If we know who you are, flip DB flags to False.
#     - Always clear the session.
#     - Return 204 so it's cheap for sendBeacon/keepalive.
#     """
#     email_hash = session.get("email")

#     if email_hash:
#         voter = Voter.query.filter_by(email_hash=email_hash).first()
#         if voter:
#             try:
#                 # Only change if needed; keeps it idempotent and reduces writes
#                 if voter.logged_in or voter.logged_in_2fa:
#                     voter.logged_in = False
#                     voter.logged_in_2fa = False
#                     db.session.commit()
#             except Exception:
#                 db.session.rollback()
#                 # we still clear the session below regardless

#     session.clear()
#     # 204 = No Content (ideal for fire-and-forget)
#     return ("Logged out successfully!", 204)

# Version 1.0
from flask import Blueprint, request, jsonify, session
from models.voter import Voter
from models.db import db
import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo

SGT = ZoneInfo("Asia/Singapore")
logout_bp = Blueprint('logout', __name__)

def _logout_voter_by_hash(email_hash: str):
    """Set login flags to False for a voter row if it exists. Idempotent."""
    voter = Voter.query.filter_by(email_hash=email_hash).first()
    if not voter:
        return False  # caller can decide how to respond

    if voter.logged_in or getattr(voter, "logged_in_2fa", False):
        voter.logged_in = False
        voter.logged_in_2fa = False
        db.session.commit()
    return True

@logout_bp.route('/', methods=['POST'])
def logout():
    # ---------- Admin path (session-based) ----------
    if session.get("role") == "admin":
        admin_hash = session.get("email")
        try:
            if admin_hash:
                # Also flip DB flags for admin's voter row, if present
                _logout_voter_by_hash(admin_hash)
            print("Logout session (admin):", dict(session))
            session.clear()
            print(f"🔓 Admin logout at {datetime.now(SGT)}")
            return jsonify({"message": "Admin logout successful."}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Admin logout failed: {e}"}), 500

    # ---------- Voter path (email required) ----------
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    if not email:
        return jsonify({"error": "Email is required"}), 400

    email_hash = hashlib.sha256(email.encode()).hexdigest()
    voter = Voter.query.filter_by(email_hash=email_hash).first()
    if not voter:
        return jsonify({"error": "User not found"}), 404

    if not voter.logged_in and not getattr(voter, "logged_in_2fa", False):
        return jsonify({"message": "User already logged out."}), 200

    try:
        voter.logged_in = False
        voter.logged_in_2fa = False
        session.clear()
        db.session.commit()
        print(f"🔓 Voter logout for {email_hash} at {datetime.now(SGT)}")
        return jsonify({"message": "Logout successful."}), 200
    except Exception as e:
        db.session.rollback()
        print(f"❌ Logout DB update failed: {e}")
        return jsonify({"error": "Logout failed due to server error."}), 500
