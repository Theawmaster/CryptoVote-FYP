import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from cryptovote.backend.utilities.anomaly_utils import (
    flag_suspicious_activity,
    failed_logins_last_10min
)

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.secret_key = "test"
    return app


@patch("cryptovote.backend.utilities.anomaly_utils.db")
@patch("cryptovote.backend.utilities.anomaly_utils.SuspiciousActivity")
def test_flag_suspicious_activity_success(mock_model, mock_db, app):
    with app.app_context():
        instance = MagicMock()
        mock_model.return_value = instance

        session = MagicMock()
        mock_db.session = session

        flag_suspicious_activity(
            email="admin@example.com",
            ip_address="127.0.0.1",
            reason="test reason",
            route_accessed="/login"
        )

        session.add.assert_called_once_with(instance)
        session.commit.assert_called_once()


@patch("cryptovote.backend.utilities.anomaly_utils.db")
@patch("cryptovote.backend.utilities.anomaly_utils.SuspiciousActivity")
def test_flag_suspicious_activity_failure(mock_model, mock_db, capsys, app):
    with app.app_context():
        mock_model.return_value = MagicMock()
        mock_db.session.add.side_effect = Exception("fail")
        mock_db.session.rollback = MagicMock()

        flag_suspicious_activity(
            email="fail@example.com",
            ip_address="127.0.0.1",
            reason="test fail",
            route_accessed="/fail"
        )

        mock_db.session.rollback.assert_called_once()
        captured = capsys.readouterr()
        assert "Suspicious Activity Logging Failed" in captured.out
        
def test_failed_logins_last_10min(app):
    with app.app_context():
        with patch("cryptovote.backend.utilities.anomaly_utils.SuspiciousActivity.query") as mock_query:
            mock_query.filter.return_value.count.return_value = 5
            
            count = failed_logins_last_10min("192.168.1.2")
            mock_query.filter.assert_called_once()
            assert count == 5


