# utilities/audit_service.py
from flask import jsonify
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy.orm import load_only

from models.db import db
from models.election import Election, Candidate
from models.candidate_tally import CandidateTally  # <-- NEW
from services.tallying_service import tally_votes
from utilities.audit_utils import generate_all_zkp_proofs
from utilities.logger_utils import log_admin_action

SGT = ZoneInfo("Asia/Singapore")


def _upsert_tallies(election_id: str, tally_rows: list[dict]):
    """
    Persist per-candidate totals into candidate_tallies (idempotent).
    tally_rows: [{candidate_id, candidate_name, vote_count}, ...]
    """
    now = datetime.now(SGT)
    for r in tally_rows:
        cid = r["candidate_id"]
        # tolerate "⚠️ ..." display strings from your service
        total = 0 if isinstance(r["vote_count"], str) else int(r["vote_count"])

        t = (CandidateTally.query
             .filter_by(election_id=election_id, candidate_id=cid)
             .one_or_none())
        if not t:
            t = CandidateTally(
                election_id=election_id,
                candidate_id=cid,
                total=total,
                computed_at=now
            )
            db.session.add(t)
        else:
            t.total = total
            t.computed_at = now


def perform_audit_report(election_id, admin_email, ip_addr):
    """
    PREVIEW ONLY. Computes a tally + ZK proofs and returns JSON.
    Does NOT flip flags or write candidate_tallies.
    """
    try:
        election = (
            db.session.query(Election)
            .options(load_only(Election.id, Election.name))
            .filter_by(id=election_id)
            .first()
        )
        if not election:
            return jsonify({"error": "Election not found"}), 404

        tally_result = tally_votes(db.session, election_id)     # [{candidate_id, candidate_name, vote_count}]
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
    """
    FINAL TALLY. Computes, persists into candidate_tallies, flips tally_generated.
    Safe against concurrent double-tally via row lock.
    """
    try:
        # lock row to avoid two concurrent tallies
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

        # compute
        tally_result = tally_votes(db.session, election_id)
        zkp_proofs   = generate_all_zkp_proofs(tally_result, election_id)

        # persist into candidate_tallies (idempotent upsert)
        _upsert_tallies(election_id, tally_result)

        # flip flag atomically with the upserts
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
