# routes/whoami.py
from flask import Blueprint, jsonify, session

whoami_bp = Blueprint("whoami_bp", __name__)

@whoami_bp.route("/whoami", methods=["GET"])
def whoami():
    return jsonify({
        "email": session.get("email"),
        "role": session.get("role"),
        "twofa": session.get("twofa", False),
    }), 200
