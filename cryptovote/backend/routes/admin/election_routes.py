import email
from flask import Blueprint, request, jsonify, session
from cryptovote.backend.utilities.anomaly_utils import flag_suspicious_activity
from services.election_service import start_election_by_id, end_election_by_id, get_election_status_by_id, create_new_election
from utilities.auth_utils import role_required

election_bp = Blueprint('election_bp', __name__)

@election_bp.route("/start-election/<election_id>", methods=["POST"])
@role_required("admin")
def start_election(election_id):
    if "role" not in session or session["role"] != "admin":
        flag_suspicious_activity(email, request.remote_addr, "Logged out admin accessed restricted route", request.path)
        return jsonify({"error": "Unauthorized. Admin login required."}), 403

    admin_email = session.get("email")
    return start_election_by_id(election_id, admin_email, request.remote_addr)


@election_bp.route("/end-election/<election_id>", methods=["POST"])
@role_required("admin")
def end_election(election_id):
    if "role" not in session or session["role"] != "admin":
        flag_suspicious_activity(email, request.remote_addr, "Logged out admin accessed restricted route", request.path)
        return jsonify({"error": "Unauthorized. Admin login required."}), 403

    admin_email = session.get("email")
    return end_election_by_id(election_id, admin_email, request.remote_addr)

@election_bp.route("/election-status/<election_id>", methods=["GET"])
@role_required("admin")
def election_status(election_id):
    if "role" not in session or session["role"] != "admin":
        flag_suspicious_activity(email, request.remote_addr, "Logged out admin accessed restricted route", request.path)
        return jsonify({"error": "Unauthorized. Admin login required."}), 403

    admin_email = session.get("email")
    return get_election_status_by_id(election_id, admin_email, request.remote_addr)

@election_bp.route("/create-election", methods=["POST"])
@role_required("admin")
def create_election():
    if "role" not in session or session["role"] != "admin":
        flag_suspicious_activity(email, request.remote_addr, "Logged out admin accessed restricted route", request.path)
        return jsonify({"error": "Unauthorized. Admin login required."}), 403

    admin_email = session.get("email")
    return create_new_election(election_id, admin_email, request.remote_addr)

