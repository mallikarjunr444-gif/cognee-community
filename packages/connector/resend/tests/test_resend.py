from unittest.mock import MagicMock, patch

import pytest
from cognee_community_connector_resend.resend import (
    DOCUMENT_SOURCE_ATTR,
    ResendConnector,
)


def test_init_missing_key(monkeypatch):
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    with pytest.raises(ValueError, match="Resend API key must be provided"):
        ResendConnector()


def test_get_emails_mocked():
    connector = ResendConnector(api_key="re_test_dummy_key")

    mock_list_resp = MagicMock()
    mock_list_resp.status_code = 200
    mock_list_resp.json.return_value = {
        "data": [
            {
                "id": "email_123",
                "from": "onboarding@resend.dev",
                "to": ["user@example.com"],
                "subject": "Welcome to Cognee",
                "created_at": "2026-10-20T08:00:00.000Z",
            }
        ]
    }

    mock_detail_resp = MagicMock()
    mock_detail_resp.status_code = 200
    mock_detail_resp.json.return_value = {
        "id": "email_123",
        "from": "onboarding@resend.dev",
        "to": ["user@example.com"],
        "subject": "Welcome to Cognee",
        "created_at": "2026-10-20T08:00:00.000Z",
        "html": "<p>Welcome!</p>",
        "text": "Welcome!",
        "last_event": "delivered",
    }

    with patch.object(connector.session, "get", side_effect=[mock_list_resp, mock_detail_resp]):
        emails = list(connector.get_emails(limit=10))
        assert len(emails) == 1
        assert emails[0]["id"] == "email_123"
        assert emails[0]["subject"] == "Welcome to Cognee"
        assert emails[0][DOCUMENT_SOURCE_ATTR] == "resend"
        assert emails[0]["last_event"] == "delivered"


def test_get_audiences_mocked():
    connector = ResendConnector(api_key="re_test_dummy_key")

    mock_audiences_resp = MagicMock()
    mock_audiences_resp.status_code = 200
    mock_audiences_resp.json.return_value = {
        "data": [
            {
                "id": "aud_789",
                "name": "Developers",
                "created_at": "2026-10-20T08:00:00.000Z",
            }
        ]
    }

    mock_contacts_resp = MagicMock()
    mock_contacts_resp.status_code = 200
    mock_contacts_resp.json.return_value = {
        "data": [{"id": "cnt_001", "email": "dev1@example.com", "first_name": "Alice"}]
    }

    with patch.object(
        connector.session,
        "get",
        side_effect=[mock_audiences_resp, mock_contacts_resp],
    ):
        audiences = list(connector.get_audiences())
        assert len(audiences) == 1
        assert audiences[0]["name"] == "Developers"
        assert audiences[0][DOCUMENT_SOURCE_ATTR] == "resend"
        assert len(audiences[0]["contacts"]) == 1
        assert audiences[0]["contacts"][0]["email"] == "dev1@example.com"


def test_rate_limit_backoff():
    connector = ResendConnector(api_key="re_test_dummy_key", max_retries=2, backoff_factor=0.01)

    mock_429 = MagicMock()
    mock_429.status_code = 429
    mock_429.headers = {"Retry-After": "0.01"}

    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.json.return_value = {"data": []}

    with patch.object(connector.session, "get", side_effect=[mock_429, mock_200]) as mock_get:
        data = connector._request("emails")
        assert data == {"data": []}
        assert mock_get.call_count == 2
