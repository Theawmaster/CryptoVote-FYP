import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from utilities import logger_utils

@patch("utilities.logger_utils.AdminLog")
@patch("utilities.logger_utils.db")
def test_log_admin_action(mock_db, mock_log_model):
    # Arrange: simulate no previous log
    with patch("utilities.logger_utils.get_last_log_hash", return_value="0"*64):
        mock_session = MagicMock()
        mock_db.session = mock_session

        action = "RESET_PASSWORD"
        email = "admin@example.com"
        role = "admin"
        ip_address = "127.0.0.1"

        # Act
        logger_utils.log_admin_action(action, email, role, ip_address)

        # Assert that AdminLog was instantiated correctly
        assert mock_log_model.call_count == 1
        args, kwargs = mock_log_model.call_args
        assert kwargs["admin_email"] == email
        assert kwargs["role"] == role
        assert kwargs["action"] == action
        assert kwargs["ip_address"] == ip_address
        assert kwargs["prev_hash"] == "0" * 64
        assert len(kwargs["entry_hash"]) == 64  # SHA-256 hash length

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

def test_compute_log_hash_deterministic():
    timestamp = datetime(2024, 1, 1, 12, 0, 0)
    h1 = logger_utils.compute_log_hash("0"*64, "a@b.com", "admin", "LOGIN", timestamp, "1.2.3.4")
    h2 = logger_utils.compute_log_hash("0"*64, "a@b.com", "admin", "LOGIN", timestamp, "1.2.3.4")

    assert h1 == h2
    assert len(h1) == 64
    assert all(c in "0123456789abcdef" for c in h1)

@patch("utilities.logger_utils.AdminLog")
def test_get_last_log_hash_none(mock_log_model):
    mock_log_model.query.order_by().first.return_value = None
    result = logger_utils.get_last_log_hash()
    assert result == "0" * 64

@patch("utilities.logger_utils.AdminLog")
def test_get_last_log_hash_existing(mock_log_model):
    mock_entry = MagicMock(entry_hash="abcd" * 16)
    mock_log_model.query.order_by().first.return_value = mock_entry
    result = logger_utils.get_last_log_hash()
    assert result == "abcd" * 16

@patch("utilities.logger_utils.AdminLog")
@patch("utilities.logger_utils.db")
def test_log_admin_action_rollback_on_failure(mock_db, mock_log_model):
    # Arrange: simulate failure in commit
    mock_session = MagicMock()
    mock_session.commit.side_effect = Exception("DB Failure")
    mock_db.session = mock_session

    with patch("utilities.logger_utils.get_last_log_hash", return_value="0" * 64):
        # Act
        logger_utils.log_admin_action("FAIL_CASE", "fail@admin.com", "admin", "127.0.0.1")

        # Ensure rollback was called due to exception
        mock_session.rollback.assert_called_once()
