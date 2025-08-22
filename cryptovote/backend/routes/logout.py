# routes/logout.py
from flask import Blueprint, request, session
from models.voter import Voter
from models.db import db
import hashlib
from datetime import datetime, timezone

logout_bp = Blueprint("logout", __name__)

def _flip_flags(email_hash: str) -> bool:
    """Idempotently set login flags to False. Returns True if a row existed."""
    v = Voter.query.filter_by(email_hash=email_hash).first()
    if not v:
        return False
    if v.logged_in or getattr(v, "logged_in_2fa", False):
        v.logged_in = False
        v.logged_in_2fa = False
        # optional: audit
        setattr(v, "last_logout_at", datetime.now(timezone.utc))
        db.session.commit()
    return True

@logout_bp.route("", methods=["POST"])
@logout_bp.route("/", methods=["POST"])
def logout():
    """
    Idempotent logout for both admin and voter.
    - Prefer the session to identify the user.
    - Optional fallback: JSON {"email": "..."} if session is absent.
    - Always clears the session.
    - Returns 204 (no body) for beacon-friendly calls.
    """
    # 1) try session first (works for both voter/admin)
    email_hash = session.get("email") or session.get("email_hash")

    # 2) optional body fallback if there is no session
    if not email_hash:
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip()
        if email:
            email_hash = hashlib.sha256(email.encode()).hexdigest()

    try:
        if email_hash:
            _flip_flags(email_hash)
        # no else: if we can't identify, we still clear session and return 204
        return ("", 204)
    finally:
        session.clear()
