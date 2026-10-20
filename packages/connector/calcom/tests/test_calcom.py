from unittest.mock import MagicMock, patch

import pytest
from cognee_community_connector_calcom.calcom import (
    DOCUMENT_SOURCE_ATTR,
    CalcomConnector,
)


def test_init_missing_key(monkeypatch):
    monkeypatch.delenv("CALCOM_API_KEY", raising=False)
    with pytest.raises(ValueError, match="Cal.com API key must be provided"):
        CalcomConnector()


def test_bookings_mocked():
    connector = CalcomConnector(api_key="cal_test_key")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "bookings": [
            {
                "id": 9988,
                "title": "Agent Strategy Sync",
                "description": "Discuss Cognee memory architecture",
                "status": "ACCEPTED",
                "startTime": "2026-10-20T10:00:00.000Z",
                "endTime": "2026-10-20T10:30:00.000Z",
                "attendees": [{"email": "founder@startup.io", "name": "Founder"}],
            }
        ]
    }

    with patch.object(connector.session, "get", return_value=mock_resp):
        bookings = list(connector.get_bookings())
        assert len(bookings) == 1
        assert bookings[0]["id"] == "9988"
        assert bookings[0]["title"] == "Agent Strategy Sync"
        assert bookings[0][DOCUMENT_SOURCE_ATTR] == "calcom"
        assert bookings[0]["status"] == "ACCEPTED"


def test_event_types_mocked():
    connector = CalcomConnector(api_key="cal_test_key")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "event_types": [
            {
                "id": 101,
                "title": "30 Min Chat",
                "slug": "30-min",
                "length": 30,
                "description": "Quick sync",
                "hidden": False,
            }
        ]
    }

    with patch.object(connector.session, "get", return_value=mock_resp):
        event_types = list(connector.get_event_types())
        assert len(event_types) == 1
        assert event_types[0]["title"] == "30 Min Chat"
        assert event_types[0]["length"] == 30
        assert event_types[0][DOCUMENT_SOURCE_ATTR] == "calcom"
