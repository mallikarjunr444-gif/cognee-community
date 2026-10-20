from unittest.mock import MagicMock, patch

import pytest
from cognee_community_connector_plausible.plausible import (
    DOCUMENT_SOURCE_ATTR,
    PlausibleConnector,
)


def test_init_missing_key_or_site(monkeypatch):
    monkeypatch.delenv("PLAUSIBLE_API_KEY", raising=False)
    monkeypatch.delenv("PLAUSIBLE_SITE_ID", raising=False)
    with pytest.raises(ValueError, match="Plausible API key must be provided"):
        PlausibleConnector(site_id="site.com")

    with pytest.raises(ValueError, match="Plausible site ID must be provided"):
        PlausibleConnector(api_key="key_123")


def test_aggregate_stats_mocked():
    connector = PlausibleConnector(api_key="key_test", site_id="analytics.test")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "results": {
            "visitors": {"value": 1540},
            "pageviews": {"value": 4200},
            "bounce_rate": {"value": 38},
            "visit_duration": {"value": 145},
        }
    }

    with patch.object(connector.session, "get", return_value=mock_resp):
        stats = list(connector.get_aggregate_stats("30d"))
        assert len(stats) == 1
        assert stats[0]["visitors"] == 1540
        assert stats[0]["pageviews"] == 4200
        assert stats[0][DOCUMENT_SOURCE_ATTR] == "plausible"
        assert stats[0]["site_id"] == "analytics.test"


def test_breakdown_mocked():
    connector = PlausibleConnector(api_key="key_test", site_id="analytics.test")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "results": [
            {"page": "/blog/ai-memory", "visitors": 850},
            {"page": "/docs/getting-started", "visitors": 420},
        ]
    }

    with patch.object(connector.session, "get", return_value=mock_resp):
        pages = list(connector.get_breakdown("event:page"))
        assert len(pages) == 2
        assert pages[0]["value"] == "/blog/ai-memory"
        assert pages[0]["visitors"] == 850
        assert pages[0][DOCUMENT_SOURCE_ATTR] == "plausible"


def test_realtime_visitors_mocked():
    connector = PlausibleConnector(api_key="key_test", site_id="analytics.test")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = "42"

    with patch.object(connector.session, "get", return_value=mock_resp):
        realtime = connector.get_realtime_visitors()
        assert realtime["realtime_visitors"] == 42
        assert realtime["site_id"] == "analytics.test"
        assert realtime[DOCUMENT_SOURCE_ATTR] == "plausible"
