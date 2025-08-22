from flask import Blueprint, jsonify
from sqlalchemy import func
from models.db import db
from models.election import Election, Candidate
from utilities.auth_utils import role_required

voter_bp = Blueprint("voter", __name__)

@voter_bp.get("/elections/active")
@role_required("voter")
def list_active_elections():
    """
    Return elections that are currently open for voting:
      is_active = TRUE AND has_started = TRUE AND has_ended = FALSE
    Includes a lightweight candidate_count for quick display.
    """
    rows = (
        db.session.query(
            Election.id,
            Election.name,
            Election.start_time,
            Election.end_time,
            Election.is_active,
            Election.has_started,
            Election.has_ended,
            func.count(Candidate.id).label("candidate_count"),
        )
        .outerjoin(Candidate, Candidate.election_id == Election.id)
        .filter(
            Election.is_active.is_(True),
            Election.has_started.is_(True),
            Election.has_ended.is_(False),
        )
        .group_by(
            Election.id,
            Election.name,
            Election.start_time,
            Election.end_time,
            Election.is_active,
            Election.has_started,
            Election.has_ended,
        )
        .order_by(Election.start_time.asc())
        .all()
    )

    def to_dict(r):
        return {
            "id": r.id,
            "name": r.name,
            "start_time": r.start_time.isoformat() if r.start_time else None,
            "end_time": r.end_time.isoformat() if r.end_time else None,
            "is_active": r.is_active,
            "has_started": r.has_started,
            "has_ended": r.has_ended,
            "candidate_count": int(r.candidate_count or 0),
        }

    return jsonify({"elections": [to_dict(r) for r in rows]}), 200
