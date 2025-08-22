from flask import Blueprint, request, jsonify
from datetime import datetime
import hashlib
from _zoneinfo import ZoneInfo

from models.db import db
from models.issued_token import IssuedToken
from models.encrypted_candidate_vote import EncryptedCandidateVote
from models.election import Candidate, Election
from models.voter_election_status import VoterElectionStatus as VES

from utilities.blind_signature_utils import load_public_key as load_rsa_pubkey
from utilities.paillier_utils import load_public_key as load_paillier_public_key
from utilities.verification.vote_verification_utils import (
    validate_vote_request,           # keep basic shape checks: fields present, strings, etc.
    parse_and_verify_signature,      # verify blind signature over token
)

SGT = ZoneInfo("Asia/Singapore")

cast_vote_bp = Blueprint("cast_vote", __name__)

@cast_vote_bp.route("/cast-vote", methods=["POST"])
def cast_vote():
    data = request.get_json() or {}

    # 1) basic request validation (presence / types)
    ok, response, status = validate_vote_request(data)
    if not ok:
        return response, status

    election_id: str = data["election_id"]
    candidate_id: str = data["candidate_id"]
    token: str = data["token"]
    signature_hex: str = data["signature"]
    
    

    # 2) verify blind signature on token
    valid_sig, signature_int, error_response = parse_and_verify_signature(
        token, signature_hex, load_rsa_pubkey()
    )
    if not valid_sig:
        # error_response can be a (json, code) tuple or an Exception/message
        return error_response if isinstance(error_response, tuple) else (jsonify({"error": str(error_response)}), 400)

    # 3) resolve valid candidates for this election
    #    (reject if election missing or candidate not part of it)
    election = db.session.get(Election, election_id)
    if not election:
        return jsonify({"error": "invalid election_id"}), 400

    rows = (
        db.session.query(Candidate.id)
        .filter(Candidate.election_id == election_id)
        .all()
    )
    valid_ids = {r.id for r in rows}
    if candidate_id not in valid_ids:
        return jsonify({"error": "invalid candidate_id"}), 400

    # 4) prevent token reuse (check if we already recorded any vote with this token hash)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    already = (
        db.session.query(EncryptedCandidateVote.id)
        .filter(EncryptedCandidateVote.token_hash == token_hash)
        .first()
    )
    if already:
        return jsonify({"error": "token_already_used"}), 403

    # 5) encrypt one-hot ballot using Paillier
    ppk = load_paillier_public_key()
    cast_time = datetime.now(SGT)

    for cid in valid_ids:
        value = 1 if cid == candidate_id else 0
        enc = ppk.encrypt(value)  # returns PaillierEncryptedNumber
        db.session.add(
            EncryptedCandidateVote(
                candidate_id=cid,
                vote_ciphertext=str(enc.ciphertext()),
                vote_exponent=enc.exponent,
                token_hash=token_hash,
                cast_at=cast_time,
            )
        )

    # 6) mark token as used (if you track this in IssuedToken)
    it = IssuedToken.query.filter_by(token_hash=token_hash).first()
    if it:
        it.used = True
    # If you *can’t* have token_hash at issuance time (server never sees raw token),
    # it’s OK to only rely on EncryptedCandidateVote existence for “used” checks.

    db.session.commit()
    return jsonify({"message": "✅ Vote cast successfully."}), 200

def mark_voted(voter_id: int, election_id: str):
    ves = VES.query.filter_by(voter_id=voter_id, election_id=election_id).one_or_none()
    if not ves:
        ves = VES(voter_id=voter_id, election_id=election_id)
        db.session.add(ves)
    ves.voted_at = datetime.now(SGT)
    db.session.commit()