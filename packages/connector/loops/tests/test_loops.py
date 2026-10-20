from unittest.mock import MagicMock, patch

import pytest
from cognee_community_connector_loops.loops import (
    DOCUMENT_SOURCE_ATTR,
    LoopsConnector,
)


def test_init_missing_key(monkeypatch):
    monkeypatch.delenv("LOOPS_API_KEY", raising=False)
    with pytest.raises(ValueError, match="Loops API key must be provided"):
        LoopsConnector()


def test_contacts_mocked():
    connector = LoopsConnector(api_key="loops_test_secret")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {
            "id": "c_101",
            "email": "sarah@ai.dev",
            "firstName": "Sarah",
            "lastName": "Connor",
            "subscribed": True,
            "userGroup": "Pro",
            "source": "Landing Page",
        }
    ]

    with patch.object(connector.session, "get", return_value=mock_resp):
        contacts = list(connector.get_contacts())
        assert len(contacts) == 1
        assert contacts[0]["id"] == "c_101"
        assert contacts[0]["email"] == "sarah@ai.dev"
        assert contacts[0][DOCUMENT_SOURCE_ATTR] == "loops"
        assert contacts[0]["userGroup"] == "Pro"


def test_transactional_mocked():
    connector = LoopsConnector(api_key="loops_test_secret")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {
            "id": "tx_202",
            "name": "Password Reset",
            "desc": "Transactional email for resetting passwords",
            "status": "published",
        }
    ]

    with patch.object(connector.session, "get", return_value=mock_resp):
        mails = list(connector.get_transactional_mails())
        assert len(mails) == 1
        assert mails[0]["id"] == "tx_202"
        assert mails[0]["name"] == "Password Reset"
        assert mails[0][DOCUMENT_SOURCE_ATTR] == "loops"
