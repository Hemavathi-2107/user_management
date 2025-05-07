import pytest
import smtplib
from app.utils.smtp_connection import SMTPClient
from unittest.mock import patch
import logging

@pytest.fixture(autouse=True)
def patch_logging(monkeypatch):
    # Silence logging calls
    monkeypatch.setattr(logging, "info", lambda *args, **kwargs: None)
    monkeypatch.setattr(logging, "error", lambda *args, **kwargs: None)

class DummySMTP:
    def __init__(self, server, port):
        self.server = server
        self.port = port
        self.tls_started = False
        self.logged_in = False
        self.sent = []

    def starttls(self):
        self.tls_started = True

    def login(self, user, pwd):
        if pwd == "bad":
            raise smtplib.SMTPAuthenticationError(535, b"Auth failed")
        self.logged_in = True

    def sendmail(self, frm, to, msg):
        if to == "bad@domain":
            raise smtplib.SMTPRecipientsRefused({to: (550, b"User unknown")})
        self.sent.append((frm, to, msg))

    def quit(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.quit()

@patch("app.utils.smtp_connection.smtplib.SMTP")
def test_send_email_success(mock_smtp):
    dummy = DummySMTP("smtp.example.com", 587)
    mock_smtp.return_value = dummy

    client = SMTPClient("smtp.example.com", 587, "user@example.com", "pass")
    client.send_email("Test", "<p>Hi</p>", "to@example.com")

    # SMTP was instantiated correctly
    mock_smtp.assert_called_with("smtp.example.com", 587)
    # TLS, login, sendmail all happened
    assert dummy.tls_started is True
    assert dummy.logged_in is True
    assert dummy.sent[0][1] == "to@example.com"
    assert "<p>Hi</p>" in dummy.sent[0][2]

@patch("app.utils.smtp_connection.smtplib.SMTP")
def test_send_email_auth_failure(mock_smtp):
    dummy = DummySMTP("smtp.example.com", 587)
    mock_smtp.return_value = dummy

    client = SMTPClient("smtp.example.com", 587, "user@example.com", "bad")
    with pytest.raises(smtplib.SMTPAuthenticationError):
        client.send_email("Subj", "<p>Hi</p>", "to@example.com")

@patch("app.utils.smtp_connection.smtplib.SMTP")
def test_send_email_recipient_refused(mock_smtp):
    dummy = DummySMTP("smtp.example.com", 587)
    mock_smtp.return_value = dummy

    client = SMTPClient("smtp.example.com", 587, "user@example.com", "pass")
    with pytest.raises(smtplib.SMTPRecipientsRefused):
        client.send_email("Subj", "<p>Hi</p>", "bad@domain")

@patch("app.utils.smtp_connection.smtplib.SMTP")
def test_send_email_generic_exception(mock_smtp):
    # Force SMTP constructor to throw
    mock_smtp.side_effect = RuntimeError("Connection error")

    client = SMTPClient("smtp.example.com", 587, "user@example.com", "pass")
    with pytest.raises(RuntimeError):
        client.send_email("Subj", "<p>Hi</p>", "to@example.com")