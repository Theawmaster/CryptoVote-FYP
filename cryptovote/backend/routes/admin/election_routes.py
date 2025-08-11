# routes/election_routes.py
from flask import Blueprint, request, jsonify, session
from models.election import Election
from utilities.anomaly_utils import flag_suspicious_activity
from services.election_service import (
    start_election_by_id, end_election_by_id, get_election_status_by_id, create_new_election
)
from utilities.auth_utils import role_required

election_bp = Blueprint('election_bp', __name__)

@election_bp.route("/start-election/<election_id>", methods=["POST"])
@role_required("admin")
def start_election(election_id):
    admin_email = session.get("email")
    return start_election_by_id(election_id, admin_email, request.remote_addr)

@election_bp.route("/end-election/<election_id>", methods=["POST"])
@role_required("admin")
def end_election(election_id):
    admin_email = session.get("email")
    return end_election_by_id(election_id, admin_email, request.remote_addr)

@election_bp.route("/election-status/<election_id>", methods=["GET"])
@role_required("admin")
def election_status(election_id):
    admin_email = session.get("email")
    return get_election_status_by_id(election_id, admin_email, request.remote_addr)

@election_bp.route("/create-election", methods=["POST"])
@role_required("admin")
def create_election():
    data = request.get_json() or {}
    # Expecting payload like: {"id": "...", "name": "..."}
    missing = [k for k in ("id", "name") if not data.get(k)]
    if missing:
        return jsonify({"error": f"Missing required field: {missing[0]}"}), 400

    admin_email = session.get("email")
    return create_new_election(data, admin_email, request.remote_addr)

@election_bp.route("/elections", methods=["GET"])
@role_required("admin")
def list_elections():
    # If you’ve got a service, call it here instead of hitting the model directly
    rows = Election.query.order_by(Election.created_at.desc()).all()
    
    def to_dict(e):
        return {
            "id": e.id,
            "name": e.name,
            "start_time": e.start_time.isoformat() if e.start_time else None,
            "end_time": e.end_time.isoformat() if e.end_time else None,
            "is_active": e.is_active,
            "has_started": e.has_started,
            "has_ended": e.has_ended,
            "tally_generated": e.tally_generated,
        }
    return jsonify({"elections": [to_dict(e) for e in rows]})