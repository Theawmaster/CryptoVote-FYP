import pytest
from flask import Flask, jsonify, request
from services import auth_service
from unittest.mock import patch

# Simulate the Flask app and login route using auth_service
@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.secret_key = "integration_test_secret"

    @app.route("/auth/login", methods=["POST"])
    def login():
        data = request.get_json()
        email = data.get("email")
        signed_nonce = data.get("signed_nonce")

        if not email:
            return jsonify({"error": "Email is required"}), 400

        email_hash = auth_service.get_email_hash(email)

        # Mocked voter exists and is verified
        voter = {"email_hash": email_hash, "is_verified": True}

        if not voter or not voter["is_verified"]:
            return jsonify({"error": "Unverified or unknown voter."}), 403

        if not signed_nonce:
            if False:  # Assume not already logged in for this test
                return jsonify({"message": "You are already signed in."}), 200

            nonce = auth_service.request_nonce(email_hash)
            return jsonify({"nonce": nonce}), 200

        # Simulate nonce validation and signature check
        nonce, error = auth_service.validate_nonce(email_hash)
        if error:
            return jsonify({"error": error}), 403

        # Simulate successful signature verification
        if signed_nonce != f"signature_of_{nonce}":
            return jsonify({"error": "Invalid signature"}), 401

        auth_service.clear_nonce(email_hash)
        return jsonify({"message": "Login successful"}), 200

    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_request_nonce_flow(client):
    email = "student@e.ntu.edu.sg"
    response = client.post("/auth/login", json={"email": email})
    assert response.status_code == 200
    data = response.get_json()
    assert "nonce" in data
    assert len(data["nonce"]) > 0


def test_login_with_valid_signed_nonce(client):
    email = "voter@e.ntu.edu.sg"
    email_hash = auth_service.get_email_hash(email)
    nonce = auth_service.request_nonce(email_hash)
    signed_nonce = f"signature_of_{nonce}"

    response = client.post("/auth/login", json={"email": email, "signed_nonce": signed_nonce})
    assert response.status_code == 200
    assert response.get_json()["message"] == "Login successful"


def test_login_with_invalid_signature(client):
    email = "voter@e.ntu.edu.sg"
    email_hash = auth_service.get_email_hash(email)
    auth_service.request_nonce(email_hash)

    response = client.post("/auth/login", json={"email": email, "signed_nonce": "bad_signature"})
    assert response.status_code == 401
    assert "Invalid signature" in response.get_json()["error"]


def test_expired_nonce_flow(client):
    email = "old@e.ntu.edu.sg"
    email_hash = auth_service.get_email_hash(email)
    auth_service.nonce_store[email_hash] = {
        "nonce": "expired_nonce",
        "issued_at": auth_service.datetime.utcnow() - auth_service.timedelta(seconds=999)
    }

    response = client.post("/auth/login", json={"email": email, "signed_nonce": "signature_of_expired_nonce"})
    assert response.status_code == 403
    assert "Nonce expired" in response.get_json()["error"]

def test_clear_nonce_removes_entry():
    email_hash = auth_service.get_email_hash("clear@ntu.edu")
    auth_service.request_nonce(email_hash)
    auth_service.clear_nonce(email_hash)
    assert email_hash not in auth_service.nonce_store
