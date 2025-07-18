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
        ciphertext = int(vote.vote_ciphertext)
        exponent = int(vote.vote_exponent)
        encrypted = paillier.EncryptedNumber(public_key, ciphertext, exponent)

        if ciphertext >= public_key.nsquare:
            logging.warning(f"[!] Ciphertext exceeds n² for vote {vote.id}. Potential overflow risk.")

        return encrypted
    except Exception as e:
        logging.error(f"❌ Failed to reconstruct encrypted number for vote {vote.id}: {e}")
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
    Handles decryption overflow gracefully.
    """
    results = {}
    for candidate_id, ciphertext in tally_map.items():
        try:
            count = private_key.decrypt(ciphertext)
            results[candidate_id] = count
        except Exception as e:
            logging.error(f"❌ Decryption failed for candidate '{candidate_id}': {e}")
            results[candidate_id] = -1  # or None if preferred
    return results


def format_tally_result(result_dict, max_reasonable_votes=10000):
    formatted = []
    for cid, count in result_dict.items():
        if count < 0:
            display_count = "⚠️ Decryption Failed"
        elif count > max_reasonable_votes:
            display_count = f"⚠️ Overflow ({count})"
        else:
            display_count = count

        formatted.append({
            "candidate_id": cid,
            "vote_count": display_count
        })
    return formatted


def tally_votes(session: Session):
    """
    Main function to be called from admin route/controller.
    Performs secure vote tallying and returns final result.
    """
    logging.info("🔐 Starting homomorphic tallying process...")

    public_key = load_public_key()
    private_key = load_private_key()

    # Warn if key too small
    bit_length = public_key.n.bit_length()
    if bit_length < 2048:
        logging.warning(f"⚠️ Paillier key bit length is {bit_length}, which may be too small for safe summation.")

    votes = fetch_encrypted_votes(session)
    tally_map = aggregate_votes(votes, public_key)
    result = decrypt_tally(tally_map, private_key)
    formatted_result = format_tally_result(result)

    logging.info("✅ Tallying complete.")
    return formatted_result
