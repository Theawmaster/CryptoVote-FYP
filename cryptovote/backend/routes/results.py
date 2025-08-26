from flask import Blueprint, jsonify, send_file, session
from io import BytesIO
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from models.db import db
from models.election import Election, Candidate
from models.candidate_tally import CandidateTally
from models.voter import Voter
from models.voter_election_status import VoterElectionStatus as VES
from utilities.auth_utils import role_required

SGT = ZoneInfo("Asia/Singapore")
results_bp = Blueprint("results", __name__)

def _edict(e: Election):
    return {
        "id": e.id,
        "name": e.name,
        "start_time": e.start_time.isoformat() if e.start_time else None,
        "end_time": e.end_time.isoformat() if e.end_time else None,
        "tally_generated": bool(getattr(e, "tally_generated", False)),
        "rsa_key_id": getattr(e, "rsa_key_id", None),
        "updated_at": e.updated_at.isoformat() if getattr(e, "updated_at", None) else None,
    }

@results_bp.get("/results/<string:election_id>")
def get_results(election_id):
    e = db.session.get(Election, election_id)
    if not e:
        return jsonify({"error":"invalid_election_id"}), 404

    cand_rows = db.session.query(Candidate.id, Candidate.name)\
        .filter(Candidate.election_id == election_id).all()
    name_map = {c.id: c.name for c in cand_rows}

    tallies = CandidateTally.query.filter_by(election_id=election_id).all()
    if not tallies or not e.tally_generated:
        return jsonify({
            "status": "pending",
            "election": _edict(e),
            "candidates": [{"id": cid, "name": nm, "total": None} for cid, nm in name_map.items()],
            "winner_ids": [],
            "last_updated": e.updated_at.isoformat() if e.updated_at else None,
        }), 200

    rows = [{"id": t.candidate_id,
             "name": name_map.get(t.candidate_id, t.candidate_id),
             "total": int(t.total),
             "computed_at": t.computed_at.isoformat()} for t in tallies]
    max_total = max(r["total"] for r in rows) if rows else 0
    winners = [r["id"] for r in rows if r["total"] == max_total]

    return jsonify({
        "status": "final",
        "election": _edict(e),
        "candidates": sorted(rows, key=lambda r: (-r["total"], r["name"])),
        "winner_ids": winners,
        "last_updated": max((r["computed_at"] for r in rows), default=e.updated_at.isoformat() if e.updated_at else None),
    }), 200

@results_bp.get("/results/<string:election_id>/audit-bundle")
def download_audit_bundle(election_id):
    e = db.session.get(Election, election_id)
    if not e:
        return jsonify({"error":"invalid_election_id"}), 404
    cands = db.session.query(Candidate.id, Candidate.name).filter_by(election_id=election_id).all()
    tallies = CandidateTally.query.filter_by(election_id=election_id).all()

    payload = {
        "meta": _edict(e),
        "candidates": [{"id": c.id, "name": c.name} for c in cands],
        "tallies": [{"candidate_id": t.candidate_id, "total": int(t.total), "computed_at": t.computed_at.isoformat()} for t in tallies],
        "generated_at": datetime.now(SGT).isoformat(),
    }
    buf = BytesIO(json.dumps(payload, indent=2).encode("utf-8"))
    return send_file(buf, mimetype="application/json", as_attachment=True, download_name=f"audit_{election_id}.json")

@results_bp.get("/voter/elections/summary")
@role_required("voter")
def voter_elections_summary():
    email_hash = session.get("email")
    voter = Voter.query.filter_by(email_hash=email_hash).first()
    if not voter or not voter.is_verified or not voter.logged_in:
        return jsonify({"error":"forbidden"}), 403

    hide = db.session.query(VES.id).filter(
        VES.voter_id == voter.id,
        VES.election_id == Election.id,
        db.or_(VES.token_issued_at.isnot(None), VES.voted_at.isnot(None))
    ).exists()

    open_e = db.session.query(Election).filter(
        Election.is_active.is_(True),
        Election.has_started.is_(True),
        Election.has_ended.is_(False),
        ~hide
    ).order_by(Election.start_time.asc()).all()

    participated = db.session.query(Election, VES)\
        .join(VES, db.and_(VES.election_id == Election.id, VES.voter_id == voter.id))\
        .order_by(Election.start_time.desc()).all()

    return jsonify({
        "open": [_edict(e) for e in open_e],
        "participated": [{
            "election": _edict(e),
            "status": {
                "token_issued": bool(s.token_issued_at),
                "voted": bool(s.voted_at),
                "results_available": bool(e.tally_generated),
            }
        } for e, s in participated]
    }), 200
