# utilities/session_utils.py
from flask import request, jsonify, session
from time import time
from models.db import db
from models.voter import Voter

DEFAULT_IDLE_TTL_SECS = 2 * 60
DEFAULT_ABS_TTL_SECS  = 8 * 60 * 60

PUBLIC_PATHS = {
    "/login", "/admin-login", "/logout/", "/2fa-verify",
    "/public-keys", "/healthz",
    # NOTE: DO NOT put /session/status here (we want 401 when expired)
}

# Endpoints that must NOT roll idle
NO_IDLE_TOUCH = { "/session/status", "/auth/voter", "/auth/admin", "/onboarding" }

# Header to mark background polls (won’t roll idle)
BACKGROUND_POLL_HEADER = "X-Background-Poll"

def _now() -> int: return int(time())

def _is_public(path: str) -> bool:
    if path in PUBLIC_PATHS: return True
    if path.startswith("/static/") or path.startswith("/assets/"): return True
    return False

def _expire(reason: str, code=401):
    try:
            email_hash = session.get("email")
            if email_hash:
                user = Voter.query.filter_by(email_hash=email_hash).first()
                if user:
                    user.logged_in = False
                    user.logged_in_2fa = False
                    db.session.commit()
    except Exception:
        db.session.rollback()
    finally:
        session.clear()

    return jsonify({"error": reason, "code": code}), code

def register_session_ttl(app, idle_ttl=DEFAULT_IDLE_TTL_SECS, abs_ttl=DEFAULT_ABS_TTL_SECS):
    @app.before_request
    def _enforce_ttl():
        if _is_public(request.path):
            return None
        if "email" not in session:
            return None

        now       = _now()
        created   = int(session.get("sess_created_at", now))
        last_seen = int(session.get("sess_last_seen",  now))

        if abs_ttl and now >= created + abs_ttl:
            return _expire("absolute_session_expired", 401)
        if idle_ttl and now >= last_seen + idle_ttl:
            return _expire("idle_session_expired", 401)

        # Only roll idle if this is NOT a “no-touch” endpoint and NOT a background poll
        path = (request.path or "").rstrip("/")
        is_no_touch = path in NO_IDLE_TOUCH
        is_bg_poll  = request.headers.get(BACKGROUND_POLL_HEADER) == "1"
        if not is_no_touch and not is_bg_poll:
            session["sess_last_seen"] = now
        return None

    @app.get("/session/status")
    def session_status():
        now = _now()
        if "email" not in session:
            return jsonify({"logged_in": False}), 200
        created   = int(session.get("sess_created_at", now))
        last_seen = int(session.get("sess_last_seen",  now))
        return jsonify({
            "logged_in": True,
            "server_now": now,
            "idle_remaining":     max(0, (last_seen + idle_ttl) - now),
            "absolute_remaining": max(0, (created   + abs_ttl)  - now),
            "warn_after_secs": 120,   # give a bigger window; more reliable with tab throttling
        }), 200

    @app.post("/session/ping")
    def session_ping():
        if "email" not in session:
            return _expire("not_logged_in")
        session["sess_last_seen"] = _now()
        return jsonify({"ok": True}), 200
