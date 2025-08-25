# routes/blind_sign.py
from flask import Blueprint, request, jsonify, session
from models.db import db
from models.issued_token import IssuedToken
from models.voter import Voter
from models.election import Election
from utilities.blind_signature_utils import sign_blinded_token
from models.voter_election_status import VoterElectionStatus as VES
from utilities.auth_utils import role_required
import hashlib
from datetime import datetime
from _zoneinfo import ZoneInfo

SGT = ZoneInfo("Asia/Singapore")

blind_sign_bp = Blueprint("blind_sign", __name__)

def mark_token_issued(voter_id: int, election_id: str):
    ves = (VES.query
              .filter_by(voter_id=voter_id, election_id=election_id)
              .one_or_none())
    if not ves:
        ves = VES(voter_id=voter_id, election_id=election_id)
        db.session.add(ves)
    ves.token_issued_at = datetime.now(SGT)
    db.session.commit()

@blind_sign_bp.post("/elections/<string:election_id>/blind-sign")
@role_required("voter")  # your decorator already checks twofa
def blind_sign(election_id):
    # ---- session identity (don’t trust email in body) ----
    email_hash = session.get("email")
    if not email_hash:
        return jsonify({"error": "unauthenticated"}), 401

    voter = Voter.query.filter_by(email_hash=email_hash).first()
    if not voter or not voter.is_verified or not voter.logged_in:
        return jsonify({"error": "forbidden"}), 403

    # ---- input ----
    data = request.get_json(force=True) or {}
    blinded_token_hex = data.get("blinded_token_hex") or data.get("blinded_token")  # allow old key for compatibility
    rsa_key_id = data.get("rsa_key_id")

    if not blinded_token_hex or not rsa_key_id:
        return jsonify({"error": "blinded_token_hex and rsa_key_id are required"}), 400

    # ---- election & key check ----
    election = Election.query.filter_by(id=election_id, is_active=True).first()
    if not election:
        return jsonify({"error": "invalid_election"}), 400

    if getattr(election, "rsa_key_id", None) != rsa_key_id:
        return jsonify({"error": "key_mismatch_for_election"}), 400

    # ---- prevent duplicate issuance (keep your current policy) ----
    already_issued = (
        db.session.query(VES.id)
        .filter(
            VES.voter_id == voter.id,
            VES.election_id == election_id,
            VES.token_issued_at.isnot(None),
        )
        .first()
    )
    if already_issued:
        return jsonify({"error": "token_already_issued_for_this_election"}), 403

    try:
        blinded_int = int(blinded_token_hex, 16)

        # Support both signatures: sign_blinded_token(blinded_int, rsa_key_id) or sign_blinded_token(blinded_int)
        try:
            signed_blinded_int = sign_blinded_token(blinded_int, rsa_key_id)  # preferred if your util supports per-key
        except TypeError:
            signed_blinded_int = sign_blinded_token(blinded_int)  # fallback to global key util

        signed_blinded_hex = hex(signed_blinded_int)[2:]

        # ---- record issuance (keep it minimal / unlinkable) ----
        issued_time = datetime.now(SGT)

        # This issuance hash is just an internal marker (not the spend token hash)
        issuance_fingerprint = f"{email_hash}|{election_id}|{issued_time.isoformat()}"
        issuance_hash = hashlib.sha256(issuance_fingerprint.encode()).hexdigest()

        issued = IssuedToken(
            token_hash=issuance_hash,
            used=False,
            issued_at=issued_time
        )
        db.session.add(issued)

        mark_token_issued(voter_id=voter.id, election_id=election_id)

        db.session.commit()

        return jsonify({
            "signed_blinded_token_hex": signed_blinded_hex,
            "rsa_key_id": rsa_key_id
        }), 200

    except ValueError:
        db.session.rollback()
        return jsonify({"error": "invalid_blinded_token_hex"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"signing_failed: {e}"}), 500

