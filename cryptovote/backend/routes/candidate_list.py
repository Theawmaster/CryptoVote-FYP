from flask import Blueprint, jsonify
from models.db import db
from models.election import Election, Candidate
from utilities.auth_utils import role_required

candidate_list_bp = Blueprint("candidate_list", __name__)

@candidate_list_bp.get("/elections/<string:election_id>")
@role_required("voter")
def election_detail(election_id):
    e = db.session.query(Election).filter_by(id=election_id).first()
    if not e:
        return jsonify({"error": "Election not found"}), 404

    cands = (
        db.session.query(Candidate.id, Candidate.name)
        .filter_by(election_id=election_id)
        .order_by(Candidate.name.asc())
        .all()
    )
    return jsonify({
        "id": e.id,
        "name": e.name,
        "start_time": e.start_time.isoformat() if e.start_time else None,
        "end_time": e.end_time.isoformat() if e.end_time else None,
        "rsa_key_id": e.rsa_key_id,
        "candidates": [{"id": c.id, "name": c.name} for c in cands],
        "candidate_count": len(cands),
    }), 200
