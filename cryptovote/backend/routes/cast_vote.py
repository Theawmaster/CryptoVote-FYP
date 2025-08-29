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
from utilities.key_fingerprint import fingerprint_paillier_n

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

    # 1) validate request (allow both legacy and E2EE)
    data = request.get_json() or {}
    # minimal required always
    for k in ("election_id","token","signature"):
        if k not in data:
            return jsonify({"error":"missing_fields"}), 400

    election_id: str = data["election_id"]
    token: str = data["token"]
    signature_hex: str = data["signature"]
    ballot = data.get("ballot")  # if present, we expect client-side ciphertexts

    # 2) election, key, candidate set
    election = db.session.get(Election, election_id)
    if not election:
        return jsonify({"error": "invalid_election_id"}), 400
    
    # after loading election
    if not (election.is_active and election.has_started and not election.has_ended):
        return jsonify({"error":"election_not_open"}), 403

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

    # 4) store encrypted one-hot ballot
    ppk = load_paillier_public_key()
    cast_time = datetime.now(SGT)
    n2 = ppk.n * ppk.n
    expected_key_id = fingerprint_paillier_n(int(ppk.n))

    if ballot:
        # --- E2EE path: client supplied ciphertexts ---
        if ballot.get("key_id") != expected_key_id:
            return jsonify({"error": "mismatched_paillier_key"}), 400
        if ballot.get("scheme") != "paillier-1hot":
            return jsonify({"error": "unsupported_ballot_scheme"}), 400
        entries = ballot.get("entries")
        if not isinstance(entries, list) or not entries:
            return jsonify({"error": "invalid_ballot_entries"}), 400
        if len(entries) != len(valid_ids):
            return jsonify({"error": "ballot_length_mismatch"}), 400
        seen = set()
        for ent in entries:
            cid = ent.get("candidate_id")
            c_str = ent.get("c")
            if not cid or cid in seen or cid not in valid_ids:
                return jsonify({"error": "invalid_candidate_in_ballot"}), 400
            seen.add(cid)
            try:
                c_val = int(c_str)
            except Exception:
                return jsonify({"error":"ciphertext_not_integer"}), 400
            if not (1 <= c_val < n2):
                return jsonify({"error":"ciphertext_out_of_range"}), 400
            db.session.add(EncryptedCandidateVote(
                candidate_id=cid,
                vote_ciphertext=str(c_val),
                vote_exponent=0,                # client encodes ints {0,1}
                token_hash=token_election_hash,
                cast_at=cast_time,
                election_id=election_id,
            ))
    else:
        # --- Legacy path: server-side encryption (current behavior) ---
        candidate_id: str = data.get("candidate_id")
        if not candidate_id or candidate_id not in valid_ids:
            return jsonify({"error": "invalid_candidate_id"}), 400
        for cid in valid_ids:
            value = 1 if cid == candidate_id else 0
            enc = ppk.encrypt(value)
            db.session.add(EncryptedCandidateVote(
                candidate_id=cid,
                vote_ciphertext=str(enc.ciphertext()),
                vote_exponent=enc.exponent,
                token_hash=token_election_hash,
                cast_at=cast_time,
                election_id=election_id,
            ))

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
