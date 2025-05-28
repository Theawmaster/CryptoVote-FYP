# audit_utils.py

import hashlib
import secrets


def generate_commitment(candidate_id: int, vote_count: int, election_id: str, salt: str) -> str:
    """
    Generate SHA-256 commitment hash.
    """
    message = f"{candidate_id}|{vote_count}|{election_id}|{salt}"
    return hashlib.sha256(message.encode()).hexdigest()


def generate_zkp_proof(candidate_id: int, vote_count: int, election_id: str):
    """
    Generate a zero-knowledge-style proof (commitment-based).
    Returns a dictionary that can be exposed in the audit API.
    """
    salt = secrets.token_hex(8)
    commitment = generate_commitment(candidate_id, vote_count, election_id, salt)

    return {
        "candidate_id": candidate_id,
        "vote_count": vote_count,
        "election_id": election_id,
        "salt": salt,
        "commitment": commitment
    }

def generate_all_zkp_proofs(result_list: list, election_id: str):
    """
    Takes the full tally result and election_id, returns list of ZKP proof objects.
    """
    return [
        generate_zkp_proof(item["candidate_id"], item["vote_count"], election_id)
        for item in result_list
    ]

