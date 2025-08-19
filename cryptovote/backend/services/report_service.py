# services/report_service.py

from flask import jsonify, send_file
from datetime import datetime
from zoneinfo import ZoneInfo
from io import BytesIO, StringIO
import csv
import os

from models.db import db
from models.election import Election, Candidate
from services.tallying_service import tally_votes
from utilities.audit_utils import generate_all_zkp_proofs
from utilities.logger_utils import log_admin_action
from fpdf import FPDF


SGT = ZoneInfo("Asia/Singapore")


def _candidate_map_for_election(election_id: str) -> dict[str, str]:
    """
    Return {candidate_id: candidate_name} for this election.
    Falls back to the id if name missing.
    """
    rows = Candidate.query.filter_by(election_id=election_id).all()
    return {c.id: (c.name or c.id) for c in rows}


def generate_report_file(election_id, format_type, admin_email, ip_addr):
    """
    Build a CSV or PDF audit report for a specific election.
    """
    try:
        election = Election.query.filter_by(id=election_id).first()
        if not election:
            return jsonify({"error": "Election not found"}), 404

        # IMPORTANT: scope the tally to the requested election
        tally_result = tally_votes(db.session, election_id)  # <-- pass election_id
        zkp_proofs   = generate_all_zkp_proofs(tally_result, election_id)
        cand_map     = _candidate_map_for_election(election_id)

        if format_type and format_type.lower() == "csv":
            return _generate_csv_report(election, tally_result, zkp_proofs, cand_map, admin_email, ip_addr)
        elif not format_type or format_type.lower() == "pdf":
            return _generate_pdf_report(election, tally_result, zkp_proofs, cand_map, admin_email, ip_addr)
        else:
            return jsonify({"error": "Unsupported format. Use 'csv' or 'pdf'."}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _generate_csv_report(election: Election, tally: list[dict], zkp_proofs: list[dict],
                         cand_map: dict[str, str], admin_email: str, ip_addr: str):
    out = StringIO()
    w = csv.writer(out)

    # Header
    w.writerow(["Election ID", election.id])
    w.writerow(["Election Name", election.name])
    w.writerow(["Generated (SGT)", datetime.now(SGT).strftime("%Y-%m-%d %H:%M:%S %Z")])
    w.writerow([])

    # Tally section
    w.writerow(["Candidate ID", "Candidate Name", "Vote Count"])
    for row in tally:
        cid = str(row["candidate_id"])
        w.writerow([cid, cand_map.get(cid, cid), row["vote_count"]])

    w.writerow([])
    w.writerow(["ZKP Proofs"])
    w.writerow(["Candidate ID", "Candidate Name", "Count", "Salt", "Commitment"])
    for p in zkp_proofs:
        cid = str(p["candidate_id"])
        w.writerow([cid, cand_map.get(cid, cid), p["vote_count"], p["salt"], p["commitment"]])

    log_admin_action("download_report_csv", admin_email, "admin", ip_addr)

    buf = BytesIO(out.getvalue().encode("utf-8"))
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name=f"cryptovote-{election.id}-report.csv",
        mimetype="text/csv",
    )


def _generate_pdf_report(election: Election, tally: list[dict], zkp_proofs: list[dict],
                         cand_map: dict[str, str], admin_email: str, ip_addr: str):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Optional logo
    logo_path = "assets/ntu_logo.png"
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=10, y=8, w=50)

    # Title
    pdf.set_xy(10, 30)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 10, txt=f"Audit Report for Election: {election.id}", ln=True, align="C")
    pdf.set_font("Arial", "", 12)
    pdf.cell(190, 8, txt=f"Name: {election.name}", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 8, txt=f"Generated on: {datetime.now(SGT).strftime('%Y-%m-%d %H:%M:%S %Z')}", ln=True, align="C")
    pdf.ln(6)

    # Tally
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 8, txt="Vote Tally:", ln=True)
    pdf.set_font("Arial", "", 10)
    for row in tally:
        cid = str(row["candidate_id"])
        cname = cand_map.get(cid, cid)
        pdf.cell(190, 7, txt=f"{cname} ({cid}): {row['vote_count']} votes", ln=True)

    pdf.ln(4)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 8, txt="ZKP Commitment Proofs:", ln=True)
    pdf.set_font("Arial", "", 10)

    for p in zkp_proofs:
        cid = str(p["candidate_id"])
        cname = cand_map.get(cid, cid)
        block = (
            f"Candidate: {cname} ({cid})\n"
            f"Count: {p['vote_count']}\n"
            f"Salt: {p['salt']}\n"
            f"Commitment: {p['commitment']}\n"
        )
        pdf.multi_cell(0, 6, block, border=1)
        pdf.ln(1)

    pdf_bytes = pdf.output(dest="S").encode("latin-1")
    buf = BytesIO(pdf_bytes)

    log_admin_action("download_report_pdf", admin_email, "admin", ip_addr)

    return send_file(
        buf,
        as_attachment=True,
        download_name=f"cryptovote-{election.id}-report.pdf",
        mimetype="application/pdf",
    )
