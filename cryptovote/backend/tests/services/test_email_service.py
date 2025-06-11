import os
import pytest
import smtplib
import importlib
from unittest.mock import patch, MagicMock

# ✅ This must be first to patch env BEFORE importing the actual function
@pytest.fixture(autouse=True)
def reload_with_env(monkeypatch):
    monkeypatch.setenv("SMTP_EMAIL", "testsender@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "dummy_password")
    monkeypatch.setenv("BASE_URL", "http://localhost:5000")

    # ✅ Reload the module to pick up new env vars
    import services.email_service
    importlib.reload(services.email_service)
    globals()["send_verification_email"] = services.email_service.send_verification_email  # rebind to global

# ✅ This test should now work correctly
@patch("smtplib.SMTP")
def test_send_verification_email_success(mock_smtp):
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server

    send_verification_email("receiver@example.com", "test-token-123")

    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("testsender@example.com", "dummy_password")
    mock_server.send_message.assert_called_once()

    msg = mock_server.send_message.call_args[0][0]
    assert msg["To"] == "receiver@example.com"
    assert "verify-email?token=test-token-123" in msg.get_content()

@patch("smtplib.SMTP")
def test_send_verification_email_auth_error(mock_smtp):
    mock_server = MagicMock()
    mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Authentication failed")
    mock_smtp.return_value.__enter__.return_value = mock_server

    with pytest.raises(smtplib.SMTPAuthenticationError):
        send_verification_email("failuser@example.com", "token123")

@patch("smtplib.SMTP")
def test_send_verification_email_timeout(mock_smtp):
    mock_smtp.side_effect = TimeoutError("Connection timed out")

    with pytest.raises(TimeoutError):
        send_verification_email("slow@example.com", "token456")

def test_fallback_base_url(monkeypatch):
    monkeypatch.delenv("BASE_URL", raising=False)
    monkeypatch.setenv("SMTP_EMAIL", "testsender@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "dummy_password")

    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        send_verification_email("receiver@example.com", "abc123")

        msg = mock_server.send_message.call_args[0][0]
        assert "http://localhost:5000/register/verify-email?token=abc123" in msg.get_content()
