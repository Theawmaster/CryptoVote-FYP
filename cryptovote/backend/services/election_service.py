from flask import jsonify
from models.db import db
from models.election import Election
from datetime import datetime
from utilities.logger_utils import log_admin_action

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
            election.start_time = datetime.utcnow()

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
            election.end_time = datetime.utcnow()

        db.session.commit()
        log_admin_action("end_election", admin_email, "admin", ip_addr)

        return jsonify({"message": f"🛑 Election '{election_id}' ended."}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

def get_election_status_by_id(election_id, admin_email, ip_addr):
    election = db.session.query(Election).filter_by(id=election_id).first()
    if not election:
        return jsonify({"error": "Election not found"}), 404

    log_admin_action("election_status", admin_email, "admin", ip_addr)

    return jsonify({
        "election_id": election_id,
        "is_active": election.is_active,
        "has_started": election.has_started,
        "has_ended": election.has_ended,
        "start_time": election.start_time,
        "end_time": election.end_time
    }), 200
