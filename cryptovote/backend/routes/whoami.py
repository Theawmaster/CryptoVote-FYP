# routes/whoami.py
from flask import Blueprint, jsonify, session
from datetime import timezone
from zoneinfo import ZoneInfo
from models.voter import Voter
from models import db  # your SQLAlchemy instance

SGT = ZoneInfo("Asia/Singapore")

def _iso_in_tz(dt, tz):
    if not dt:
        return None
    # if DB stored naive, treat as UTC; adjust if your DB stores local
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(tz).isoformat()

whoami_bp = Blueprint("whoami", __name__)

@whoami_bp.get("/whoami")
def whoami():
    email_hash = session.get("email") or session.get("email_hash")
    role  = session.get("role")
    twofa = bool(session.get("twofa"))

    voter = Voter.query.filter_by(email_hash=email_hash).first() if email_hash else None
    last = getattr(voter, "last_login_at", None)
    ip   = getattr(voter, "last_login_ip", None)

    return jsonify({
        "role": role,
        "twofa": twofa,
        "email_hash": email_hash,
        # UTC and SGT (+08:00)
        "last_login_at": _iso_in_tz(last, timezone.utc),     # e.g. 2025-08-22T02:37:11Z
        "last_login_at_sgt": _iso_in_tz(last, SGT),          # e.g. 2025-08-22T10:37:11+08:00
        "last_login_ip": ip,
    }), 200
