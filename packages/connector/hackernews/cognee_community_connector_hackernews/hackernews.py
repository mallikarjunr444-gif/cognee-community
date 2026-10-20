import logging
import time
from typing import Any, Dict, Iterator, List, Optional

import requests

try:
    from cognee.shared.SourceMetadata import DOCUMENT_SOURCE_ATTR
except ImportError:
    DOCUMENT_SOURCE_ATTR = "metadata_document_source"

try:
    from cognee.shared.logging_utils import get_logger

    logger = get_logger("hackernews_connector")
except ImportError:
    logger = logging.getLogger("hackernews_connector")


class HackerNewsConnector:
    """Connector for extracting stories and discussions from Hacker News."""

    def __init__(
        self,
        base_url: str = "https://hacker-news.firebaseio.com/v0",
        max_retries: int = 3,
        backoff_factor: float = 0.5,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.session = requests.Session()

    def _get_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/item/{item_id}.json"
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    return response.json()
            except requests.RequestException as exc:
                if attempt == self.max_retries:
                    logger.warning("Failed to fetch item %d: %s", item_id, exc)
                    return None
                time.sleep(self.backoff_factor * attempt)
        return None

    def get_top_stories(self, limit: int = 50) -> Iterator[Dict[str, Any]]:
        """Fetch top stories from Hacker News."""
        url = f"{self.base_url}/topstories.json"
        try:
            resp = self.session.get(url, timeout=20)
            resp.raise_for_status()
            story_ids: List[int] = resp.json() or []
        except Exception as err:
            logger.error("Failed to fetch top stories: %s", err)
            return

        for story_id in story_ids[:limit]:
            item = self._get_item(story_id)
            if item and not item.get("deleted") and not item.get("dead"):
                yield {
                    "id": str(item.get("id")),
                    "title": item.get("title"),
                    "by": item.get("by"),
                    "score": item.get("score", 0),
                    "time": item.get("time"),
                    "url": item.get("url"),
                    "text": item.get("text"),
                    "descendants": item.get("descendants", 0),
                    DOCUMENT_SOURCE_ATTR: "hackernews",
                }

    def get_ask_stories(self, limit: int = 50) -> Iterator[Dict[str, Any]]:
        """Fetch Ask HN stories."""
        url = f"{self.base_url}/askstories.json"
        try:
            resp = self.session.get(url, timeout=20)
            resp.raise_for_status()
            story_ids: List[int] = resp.json() or []
        except Exception as err:
            logger.error("Failed to fetch ask stories: %s", err)
            return

        for story_id in story_ids[:limit]:
            item = self._get_item(story_id)
            if item and not item.get("deleted") and not item.get("dead"):
                yield {
                    "id": str(item.get("id")),
                    "title": item.get("title"),
                    "by": item.get("by"),
                    "score": item.get("score", 0),
                    "time": item.get("time"),
                    "text": item.get("text"),
                    "descendants": item.get("descendants", 0),
                    DOCUMENT_SOURCE_ATTR: "hackernews",
                }


def hackernews_top_stories_resource(
    limit: int = 50,
) -> Iterator[Dict[str, Any]]:
    connector = HackerNewsConnector()
    yield from connector.get_top_stories(limit=limit)


def hackernews_ask_hn_resource(
    limit: int = 50,
) -> Iterator[Dict[str, Any]]:
    connector = HackerNewsConnector()
    yield from connector.get_ask_stories(limit=limit)
