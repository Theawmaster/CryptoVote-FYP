from flask import jsonify
from models.db import db
from models.election import Election
from services.tallying_service import tally_votes
from utilities.audit_utils import generate_all_zkp_proofs
from utilities.logger_utils import log_admin_action
from sqlalchemy.orm import load_only

def perform_audit_report(election_id, admin_email, ip_addr):
    try:
        election = (
            db.session.query(Election)
            .options(load_only(Election.id, Election.name))
            .filter_by(id=election_id)
            .first()
        )
        if not election:
            return jsonify({"error": "Election not found"}), 404

        # ✅ pass election_id to the tally
        tally_result = tally_votes(db.session, election_id)
        zkp_proofs   = generate_all_zkp_proofs(tally_result, election_id)

        try:
            log_admin_action("audit_report_preview", admin_email, "admin", ip_addr)
        except Exception as e:
            print("⚠️ Logging failed:", e)

        return jsonify({
            "election_id": election_id,
            "tally": tally_result,
            "zkp_proofs": list(zkp_proofs),
            "verifier_link": "/admin/verify-proof"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def perform_tally(election_id, admin_email, ip_addr):
    try:
        # Row lock avoids two concurrent tallies racing
        election = (
            db.session.query(Election)
            .filter_by(id=election_id)
            .with_for_update()
            .first()
        )
        if not election:
            return jsonify({"error": "Election not found"}), 404

        if election.tally_generated:
            return jsonify({"error": "Tally already generated for this election."}), 400
        if not election.has_ended:
            return jsonify({"error": "Cannot tally before election ends."}), 400

        # ✅ scope tally to this election
        tally_result = tally_votes(db.session, election_id)
        zkp_proofs   = generate_all_zkp_proofs(tally_result, election_id)

        # Mark as tallied atomically
        election.tally_generated = True
        db.session.commit()

        try:
            log_admin_action("tally_election", admin_email, "admin", ip_addr)
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
