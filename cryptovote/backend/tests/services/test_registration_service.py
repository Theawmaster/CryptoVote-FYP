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
