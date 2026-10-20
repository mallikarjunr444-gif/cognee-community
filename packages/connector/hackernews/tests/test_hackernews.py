from unittest.mock import MagicMock, patch

from cognee_community_connector_hackernews.hackernews import (
    DOCUMENT_SOURCE_ATTR,
    HackerNewsConnector,
)


def test_top_stories_mocked():
    connector = HackerNewsConnector()

    mock_ids_resp = MagicMock()
    mock_ids_resp.status_code = 200
    mock_ids_resp.json.return_value = [1001, 1002]

    mock_item_1 = {
        "id": 1001,
        "title": "Cognee Memory Layer",
        "by": "pg",
        "score": 350,
        "time": 1729400000,
        "url": "https://cognee.ai",
        "descendants": 84,
    }

    mock_item_2 = {
        "id": 1002,
        "title": "Dead Story",
        "dead": True,
    }

    with patch.object(connector.session, "get") as mock_get:
        mock_get.return_value = mock_ids_resp
        with patch.object(connector, "_get_item", side_effect=[mock_item_1, mock_item_2]):
            stories = list(connector.get_top_stories(limit=10))
            assert len(stories) == 1
            assert stories[0]["id"] == "1001"
            assert stories[0]["title"] == "Cognee Memory Layer"
            assert stories[0][DOCUMENT_SOURCE_ATTR] == "hackernews"
            assert stories[0]["score"] == 350


def test_ask_stories_mocked():
    connector = HackerNewsConnector()

    mock_ids_resp = MagicMock()
    mock_ids_resp.status_code = 200
    mock_ids_resp.json.return_value = [2001]

    mock_item = {
        "id": 2001,
        "title": "Ask HN: Best vector memory for agents?",
        "by": "karpathy",
        "score": 520,
        "time": 1729405000,
        "text": "What do people use for long term agent memory?",
        "descendants": 120,
    }

    with patch.object(connector.session, "get") as mock_get:
        mock_get.return_value = mock_ids_resp
        with patch.object(connector, "_get_item", return_value=mock_item):
            stories = list(connector.get_ask_stories(limit=5))
            assert len(stories) == 1
            assert stories[0]["id"] == "2001"
            assert stories[0]["by"] == "karpathy"
            assert stories[0][DOCUMENT_SOURCE_ATTR] == "hackernews"
