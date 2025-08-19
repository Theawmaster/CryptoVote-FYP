# services/tallying_service.py
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging
from phe import paillier

from models.encrypted_candidate_vote import EncryptedCandidateVote
from models.election import Candidate
from utilities.paillier_utils import load_private_key, load_public_key


def fetch_encrypted_votes(session: Session, election_id: str):
    """
    Retrieve encrypted votes ONLY for this election by joining through Candidate.
    """
    return (
        session.query(EncryptedCandidateVote)
        .join(Candidate, Candidate.id == EncryptedCandidateVote.candidate_id)
        .filter(Candidate.election_id == election_id)
        .all()
    )


def reconstruct_encrypted_number(public_key, vote: EncryptedCandidateVote):
    """
    Reconstruct a Paillier EncryptedNumber from stored ciphertext/exponent.
    """
    try:
        ciphertext = int(vote.vote_ciphertext)
        exponent = int(vote.vote_exponent)
        enc = paillier.EncryptedNumber(public_key, ciphertext, exponent)

        if ciphertext >= public_key.nsquare:
            logging.warning(
                f"[!] Ciphertext exceeds n² for vote {vote.id}. Potential overflow risk."
            )
        return enc
    except Exception as e:
        logging.error(f"❌ Reconstruct failed for vote {vote.id}: {e}")
        return None


def aggregate_votes(votes, public_key):
    """
    Homomorphically add encrypted ballots per candidate.
    Returns: dict[candidate_id] -> EncryptedNumber
    """
    zero = public_key.encrypt(0)
    tally_map = defaultdict(lambda: zero)

    for v in votes:
        enc = reconstruct_encrypted_number(public_key, v)
        if enc is not None:
            tally_map[v.candidate_id] += enc

    return tally_map


def decrypt_tally(tally_map, private_key):
    """
    Decrypt the per-candidate encrypted sums.
    Returns: dict[candidate_id] -> int (or -1 on failure)
    """
    out = {}
    for cid, enc_sum in tally_map.items():
        try:
            out[cid] = private_key.decrypt(enc_sum)
        except Exception as e:
            logging.error(f"❌ Decryption failed for candidate '{cid}': {e}")
            out[cid] = -1
    return out


def format_tally_result(session: Session, election_id: str, dec_counts: dict, max_reasonable=10000):
    """
    Produce a list including zero-vote candidates:
    [{candidate_id, candidate_name, vote_count}, ...]
    """
    candidates = (
        session.query(Candidate.id, Candidate.name)
        .filter(Candidate.election_id == election_id)
        .order_by(Candidate.name.asc())
        .all()
    )

    rows = []
    for cid, cname in candidates:
        count = dec_counts.get(cid, 0)
        if count < 0:
            display = "⚠️ Decryption Failed"
        elif max_reasonable is not None and count > max_reasonable:
            display = f"⚠️ Overflow ({count})"
        else:
            display = int(count)
        rows.append({
            "candidate_id": cid,
            "candidate_name": cname,
            "vote_count": display,
        })
    return rows


def tally_votes(session: Session, election_id: str):
    """
    Main entry: tally one election’s votes using Paillier homomorphic addition.
    """
    logging.info(f"🔐 Starting tally for election '{election_id}'")

    public_key = load_public_key()
    private_key = load_private_key()

    if public_key.n.bit_length() < 2048:
        logging.warning("⚠️ Paillier key < 2048 bits; consider rotating to a stronger key.")

    votes = fetch_encrypted_votes(session, election_id)
    enc_sums = aggregate_votes(votes, public_key)
    dec_counts = decrypt_tally(enc_sums, private_key)
    result = format_tally_result(session, election_id, dec_counts)

    logging.info("✅ Tally complete.")
    return result
