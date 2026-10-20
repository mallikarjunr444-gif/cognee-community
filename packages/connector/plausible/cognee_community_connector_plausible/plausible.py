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

    logger = get_logger("plausible_connector")
except ImportError:
    logger = logging.getLogger("plausible_connector")


class PlausibleConnector:
    """Connector for Plausible Analytics API (Cloud or Self-Hosted)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        site_id: Optional[str] = None,
        base_url: str = "https://plausible.io/api/v1",
        max_retries: int = 3,
        backoff_factor: float = 1.0,
    ) -> None:
        self.api_key = api_key or os.environ.get("PLAUSIBLE_API_KEY")
        if not self.api_key:
            raise ValueError("Plausible API key must be provided or set via PLAUSIBLE_API_KEY.")
        self.site_id = site_id or os.environ.get("PLAUSIBLE_SITE_ID")
        if not self.site_id:
            raise ValueError("Plausible site ID must be provided or set via PLAUSIBLE_SITE_ID.")
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
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
        query["site_id"] = self.site_id

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
                        "Rate limit reached on Plausible API. Backing off for %.2fs.",
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

    def get_realtime_visitors(self) -> Dict[str, Any]:
        """Fetch current realtime visitor count."""
        url = f"{self.base_url}/stats/realtime/visitors"
        resp = self.session.get(url, params={"site_id": self.site_id}, timeout=30)
        resp.raise_for_status()
        count = int(resp.text) if resp.text.isdigit() else 0
        return {
            "site_id": self.site_id,
            "realtime_visitors": count,
            DOCUMENT_SOURCE_ATTR: "plausible",
        }

    def get_aggregate_stats(self, period: str = "30d") -> Iterator[Dict[str, Any]]:
        """Fetch aggregate traffic metrics."""
        data = self._request(
            "stats/aggregate",
            params={
                "period": period,
                "metrics": "visitors,pageviews,bounce_rate,visit_duration",
            },
        )
        results = data.get("results", {})
        yield {
            "id": f"{self.site_id}_{period}",
            "site_id": self.site_id,
            "period": period,
            "visitors": results.get("visitors", {}).get("value", 0),
            "pageviews": results.get("pageviews", {}).get("value", 0),
            "bounce_rate": results.get("bounce_rate", {}).get("value", 0),
            "visit_duration": results.get("visit_duration", {}).get("value", 0),
            DOCUMENT_SOURCE_ATTR: "plausible",
        }

    def get_breakdown(
        self, property_name: str = "event:page", period: str = "30d", limit: int = 100
    ) -> Iterator[Dict[str, Any]]:
        """Fetch breakdown by property (e.g. event:page, visit:source)."""
        data = self._request(
            "stats/breakdown",
            params={
                "property": property_name,
                "period": period,
                "limit": limit,
            },
        )
        items: List[Dict[str, Any]] = data.get("results", [])
        for item in items:
            key_val = item.get("page") or item.get("source") or item.get(property_name) or "item"
            yield {
                "id": f"{self.site_id}_{property_name}_{key_val}",
                "site_id": self.site_id,
                "property": property_name,
                "value": key_val,
                "visitors": item.get("visitors", 0),
                DOCUMENT_SOURCE_ATTR: "plausible",
            }


def plausible_aggregate_resource(
    api_key: Optional[str] = None,
    site_id: Optional[str] = None,
    period: str = "30d",
) -> Iterator[Dict[str, Any]]:
    connector = PlausibleConnector(api_key=api_key, site_id=site_id)
    yield from connector.get_aggregate_stats(period=period)


def plausible_breakdown_resource(
    api_key: Optional[str] = None,
    site_id: Optional[str] = None,
    property_name: str = "event:page",
    period: str = "30d",
) -> Iterator[Dict[str, Any]]:
    connector = PlausibleConnector(api_key=api_key, site_id=site_id)
    yield from connector.get_breakdown(property_name=property_name, period=period)
