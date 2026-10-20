import logging
import os
import time
from typing import Any, Dict, Iterator, List, Optional

import requests

try:
    from cognee.shared.SourceMetadata import DOCUMENT_SOURCE_ATTR
except ImportError:
    DOCUMENT_SOURCE_ATTR = "metadata_document_source"

try:
    from cognee.shared.logging_utils import get_logger

    logger = get_logger("calcom_connector")
except ImportError:
    logger = logging.getLogger("calcom_connector")


class CalcomConnector:
    """Connector for extracting bookings and event types from Cal.com API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.cal.com/v1",
        max_retries: int = 3,
        backoff_factor: float = 1.0,
    ) -> None:
        self.api_key = api_key or os.environ.get("CALCOM_API_KEY")
        if not self.api_key:
            raise ValueError("Cal.com API key must be provided or set via CALCOM_API_KEY.")
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
            }
        )

    def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        query = dict(params or {})
        query["apiKey"] = self.api_key

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(url, params=query, timeout=30)
                if response.status_code == 429:
                    retry_after = float(
                        response.headers.get(
                            "Retry-After",
                            self.backoff_factor * (2**attempt),
                        )
                    )
                    logger.warning(
                        "Rate limit reached on Cal.com API. Backing off for %.2fs.",
                        retry_after,
                    )
                    time.sleep(retry_after)
                    continue

                response.raise_for_status()
                return response.json()
            except requests.RequestException as exc:
                if attempt == self.max_retries:
                    logger.error("Failed request to %s: %s", url, exc)
                    raise
                time.sleep(self.backoff_factor * (2**attempt))
        raise RuntimeError(f"Exhausted retries calling {url}")

    def get_bookings(self, status: Optional[str] = None) -> Iterator[Dict[str, Any]]:
        """Fetch bookings/meetings from Cal.com."""
        params: Dict[str, Any] = {}
        if status:
            params["status"] = status
        data = self._request("bookings", params=params)
        bookings: List[Dict[str, Any]] = data.get("bookings", [])
        for item in bookings:
            yield {
                "id": str(item.get("id")),
                "title": item.get("title"),
                "description": item.get("description"),
                "status": item.get("status"),
                "startTime": item.get("startTime"),
                "endTime": item.get("endTime"),
                "attendees": item.get("attendees", []),
                DOCUMENT_SOURCE_ATTR: "calcom",
            }

    def get_event_types(self) -> Iterator[Dict[str, Any]]:
        """Fetch user event types/schedules from Cal.com."""
        data = self._request("event-types")
        event_types: List[Dict[str, Any]] = data.get("event_types", [])
        for item in event_types:
            yield {
                "id": str(item.get("id")),
                "title": item.get("title"),
                "slug": item.get("slug"),
                "length": item.get("length"),
                "description": item.get("description"),
                "hidden": item.get("hidden", False),
                DOCUMENT_SOURCE_ATTR: "calcom",
            }


def calcom_bookings_resource(
    api_key: Optional[str] = None,
    status: Optional[str] = None,
) -> Iterator[Dict[str, Any]]:
    connector = CalcomConnector(api_key=api_key)
    yield from connector.get_bookings(status=status)


def calcom_event_types_resource(
    api_key: Optional[str] = None,
) -> Iterator[Dict[str, Any]]:
    connector = CalcomConnector(api_key=api_key)
    yield from connector.get_event_types()
