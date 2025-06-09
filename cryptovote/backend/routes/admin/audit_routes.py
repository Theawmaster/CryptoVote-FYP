from flask import Blueprint, session, request
from services.audit_service import perform_audit_report, perform_tally
from utilities.auth_utils import role_required

audit_bp = Blueprint('audit_bp', __name__)

@audit_bp.route("/audit-report/<election_id>")
@role_required("admin")
def audit_report(election_id):
    return perform_audit_report(election_id, session["email"], request.remote_addr)

@audit_bp.route("/tally-election/<election_id>", methods=["POST"])
@role_required("admin")
def tally_election(election_id):
    return perform_tally(election_id, session["email"], request.remote_addr)
