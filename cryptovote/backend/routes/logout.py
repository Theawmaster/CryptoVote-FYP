from flask import Blueprint, request, jsonify, session
from models.voter import Voter
from models.db import db

logout_bp = Blueprint('logout', __name__)

@logout_bp.route('/', methods=['POST'])
def logout():
    # Prefer fully authenticated identity; fall back to pending if you ever store it
    email_hash = session.get('email')
    if email_hash:
        voter = Voter.query.filter_by(email_hash=email_hash).first()
        if voter:
            try:
                voter.logged_in = False
                voter.logged_in_2fa = False
                db.session.commit()
            except Exception:
                db.session.rollback()

    session.clear()
    return jsonify({'message': 'Logout successful.'}), 200

# Version 1.0
# routes/logout.py
# from flask import Blueprint, request, jsonify, session
# from models.voter import Voter
# from models.db import db
# import hashlib
# from datetime import datetime
# from zoneinfo import ZoneInfo

# SGT = ZoneInfo("Asia/Singapore")
# logout_bp = Blueprint('logout', __name__)

# def _logout_voter_by_hash(email_hash: str):
#     """Set login flags to False for a voter row if it exists. Idempotent."""
#     voter = Voter.query.filter_by(email_hash=email_hash).first()
#     if not voter:
#         return False  # caller can decide how to respond

#     if voter.logged_in or getattr(voter, "logged_in_2fa", False):
#         voter.logged_in = False
#         voter.logged_in_2fa = False
#         db.session.commit()
#     return True

# @logout_bp.route('/', methods=['POST'])
# def logout():
#     # ---------- Admin path (session-based) ----------
#     if session.get("role") == "admin":
#         admin_hash = session.get("email")
#         try:
#             if admin_hash:
#                 # Also flip DB flags for admin's voter row, if present
#                 _logout_voter_by_hash(admin_hash)
#             print("Logout session (admin):", dict(session))
#             session.clear()
#             print(f"🔓 Admin logout at {datetime.now(SGT)}")
#             return jsonify({"message": "Admin logout successful."}), 200
#         except Exception as e:
#             db.session.rollback()
#             return jsonify({"error": f"Admin logout failed: {e}"}), 500

#     # ---------- Voter path (email required) ----------
#     data = request.get_json(silent=True) or {}
#     email = data.get("email")
#     if not email:
#         return jsonify({"error": "Email is required"}), 400

#     email_hash = hashlib.sha256(email.encode()).hexdigest()
#     voter = Voter.query.filter_by(email_hash=email_hash).first()
#     if not voter:
#         return jsonify({"error": "User not found"}), 404

#     if not voter.logged_in and not getattr(voter, "logged_in_2fa", False):
#         return jsonify({"message": "User already logged out."}), 200

#     try:
#         voter.logged_in = False
#         voter.logged_in_2fa = False
#         session.clear()
#         db.session.commit()
#         print(f"🔓 Voter logout for {email_hash} at {datetime.now(SGT)}")
#         return jsonify({"message": "Logout successful."}), 200
#     except Exception as e:
#         db.session.rollback()
#         print(f"❌ Logout DB update failed: {e}")
#         return jsonify({"error": "Logout failed due to server error."}), 500
