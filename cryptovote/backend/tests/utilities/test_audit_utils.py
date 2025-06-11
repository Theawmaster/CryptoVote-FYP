import pytest
import hashlib
from backend.utilities import audit_utils


def test_generate_commitment_consistency():
    candidate_id = 1
    vote_count = 100
    election_id = "election2025"
    salt = "fixedsalt123"

    expected = hashlib.sha256(f"{candidate_id}|{vote_count}|{election_id}|{salt}".encode()).hexdigest()
    actual = audit_utils.generate_commitment(candidate_id, vote_count, election_id, salt)

    assert actual == expected
    assert len(actual) == 64  # SHA-256 hex length


def test_generate_zkp_proof_structure():
    candidate_id = 42
    vote_count = 77
    election_id = "secure_election"

    proof = audit_utils.generate_zkp_proof(candidate_id, vote_count, election_id)

    assert isinstance(proof, dict)
    assert set(proof.keys()) == {"candidate_id", "vote_count", "election_id", "salt", "commitment"}
    assert proof["candidate_id"] == candidate_id
    assert proof["vote_count"] == vote_count
    assert proof["election_id"] == election_id
    assert isinstance(proof["salt"], str)
    assert len(proof["commitment"]) == 64


def test_generate_zkp_proof_random_salt_changes_commitment():
    candidate_id = 5
    vote_count = 10
    election_id = "audit2025"

    proof1 = audit_utils.generate_zkp_proof(candidate_id, vote_count, election_id)
    proof2 = audit_utils.generate_zkp_proof(candidate_id, vote_count, election_id)

    # Ensure randomness
    assert proof1["salt"] != proof2["salt"]
    assert proof1["commitment"] != proof2["commitment"]


def test_generate_all_zkp_proofs_batch():
    input_data = [
        {"candidate_id": 1, "vote_count": 99},
        {"candidate_id": 2, "vote_count": 101}
    ]
    election_id = "demo_election"

    result = audit_utils.generate_all_zkp_proofs(input_data, election_id)

    assert isinstance(result, list)
    assert len(result) == 2
    for proof in result:
        assert set(proof.keys()) == {"candidate_id", "vote_count", "election_id", "salt", "commitment"}
        assert proof["election_id"] == election_id
