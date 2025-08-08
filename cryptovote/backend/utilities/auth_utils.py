# utilities/auth_utils.py
from functools import wraps
from flask import session, jsonify

def role_required(required_role: str):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            role = session.get("role")
            twofa = session.get("twofa")
            if role != required_role or not twofa:
                return jsonify({"error": "Admin access required"}), 403
            return f(*args, **kwargs)
        return wrapped
    return decorator
