from flask import Blueprint, request, jsonify, session
from services.election_service import start_election_by_id, end_election_by_id, get_election_status_by_id
from utilities.auth_utils import role_required

election_bp = Blueprint('election_bp', __name__)

@election_bp.route("/start-election/<election_id>", methods=["POST"])
@role_required("admin")
def start_election(election_id):
    return start_election_by_id(election_id, session["email"], request.remote_addr)

@election_bp.route("/end-election/<election_id>", methods=["POST"])
@role_required("admin")
def end_election(election_id):
    return end_election_by_id(election_id, session["email"], request.remote_addr)

@election_bp.route("/election-status/<election_id>", methods=["GET"])
@role_required("admin")
def election_status(election_id):
    return get_election_status_by_id(election_id, session["email"], request.remote_addr)
