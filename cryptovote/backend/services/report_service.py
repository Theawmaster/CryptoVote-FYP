from flask import jsonify, send_file
from datetime import datetime
from models.db import db
from models.election import Election
from services.tallying_service import tally_votes
from utilities.audit_utils import generate_all_zkp_proofs
from utilities.logger_utils import log_admin_action
from fpdf import FPDF
import csv, io, os

def generate_report_file(election_id, format_type, admin_email, ip_addr):
    try:
        election = db.session.query(Election).filter_by(id=election_id).first()
        if not election:
            return jsonify({"error": "Election not found"}), 404

        tally_result = tally_votes(db.session)
        zkp_proofs = generate_all_zkp_proofs(tally_result, election_id)

        if format_type == "csv":
            return generate_csv_report(election_id, tally_result, zkp_proofs, admin_email, ip_addr)
        elif format_type == "pdf":
            return generate_pdf_report(election_id, tally_result, zkp_proofs, admin_email, ip_addr)
        else:
            return jsonify({"error": "Unsupported format. Use 'csv' or 'pdf'."}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def generate_csv_report(election_id, tally, zkp_proofs, admin_email, ip_addr):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Candidate ID", "Vote Count", "Salt", "Commitment"])
    for row in zkp_proofs:
        writer.writerow([
            row["candidate_id"],
            row["vote_count"],
            row["salt"],
            row["commitment"]
        ])

    log_admin_action("download_report_csv", admin_email, "admin", ip_addr)

    buffer = io.BytesIO()
    buffer.write(output.getvalue().encode())
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"audit_report_{election_id}.csv",
        mimetype='text/csv'
    )

def generate_pdf_report(election_id, tally, zkp_proofs, admin_email, ip_addr):
    pdf = FPDF()
    pdf.add_page()

    logo_path = "assets/ntu_logo.png"
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=10, y=8, w=50)

    pdf.set_xy(10, 35)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt=f"Audit Report for Election: {election_id}", ln=True, align='C')

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    pdf.set_font("Arial", '', 10)
    pdf.cell(200, 10, txt=f"Generated on: {timestamp}", ln=True, align='C')
    pdf.ln(8)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Vote Tally:", ln=True)
    pdf.set_font("Arial", '', 10)
    for row in tally:
        pdf.cell(200, 8, txt=f"Candidate {row['candidate_id']}: {row['vote_count']} votes", ln=True)

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

    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    buffer = io.BytesIO(pdf_bytes)

    log_admin_action("download_report_pdf", admin_email, "admin", ip_addr)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"audit_report_{election_id}.pdf",
        mimetype='application/pdf'
    )
