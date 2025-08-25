from flask import Blueprint, request, jsonify, session
from datetime import datetime
import hashlib
from zoneinfo import ZoneInfo

from models.voter import Voter
from models.db import db
# from models.issued_token import IssuedToken   # optional: you can remove if unused
from models.encrypted_candidate_vote import EncryptedCandidateVote
from models.election import Candidate, Election
from models.voter_election_status import VoterElectionStatus as VES

from utilities.blind_signature_utils import load_public_key as load_rsa_pubkey
from utilities.paillier_utils import load_public_key as load_paillier_public_key
from utilities.verification.vote_verification_utils import (
    validate_vote_request,
    parse_and_verify_signature,
)

SGT = ZoneInfo("Asia/Singapore")
cast_vote_bp = Blueprint("cast_vote", __name__)

@cast_vote_bp.route("/cast-vote", methods=["POST"])
def cast_vote():
    # 0) session auth
    email_hash = session.get("email")
    if not email_hash:
        return jsonify({"error": "unauthenticated"}), 401
    voter = Voter.query.filter_by(email_hash=email_hash).first()
    if not voter or not voter.is_verified or not voter.logged_in:
        return jsonify({"error": "forbidden"}), 403

    # 1) validate request
    data = request.get_json() or {}
    ok, response, status = validate_vote_request(data)
    if not ok:
        return response, status

    election_id: str = data["election_id"]
    candidate_id: str = data["candidate_id"]
    token: str = data["token"]
    signature_hex: str = data["signature"]

    # 2) election, key, candidate set
    election = db.session.get(Election, election_id)
    if not election:
        return jsonify({"error": "invalid_election_id"}), 400

    # verify with THIS election's RSA key
    try:
        rsa_pub = load_rsa_pubkey(election.rsa_key_id)
    except TypeError:
        rsa_pub = load_rsa_pubkey()

    # OPTIONAL “gold”: verify signature over scoped message:
    # scoped_hex = hashlib.sha256(f"{election_id}|{token}".encode()).hexdigest()
    # valid_sig, _, err = parse_and_verify_signature(scoped_hex, signature_hex, rsa_pub)
    valid_sig, _, err = parse_and_verify_signature(token, signature_hex, rsa_pub)
    if not valid_sig:
        return err if isinstance(err, tuple) else (jsonify({"error": "invalid_signature"}), 400)

    candidate_rows = db.session.query(Candidate.id).filter(
        Candidate.election_id == election_id
    ).all()
    valid_ids = {r.id for r in candidate_rows}
    if candidate_id not in valid_ids:
        return jsonify({"error": "invalid_candidate_id"}), 400

    # 3) REUSE GUARDS
    # (a) token reuse scoped to election
    token_election_hash = hashlib.sha256(f"{election_id}|{token}".encode("utf-8")).hexdigest()
    used_token = (
        db.session.query(EncryptedCandidateVote.id)
        .filter(EncryptedCandidateVote.token_hash == token_election_hash)
        .first()
    )
    if used_token:
        return jsonify({"error": "token_already_used"}), 403

    # (b) voter double-vote prevention (this is where your VES check belongs—already here)
    ves_record = VES.query.filter_by(voter_id=voter.id, election_id=election_id).first()
    if ves_record and ves_record.voted_at:
        return jsonify({"error": "already_voted"}), 403

    # 4) encrypt one-hot ballot
    ppk = load_paillier_public_key()
    cast_time = datetime.now(SGT)

    for cid in valid_ids:
        value = 1 if cid == candidate_id else 0
        enc = ppk.encrypt(value)
        db.session.add(
            EncryptedCandidateVote(
                candidate_id=cid,
                vote_ciphertext=str(enc.ciphertext()),
                vote_exponent=enc.exponent,
                token_hash=token_election_hash,   # <-- scoped
                cast_at=cast_time,
                election_id=election_id,          # <-- stored for audit/index
            )
        )

    # 5) mark voted
    mark_voted(voter.id, election_id)

    db.session.commit()
    return jsonify({"message": "✅ Vote cast successfully."}), 200


def mark_voted(voter_id: int, election_id: str):
    ves = VES.query.filter_by(voter_id=voter_id, election_id=election_id).one_or_none()
    if not ves:
        ves = VES(voter_id=voter_id, election_id=election_id)
        db.session.add(ves)
    ves.voted_at = datetime.now(SGT)
