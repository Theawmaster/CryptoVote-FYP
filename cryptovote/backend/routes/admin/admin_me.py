from flask import Blueprint, jsonify, session
from datetime import timezone
from utilities.auth_utils import role_required
from models.voter import Voter

bp_me = Blueprint("admin_me", __name__)

def to_iso_utc(dt):
    """Serialize a datetime as ISO-8601 UTC with a trailing 'Z'."""
    if not dt:
        return None
    if dt.tzinfo is None:
        # treat stored naive datetimes as UTC (adjust if your DB stores local)
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")

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
        "last_login_at": to_iso_utc(v.last_login_at),
        "last_login_ip": v.last_login_ip,
        "last_2fa_at": to_iso_utc(v.last_2fa_at),
    }), 200
