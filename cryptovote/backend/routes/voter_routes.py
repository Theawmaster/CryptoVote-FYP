# routes/voter.py
from flask import Blueprint, jsonify, session
from sqlalchemy import func, and_, or_
from models.db import db
from models.election import Election, Candidate
from models.voter import Voter
from models.voter_election_status import VoterElectionStatus as VES
from utilities.auth_utils import role_required

voter_bp = Blueprint("voter", __name__)

@voter_bp.get("/elections/active")
@role_required("voter")
def list_active_elections():
    """
    Return elections that are open for voting and hide any election where this voter
    has either been issued a token OR has voted.
    """

    # Resolve voter deterministically from the session email
    email_hash = session.get("email")
    if not email_hash:
        return jsonify({"error": "unauthenticated"}), 401

    voter = Voter.query.filter_by(email_hash=email_hash).first()
    if not voter or not voter.is_verified or not voter.logged_in:
        return jsonify({"error": "forbidden"}), 403
    voter_id = voter.id

    # Correlated NOT EXISTS(VES where voter_id matches AND election_id matches AND (token_issued_at or voted_at))
    hide_exists = (
        db.session.query(VES.id)
        .filter(
            VES.voter_id == voter_id,
            VES.election_id == Election.id,
            or_(VES.token_issued_at.isnot(None), VES.voted_at.isnot(None)),
        )
        .exists()
    )

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
            ~hide_exists,   # NOT EXISTS
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

    return jsonify({
        "elections": [{
            "id": r.id,
            "name": r.name,
            "start_time": r.start_time.isoformat() if r.start_time else None,
            "end_time": r.end_time.isoformat() if r.end_time else None,
            "is_active": r.is_active,
            "has_started": r.has_started,
            "has_ended": r.has_ended,
            "candidate_count": int(r.candidate_count or 0),
        } for r in rows]
    }), 200
