import os
import sys
import pytest
from flask import Flask
from unittest.mock import patch

# Ensure backend is in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from models.db import db

@pytest.fixture(scope="module")
def test_app():
    app = Flask(__name__)
    app.secret_key = "test"
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope="module")
def client(test_app):
    with patch("routes.admin.download_routes.role_required", lambda _: (lambda f: f)):
        from routes.admin.download_routes import download_bp
        test_app.register_blueprint(download_bp, url_prefix="/admin")
        return test_app.test_client()
