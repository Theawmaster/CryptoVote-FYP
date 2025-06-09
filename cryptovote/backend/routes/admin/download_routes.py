from flask import Blueprint, request, session
from services.report_service import generate_report_file
from utilities.auth_utils import role_required

download_bp = Blueprint("download_bp", __name__)

@download_bp.route("/download-report/<election_id>", methods=["GET"])
@role_required("admin")
def download_report(election_id):
    format_type = request.args.get("format", "csv")  # ?format=pdf or csv
    return generate_report_file(election_id, format_type, session["email"], request.remote_addr)
