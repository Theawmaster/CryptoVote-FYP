import os
from functools import wraps
from flask import session, jsonify, current_app, request

def role_required(role):
    def deco(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            # ---- DEV-ONLY BYPASS (optional) ----
            allow_bypass = (
                current_app.debug
                and os.getenv("ALLOW_DEV_ADMIN_BYPASS") == "1"
                and request.remote_addr in ("127.0.0.1", "::1")
                and request.headers.get("X-Bypass-Admin") == "1"
            )
            if allow_bypass:
                return fn(*args, **kwargs)
            # ---- Real checks ----
            if session.get('role') != role:
                return jsonify({'error': 'forbidden'}), 403
            if session.get('twofa') is not True:
                return jsonify({'error': '2fa_required'}), 403
            return fn(*args, **kwargs)
        return wrapped
    return deco
