from functools import wraps
from flask import session, redirect, url_for, jsonify
from models.voter import Voter
from models.db import db

def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            user_email = session.get("email")
            if not user_email:
                return jsonify({"error": "Authentication required"}), 401

            voter = db.session.query(Voter).filter_by(email_hash=user_email).first()
            if not voter or voter.vote_role != required_role:
                return jsonify({"error": f"{required_role.capitalize()} role required"}), 403
            
            if "role" not in session or session["role"] != required_role:
                return jsonify({"error": "Unauthorized access. Admins only."}), 403

            return f(*args, **kwargs)
        return wrapped
    return decorator

