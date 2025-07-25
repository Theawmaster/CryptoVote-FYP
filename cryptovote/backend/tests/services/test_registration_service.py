import pytest
from flask import Flask
from unittest.mock import MagicMock, patch
from services import registration_service as service
from models.db import db

@pytest.fixture
def create_app():
    def _create_app():
        app = Flask(__name__)
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(app)
        with app.app_context():
            db.create_all()
        return app
    return _create_app

def test_already_verified_user(create_app):
    app = create_app()
    fake_voter = MagicMock()
    fake_voter.is_verified = True

    with app.app_context():
        with patch("services.registration_service.Voter") as mock_voter:
            mock_voter.query.filter_by.return_value.first.return_value = fake_voter
            response, status = service.handle_registration("alice@e.ntu.edu.sg")
            assert status == 200
            assert "already verified" in response.get_json()["message"]

def test_already_registered_not_verified(create_app):
    app = create_app()
    fake_voter = MagicMock()
    fake_voter.is_verified = False

    with app.app_context():
        with patch("services.registration_service.Voter") as mock_voter, \
             patch("services.registration_service.secrets.token_urlsafe", return_value="token123"), \
             patch("services.registration_service.send_verification_email", return_value=None):
            mock_voter.query.filter_by.return_value.first.return_value = fake_voter
            response, status = service.handle_registration("bob@e.ntu.edu.sg")
            assert status == 200
            assert "not verified" in response.get_json()["message"]

def test_new_user_registration_success(create_app):
    app = create_app()

    with app.app_context():
        from services.registration_service import Voter  # import here to patch query after context
        with patch.object(Voter.query, "filter_by") as mock_filter_by, \
             patch("services.registration_service.secrets.token_urlsafe", return_value="token123"), \
             patch("services.registration_service.generate_rsa_key_pair", return_value=("PRIVATE_KEY_MOCK", "PUBLIC_KEY_MOCK")), \
             patch("services.registration_service.send_verification_email", return_value=None):

            mock_filter_by.return_value.first.return_value = None

            response, status = service.handle_registration("newbie@e.ntu.edu.sg")
            assert status == 201
            assert "Verification email sent" in response.get_json()["message"]
            assert response.get_json()["private_key"] == "PRIVATE_KEY_MOCK"

def test_invalid_email_domain(create_app):
    app = create_app()
    with app.app_context():
        response, status = service.handle_registration("hacker@gmail.com")
        assert status == 400
        assert "Invalid email domain" in response.get_json()["error"]

def test_db_failure_during_new_registration(create_app):
    app = create_app()
    with app.app_context():
        from services.registration_service import Voter
        with patch.object(Voter.query, "filter_by") as mock_filter_by, \
             patch("services.registration_service.secrets.token_urlsafe", return_value="token123"), \
             patch("services.registration_service.generate_rsa_key_pair", return_value=("PRIVATE_KEY_MOCK", "PUBLIC_KEY_MOCK")), \
             patch("services.registration_service.send_verification_email", return_value=None), \
             patch("services.registration_service.db.session.commit", side_effect=Exception("DB commit failed")):

            mock_filter_by.return_value.first.return_value = None

            response, status = service.handle_registration("fail@e.ntu.edu.sg")
            assert status == 500
            assert "Internal error" in response.get_json()["error"]

def test_resend_token_commit_failure(create_app):
    app = create_app()
    fake_voter = MagicMock()
    fake_voter.is_verified = False

    with app.app_context():
        with patch("services.registration_service.Voter") as mock_voter, \
             patch("services.registration_service.secrets.token_urlsafe", return_value="token123"), \
             patch("services.registration_service.send_verification_email", return_value=None), \
             patch("services.registration_service.db.session.commit", side_effect=Exception("DB error")):

            mock_voter.query.filter_by.return_value.first.return_value = fake_voter
            response, status = service.handle_registration("crash@e.ntu.edu.sg")
            assert status == 500
            assert "Internal error" in response.get_json()["error"]
            
def test_verify_signature_success(create_app):
    app = create_app()
    with app.app_context():
        mock_public_key = MagicMock()
        mock_voter = MagicMock()
        mock_voter.public_key = "-----BEGIN PUBLIC KEY-----\nFAKEKEY\n-----END PUBLIC KEY-----"

        with patch("services.registration_service.Voter") as mock_voter_model, \
             patch("services.registration_service.serialization.load_pem_public_key", return_value=mock_public_key), \
             patch("services.registration_service.base64.b64decode", return_value=b"signed_nonce"):

            # Mock the query chain
            mock_query = MagicMock()
            mock_query.filter_by.return_value.first.return_value = mock_voter
            mock_voter_model.query = mock_query

            mock_public_key.verify.return_value = None  # Simulate successful verify

            result, msg = service.verify_voter_signature("test@e.ntu.edu.sg", "fakeb64", "nonce")
            assert result is True
            assert msg == "Signature verified"

def test_verify_signature_failure(create_app):
    app = create_app()
    with app.app_context():
        mock_public_key = MagicMock()
        mock_voter = MagicMock()
        mock_voter.public_key = "-----BEGIN PUBLIC KEY-----\nFAKEKEY\n-----END PUBLIC KEY-----"

        with patch("services.registration_service.Voter") as mock_voter_model, \
             patch("services.registration_service.serialization.load_pem_public_key", return_value=mock_public_key), \
             patch("services.registration_service.base64.b64decode", return_value=b"signed_nonce"):

            # Mock the query chain
            mock_query = MagicMock()
            mock_query.filter_by.return_value.first.return_value = mock_voter
            mock_voter_model.query = mock_query

            mock_public_key.verify.side_effect = Exception("Invalid signature")

            result, msg = service.verify_voter_signature("test@e.ntu.edu.sg", "fakeb64", "nonce")
            assert result is False
            assert msg == "Invalid signature"

def test_generate_nonce():
    nonce = service.generate_nonce()
    assert isinstance(nonce, str)
    assert len(nonce) > 10  # sanity check

