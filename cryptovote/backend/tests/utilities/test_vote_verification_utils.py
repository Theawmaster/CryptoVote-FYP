import sys, os
import pytest
from flask import Flask
from unittest.mock import patch, MagicMock
from utilities.verification import vote_verification_utils as utils
from app import app

# Dynamically add cryptovote/backend to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

@pytest.fixture(autouse=True)
def app_context():
    with app.app_context():
        yield

@pytest.fixture
def fake_data():
    return {
        "token": "abc",
        "signature": "123",
        "candidate_id": "alice"
    }

def test_validate_vote_request_all_fields_present(fake_data):
    ok, response, status = utils.validate_vote_request(fake_data)
    assert ok is True
    assert response is None

def test_validate_vote_request_missing_field():
    incomplete_data = {"token": "abc", "signature": "123"}  # missing ciphertext and exponent
    ok, response, status = utils.validate_vote_request(incomplete_data)
    assert ok is False
    assert response.json["error"].startswith("Missing field")
    assert status == 400

def test_is_valid_hex():
    assert utils.is_valid_hex("deadbeef") is True
    assert utils.is_valid_hex("xyz") is False

def test_parse_and_verify_signature_success():
    class DummyKey:
        e = 65537
        n = 999998727899283

    sig_hex = "1a2b3c"
    message = "voteforA123"

    with patch("utilities.blind_signature_utils.verify_signed_token", return_value=True) as mock_verify:
        valid, sig_int, err = utils.parse_and_verify_signature(message, sig_hex, DummyKey())
        assert valid is True
        assert isinstance(sig_int, int)
        assert err is None
        mock_verify.assert_called_once()

def test_parse_and_verify_signature_invalid_hex():
    app = Flask(__name__)
    with app.app_context():
        valid, response, status = utils.parse_and_verify_signature("voteforA123", "nothex$$", MagicMock())
        assert not valid
        assert status == 400
        assert response.get_json() == {"error": "Signature must be valid hex"}

def test_is_token_used_false():
    mock_query = MagicMock()
    mock_query.filter_by.return_value.first.return_value = None

    with patch("cryptovote.backend.utilities.verification.vote_verification_utils.IssuedToken") as MockIssuedToken:
        MockIssuedToken.query = mock_query
        result = utils.is_token_used("fake_token")
        assert result is False

def test_is_token_used_true():
    mock_query = MagicMock()
    mock_query.filter_by.return_value.first.return_value = MagicMock()

    with patch("utilities.verification.vote_verification_utils.IssuedToken") as MockIssuedToken:
        MockIssuedToken.query = mock_query
        result = utils.is_token_used("fakehash")
        assert result is True

def test_store_vote_and_token():
    with patch("models.db.db.session") as mock_session:
        utils.store_vote_and_token("hash123", "ciphertext")
        assert mock_session.commit.called
