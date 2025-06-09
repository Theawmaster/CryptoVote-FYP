from flask import Blueprint, jsonify, render_template, session, request
from services.tallying_service import tally_votes
from utilities.audit_utils import generate_all_zkp_proofs
from utilities.auth_utils import role_required  
from utilities.logger_utils import log_admin_action 
from models.db import db
from models.election import Election
from datetime import datetime

import base64, io, os
from flask import send_file
from fpdf import FPDF

admin_bp = Blueprint('admin', __name__)

# Optional dev-login for testing
# @admin_bp.route("/dev-login-admin")
# def dev_login_as_admin():
#     session["email"] = "admin@ntu.edu.sg"
#     session["role"] = "admin"
#     return jsonify({
#         "message": "🧪 Dev session as admin created.",
#         "session": dict(session)
#     }), 200

# ====== ADMIN DASHBOARD ======
@admin_bp.route("/audit-report/<election_id>")
@role_required("admin")
def audit_report(election_id):
    try:
        election = db.session.query(Election).filter_by(id=election_id).first()
        if not election:
            return jsonify({"error": "Election not found"}), 404

        tally_result = tally_votes(db.session)
        zkp_proofs = generate_all_zkp_proofs(tally_result, election_id)

        try:
            log_admin_action("tally_votes", session["email"], "admin", request.remote_addr)
        except Exception as e:
            print("⚠️ Logging failed:", e)

        return jsonify({
            "election_id": election_id,
            "tally": tally_result,
            "zkp_proofs": list(zkp_proofs),
            "verifier_link": "/admin/verify-proof"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ====== START ELECTION ======
@admin_bp.route("/start-election/<election_id>", methods=["POST"])
@role_required("admin")
def start_election(election_id):
    try:
        election = db.session.query(Election).filter_by(id=election_id).first()
        if not election:
            return jsonify({"error": "Election not found"}), 404

        if election.has_started:
            return jsonify({"message": "Election already started."}), 200

        election.has_started = True
        election.is_active = True
        if not election.start_time:
            election.start_time = datetime.utcnow()

        db.session.commit()
        log_admin_action("start_election", session["email"], "admin", request.remote_addr)
        return jsonify({"message": f"✅ Election '{election_id}' started."}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# ====== ELECTION STATUS ======
@admin_bp.route("/election-status/<election_id>", methods=["GET"])
@role_required("admin")
def election_status(election_id):
    election = db.session.query(Election).filter_by(id=election_id).first()
    if not election:
        return jsonify({"error": "Election not found"}), 404
    log_admin_action("election_status", session["email"], "admin", request.remote_addr)
    return jsonify({
        "election_id": election_id,
        "is_active": election.is_active,
        "has_started": election.has_started,
        "has_ended": election.has_ended,
        "start_time": election.start_time,
        "end_time": election.end_time
    }), 200

@admin_bp.route("/tally-election/<election_id>", methods=["POST"])
@role_required("admin")
def tally_election(election_id):
    try:
        # 🔍 Fetch election
        election = db.session.query(Election).filter_by(id=election_id).first()
        if not election:
            return jsonify({"error": "Election not found"}), 404
        if election.tally_generated:
            return jsonify({"error": "Tally already generated for this election."}), 400
        if not election.has_ended:
            return jsonify({"error": "Cannot tally before election ends."}), 400

        # ✅ Perform tally
        tally_result = tally_votes(db.session)
        zkp_proofs = generate_all_zkp_proofs(tally_result, election_id)

        # ✅ Update election metadata
        election.tally_generated = True
        db.session.commit()

        # 🧾 Log the admin action
        try:
            log_admin_action("tally_election", session["email"], "admin", request.remote_addr)
        except Exception as e:
            print("⚠️ Logging failed:", e)

        return jsonify({
            "message": "✅ Tally successful.",
            "election_id": election_id,
            "tally": tally_result,
            "zkp_proofs": list(zkp_proofs)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ====== END ELECTION ======
@admin_bp.route("/end-election/<election_id>", methods=["POST"])
@role_required("admin")
def end_election(election_id):
    try:
        election = db.session.query(Election).filter_by(id=election_id).first()
        if not election:
            return jsonify({"error": "Election not found"}), 404

        if election.has_ended:
            return jsonify({"message": "Election already ended."}), 200

        election.has_ended = True
        election.is_active = False
        if not election.end_time:
            election.end_time = datetime.utcnow()

        db.session.commit()
        log_admin_action("end_election", session["email"], "admin", request.remote_addr)
        return jsonify({"message": f"🛑 Election '{election_id}' ended."}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# ====== DOWNLOAD AUDIT REPORT ======    
@admin_bp.route("/download-report/<election_id>", methods=["GET"])
@role_required("admin")
def download_report(election_id):
    try:
        election = db.session.query(Election).filter_by(id=election_id).first()
        if not election:
            return jsonify({"error": "Election not found"}), 404

        # Get tally + ZKP
        tally_result = tally_votes(db.session)
        zkp_proofs = generate_all_zkp_proofs(tally_result, election_id)

        # Choose format
        format_type = request.args.get("format", "csv")  # ?format=pdf or csv

        if format_type == "csv":
            return generate_csv_report(election_id, tally_result, zkp_proofs)
        elif format_type == "pdf":
            return generate_pdf_report(election_id, tally_result, zkp_proofs)
        else:
            return jsonify({"error": "Unsupported format. Use 'csv' or 'pdf'."}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def generate_pdf_report(election_id, tally, zkp_proofs):
    pdf = FPDF()
    pdf.add_page()

    # Add NTU logo at top (ensure path is correct)
    logo_path = "assets/ntu_logo.png"  # Save the uploaded image to this location
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=10, y=8, w=50)

    # Move below image
    pdf.set_xy(10, 35)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt=f"Audit Report for Election: {election_id}", ln=True, align='C')

    pdf.set_font("Arial", '', 10)
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    pdf.cell(200, 10, txt=f"Generated on: {timestamp}", ln=True, align='C')
    pdf.ln(8)

    # Tally section
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Vote Tally:", ln=True)
    pdf.set_font("Arial", '', 10)
    for row in tally:
        pdf.cell(200, 8, txt=f"Candidate {row['candidate_id']}: {row['vote_count']} votes", ln=True)

    # ZKP section
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="ZKP Commitment Proofs:", ln=True)
    pdf.set_font("Arial", '', 10)
    for proof in zkp_proofs:
        pdf.multi_cell(0, 8, txt=(
            f"Candidate: {proof['candidate_id']}\n"
            f"Count: {proof['vote_count']}\n"
            f"Salt: {proof['salt']}\n"
            f"Commitment: {proof['commitment']}\n"
        ), border=1)
        pdf.ln(1)

    # Output as BytesIO
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    buffer = io.BytesIO(pdf_bytes)

    log_admin_action("download_report", session["email"], "admin", request.remote_addr)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"audit_report_{election_id}.pdf",
        mimetype='application/pdf'
    )
