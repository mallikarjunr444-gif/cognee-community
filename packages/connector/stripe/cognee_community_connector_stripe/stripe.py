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

    logger = get_logger("stripe_connector")
except ImportError:
    logger = logging.getLogger("stripe_connector")


class StripeConnector:
    """Connector for extracting charges and subscriptions from Stripe API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.stripe.com/v1",
        max_retries: int = 3,
        backoff_factor: float = 1.0,
    ) -> None:
        env_key = os.environ.get("STRIPE_SECRET_KEY") or os.environ.get("STRIPE_API_KEY")
        self.api_key = api_key or env_key
        if not self.api_key:
            raise ValueError("Stripe API key must be provided or set via STRIPE_SECRET_KEY.")
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
            }
        )

    def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(url, params=params, timeout=30)
                if response.status_code == 429:
                    retry_after = float(
                        response.headers.get(
                            "Retry-After",
                            self.backoff_factor * (2**attempt),
                        )
                    )
                    logger.warning(
                        "Rate limit reached on Stripe API. Backing off for %.2fs.",
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

    def get_charges(self, limit: int = 100) -> Iterator[Dict[str, Any]]:
        """Fetch charges from Stripe."""
        data = self._request("charges", params={"limit": limit})
        charges: List[Dict[str, Any]] = data.get("data", [])
        for item in charges:
            yield {
                "id": item.get("id"),
                "amount": item.get("amount"),
                "currency": item.get("currency"),
                "customer": item.get("customer"),
                "status": item.get("status"),
                "paid": item.get("paid"),
                "description": item.get("description"),
                "created": item.get("created"),
                DOCUMENT_SOURCE_ATTR: "stripe",
            }

    def get_subscriptions(self, limit: int = 100) -> Iterator[Dict[str, Any]]:
        """Fetch active subscriptions from Stripe."""
        data = self._request("subscriptions", params={"limit": limit, "status": "all"})
        subscriptions: List[Dict[str, Any]] = data.get("data", [])
        for item in subscriptions:
            yield {
                "id": item.get("id"),
                "customer": item.get("customer"),
                "status": item.get("status"),
                "current_period_start": item.get("current_period_start"),
                "current_period_end": item.get("current_period_end"),
                "cancel_at_period_end": item.get("cancel_at_period_end"),
                DOCUMENT_SOURCE_ATTR: "stripe",
            }


def stripe_charges_resource(
    api_key: Optional[str] = None,
    limit: int = 100,
) -> Iterator[Dict[str, Any]]:
    connector = StripeConnector(api_key=api_key)
    yield from connector.get_charges(limit=limit)


def stripe_subscriptions_resource(
    api_key: Optional[str] = None,
    limit: int = 100,
) -> Iterator[Dict[str, Any]]:
    connector = StripeConnector(api_key=api_key)
    yield from connector.get_subscriptions(limit=limit)
