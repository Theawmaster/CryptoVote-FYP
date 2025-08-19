from flask import Blueprint, jsonify, session
from utilities.auth_utils import role_required
from models.voter import Voter

bp_me = Blueprint("admin_me", __name__)  

@bp_me.get("/me")
@role_required("admin")
def admin_me():
    email_hash = session.get("email")
    if not email_hash:
        return jsonify({"error": "Not authenticated"}), 401

    v = Voter.query.filter_by(email_hash=email_hash).first()
    if not v or v.vote_role != "admin":
        return jsonify({"error": "Not an admin"}), 403

    return jsonify({
        "role": v.vote_role,
        "last_login_at": v.last_login_at.isoformat() if v.last_login_at else None,
        "last_login_ip": v.last_login_ip,
        "last_2fa_at": v.last_2fa_at.isoformat() if v.last_2fa_at else None,
    }), 200
