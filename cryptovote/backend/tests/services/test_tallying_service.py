import pytest
from unittest.mock import MagicMock, patch
from services import tallying_service

# ------------------ Test aggregate_votes ------------------ #

@patch("services.tallying_service.reconstruct_encrypted_number")
def test_aggregate_votes_with_multiple_votes(mock_reconstruct):
    public_key = MagicMock()

    # Mock encrypted zero values
    enc_alice_total = MagicMock(name="alice_total")
    enc_bob_total = MagicMock(name="bob_total")

    def encrypt_zero_side_effect(*args, **kwargs):
        if encrypt_zero_side_effect.counter == 0:
            encrypt_zero_side_effect.counter += 1
            return enc_alice_total
        else:
            return enc_bob_total
    encrypt_zero_side_effect.counter = 0
    public_key.encrypt.side_effect = encrypt_zero_side_effect

    # Mock reconstructed ciphertexts
    enc_1000 = MagicMock(name="enc_1000")
    enc_2000 = MagicMock(name="enc_2000")
    enc_3000 = MagicMock(name="enc_3000")
    mock_reconstruct.side_effect = [enc_1000, enc_2000, enc_3000]

    # Make homomorphic addition chainable
    enc_alice_total.__iadd__.side_effect = lambda other: enc_alice_total
    enc_bob_total.__iadd__.side_effect = lambda other: enc_bob_total

    vote1 = MagicMock(candidate_id="alice", vote_ciphertext="1000", vote_exponent="1")
    vote2 = MagicMock(candidate_id="alice", vote_ciphertext="2000", vote_exponent="1")
    vote3 = MagicMock(candidate_id="bob", vote_ciphertext="3000", vote_exponent="1")

    tally = tallying_service.aggregate_votes([vote1, vote2, vote3], public_key)

    assert tally["alice"] == enc_alice_total
    assert tally["bob"] == enc_bob_total
    assert enc_alice_total.__iadd__.call_count == 2
    assert enc_bob_total.__iadd__.call_count == 1


# ------------------ Test decrypt_tally ------------------ #

@patch("services.tallying_service.load_private_key")
def test_decrypt_tally(mock_load_key):
    mock_private_key = MagicMock()
    mock_load_key.return_value = mock_private_key

    mock_private_key.decrypt.side_effect = lambda x: f"dec({x})"

    input_map = {
        "alice": "encsum1",
        "bob": "encsum2"
    }

    result = tallying_service.decrypt_tally(input_map, mock_private_key)

    assert result == {
        "alice": "dec(encsum1)",
        "bob": "dec(encsum2)"
    }
    mock_private_key.decrypt.assert_any_call("encsum1")
    mock_private_key.decrypt.assert_any_call("encsum2")


# ------------------ Test format_tally_result ------------------ #

def test_format_tally_result():
    input_map = {
        "alice": 5,
        "bob": 3
    }
    result = tallying_service.format_tally_result(input_map)

    assert {"alice", "bob"} == {r["candidate_id"] for r in result}
    assert {5, 3} == {r["vote_count"] for r in result}


# ------------------ Test tally_votes (end-to-end) ------------------ #

@patch("services.tallying_service.load_public_key")
@patch("services.tallying_service.load_private_key")
@patch("services.tallying_service.fetch_encrypted_votes")
@patch("services.tallying_service.aggregate_votes")
@patch("services.tallying_service.decrypt_tally")
def test_tally_votes(mock_decrypt, mock_aggregate, mock_fetch, mock_priv, mock_pub):
    mock_votes = [
        MagicMock(candidate_id="alice", vote_ciphertext="aaa", vote_exponent="1"),
        MagicMock(candidate_id="bob", vote_ciphertext="bbb", vote_exponent="1")
    ]
    mock_fetch.return_value = mock_votes
    mock_aggregate.return_value = {
        "alice": "encsum1",
        "bob": "encsum2"
    }
    mock_decrypt.return_value = {
        "alice": 3,
        "bob": 2
    }

    mock_session = MagicMock()
    result = tallying_service.tally_votes(mock_session)

    assert {"alice", "bob"} == {r["candidate_id"] for r in result}
    assert {3, 2} == {r["vote_count"] for r in result}

    mock_fetch.assert_called_once_with(mock_session)
    mock_aggregate.assert_called_once_with(mock_votes, mock_pub.return_value)
    mock_decrypt.assert_called_once()
