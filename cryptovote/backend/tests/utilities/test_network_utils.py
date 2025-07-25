import pytest
import os
from flask import Flask, jsonify
from unittest.mock import patch

from utilities.network_utils import is_ntu_ip, ntu_wifi_only

# --- Unit Tests for is_ntu_ip ---

def test_is_ntu_ip_valid_ntu_public():
    assert is_ntu_ip("155.69.191.45") is True

def test_is_ntu_ip_valid_ntu_private():
    assert is_ntu_ip("10.10.10.10") is True

def test_is_ntu_ip_invalid_ip():
    assert is_ntu_ip("192.168.0.1") is False

def test_is_ntu_ip_malformed():
    assert is_ntu_ip("not.an.ip") is False


# --- Integration Test with Decorator ---

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True

    @app.route("/protected")
    @ntu_wifi_only
    def protected_route():
        return jsonify({"message": "Access granted"}), 200

    return app

@pytest.fixture
def client(app):
    return app.test_client()


# --- Decorator Tests ---

def test_ntu_wifi_only_allows_ntu_ip(client):
    response = client.get("/protected", environ_overrides={"REMOTE_ADDR": "155.69.191.100"})
    assert response.status_code == 200
    assert b"Access granted" in response.data

def test_ntu_wifi_only_rejects_non_ntu_ip(client):
    response = client.get("/protected", environ_overrides={"REMOTE_ADDR": "8.8.8.8"})
    assert response.status_code == 403
    assert b"Access restricted to NTU WiFi" in response.data

@patch.dict(os.environ, {"FLASK_ENV": "development"})
def test_ntu_wifi_only_bypassed_in_dev(client):
    response = client.get("/protected", environ_overrides={"REMOTE_ADDR": "8.8.8.8"})
    assert response.status_code == 200
    assert b"Access granted" in response.data
