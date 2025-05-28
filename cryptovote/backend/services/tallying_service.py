from collections import defaultdict
from models.encrypted_candidate_vote import EncryptedCandidateVote
from utilities.paillier_utils import load_private_key, load_public_key
from phe import paillier
from sqlalchemy.orm import Session
import logging


def fetch_encrypted_votes(session: Session):
    """Retrieve all encrypted candidate votes from the database."""
    return session.query(EncryptedCandidateVote).all()


def reconstruct_encrypted_number(public_key, vote):
    """
    Reconstruct an encrypted number from the vote data.
    Returns a Paillier EncryptedNumber object or None if reconstruction fails.
    """
    try:
        return paillier.EncryptedNumber(public_key, int(vote.vote_ciphertext), int(vote.vote_exponent))
    except Exception as e:
        logging.error(f"Failed to reconstruct encrypted number for vote {vote.id}: {e}")
        return None


def aggregate_votes(votes, public_key):
    """
    Aggregate encrypted votes using homomorphic addition.
    Returns a dictionary: {candidate_id: encrypted_sum}
    """
    tally_map = defaultdict(lambda: public_key.encrypt(0))

    for vote in votes:
        candidate_id = vote.candidate_id 
        encrypted_num = reconstruct_encrypted_number(public_key, vote)
        if encrypted_num:
            tally_map[candidate_id] += encrypted_num


    return tally_map


def decrypt_tally(tally_map, private_key):
    """
    Decrypt each candidate's tally.
    Returns: {candidate_id: decrypted_vote_count}
    """
    return {
        candidate_id: private_key.decrypt(ciphertext)
        for candidate_id, ciphertext in tally_map.items()
    }


def format_tally_result(result_dict):
    """
    Format tally result for API response or dashboard publishing.
    Returns list of dicts.
    """
    return [
        {"candidate_id": cid, "vote_count": count}
        for cid, count in result_dict.items()
    ]


def tally_votes(session: Session):
    """
    Main function to be called from admin route/controller.
    Performs secure vote tallying and returns final result.
    """
    logging.info("🔐 Starting homomorphic tallying process...")

    public_key = load_public_key()
    private_key = load_private_key()

    votes = fetch_encrypted_votes(session)
    tally_map = aggregate_votes(votes, public_key)
    result = decrypt_tally(tally_map, private_key)

    formatted_result = format_tally_result(result)

    logging.info("✅ Tallying complete.")
    return formatted_result
