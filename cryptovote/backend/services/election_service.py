# services/election_service.py
from flask import jsonify
from datetime import datetime
from zoneinfo import ZoneInfo
from uuid import uuid4
from sqlalchemy import func

from models.db import db
from models.election import Election, Candidate
from models.encrypted_candidate_vote import EncryptedCandidateVote  # check file name

from utilities.logger_utils import log_admin_action

SGT = ZoneInfo("Asia/Singapore")


def start_election_by_id(election_id, admin_email, ip_addr):
    try:
        election = db.session.query(Election).filter_by(id=election_id).first()
        if not election:
            return jsonify({"error": "Election not found"}), 404

        if election.has_started:
            return jsonify({"message": "Election already started."}), 200

        election.has_started = True
        election.is_active = True
        if not election.start_time:
            election.start_time = datetime.now(SGT)

        db.session.commit()
        log_admin_action("start_election", admin_email, "admin", ip_addr)
        return jsonify({"message": f"✅ Election '{election_id}' started."}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


def end_election_by_id(election_id, admin_email, ip_addr):
    try:
        election = db.session.query(Election).filter_by(id=election_id).first()
        if not election:
            return jsonify({"error": "Election not found"}), 404

        if election.has_ended:
            return jsonify({"message": "Election already ended."}), 200

        election.has_ended = True
        election.is_active = False
        if not election.end_time:
            election.end_time = datetime.now(SGT)

        db.session.commit()
        log_admin_action("end_election", admin_email, "admin", ip_addr)
        return jsonify({"message": f"🛑 Election '{election_id}' ended."}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


def get_election_status_by_id(election_id, admin_email, ip_addr):
    try:
        election = db.session.query(Election).filter_by(id=election_id).first()
        if not election:
            return jsonify({"error": "Election not found"}), 404

        log_admin_action("election_status", admin_email, "admin", ip_addr)

        # Counts (guarded so missing FKs won't crash)
        try:
            candidate_count = Candidate.query.filter_by(election_id=election_id).count()
            vote_count = (
                db.session.query(func.count(EncryptedCandidateVote.id))
                .join(Candidate, Candidate.id == EncryptedCandidateVote.candidate_id)
                .filter(Candidate.election_id == election_id)
                .scalar()
            ) or 0
        except Exception:
            candidate_count = 0
            vote_count = 0

        return jsonify({
            "id": election.id,                                  # <- frontend expects id
            "name": election.name or "",                        # never undefined
            "is_active": bool(election.is_active),
            "has_started": bool(election.has_started),
            "has_ended": bool(election.has_ended),
            "start_time": election.start_time.isoformat() if election.start_time else None,
            "end_time":   election.end_time.isoformat()   if election.end_time   else None,  # <- fixed
            "tally_generated": bool(election.tally_generated),
            "candidate_count": int(candidate_count),
            "vote_count": int(vote_count),
        }), 200

    except Exception as e:
        # Catch anything unexpected so the client gets a JSON error, not a 500 HTML page
        return jsonify({"error": f"Server error: {str(e)}"}), 500


def create_new_election(data, admin_email, ip_addr):
    required_fields = ["id", "name"]
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    existing = db.session.query(Election).filter_by(id=data["id"]).first()
    if existing:
        return jsonify({"error": "Election with this ID already exists."}), 400

    candidates_payload = data.get("candidates", []) or []

    try:
        election = Election(
            id=data["id"],
            name=data["name"],
            start_time=None,
            end_time=None,
            is_active=False,
            has_started=False,
            has_ended=False,
            tally_generated=False
        )
        db.session.add(election)

        created_candidates = []
        for c in candidates_payload:
            cname = (c.get("name") or "").strip()
            if not cname:
                continue
            cid = (c.get("id") or uuid4().hex)[:64]
            created = Candidate(id=cid, name=cname, election_id=election.id)
            db.session.add(created)
            created_candidates.append(created)

        db.session.commit()
        try:
            log_admin_action("create_election", admin_email, "admin", ip_addr)
        except Exception:
            pass

        return jsonify({
            "message": f"🆕 Election '{election.id}' created successfully.",
            "election": {
                "id": election.id,
                "name": election.name,
                "start_time": None,
                "end_time": None,
                "is_active": election.is_active,
                "has_started": election.has_started,
                "has_ended": election.has_ended,
                "tally_generated": election.tally_generated,
                "candidates": [{"id": c.id, "name": c.name} for c in created_candidates],
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Server error: {str(e)}"}), 500
