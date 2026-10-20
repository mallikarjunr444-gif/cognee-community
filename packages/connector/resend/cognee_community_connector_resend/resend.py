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

    logger = get_logger("resend_connector")
except ImportError:
    logger = logging.getLogger("resend_connector")


class ResendConnector:
    """Connector for extracting sent emails and audiences from Resend API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.resend.com",
        max_retries: int = 3,
        backoff_factor: float = 1.0,
    ) -> None:
        self.api_key = api_key or os.environ.get("RESEND_API_KEY")
        if not self.api_key:
            raise ValueError("Resend API key must be provided or set via RESEND_API_KEY.")
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
                        "Rate limit reached on Resend API. Backing off for %.2fs.",
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

    def get_emails(self, limit: int = 100) -> Iterator[Dict[str, Any]]:
        """Fetch sent emails from Resend."""
        data = self._request("emails", params={"limit": limit})
        emails: List[Dict[str, Any]] = data.get("data", [])
        for item in emails:
            email_id = item.get("id")
            detail: Dict[str, Any] = item
            if email_id:
                try:
                    detail = self._request(f"emails/{email_id}")
                except Exception as err:
                    logger.warning("Could not fetch details for email %s: %s", email_id, err)
            yield {
                "id": detail.get("id"),
                "from": detail.get("from"),
                "to": detail.get("to"),
                "subject": detail.get("subject"),
                "created_at": detail.get("created_at"),
                "html": detail.get("html"),
                "text": detail.get("text"),
                "last_event": detail.get("last_event"),
                DOCUMENT_SOURCE_ATTR: "resend",
            }

    def get_audiences(self) -> Iterator[Dict[str, Any]]:
        """Fetch contact audiences from Resend."""
        data = self._request("audiences")
        audiences: List[Dict[str, Any]] = data.get("data", [])
        for audience in audiences:
            audience_id = audience.get("id")
            contacts: List[Dict[str, Any]] = []
            if audience_id:
                try:
                    cdata = self._request(f"audiences/{audience_id}/contacts")
                    contacts = cdata.get("data", [])
                except Exception as err:
                    logger.warning(
                        "Could not fetch contacts for audience %s: %s",
                        audience_id,
                        err,
                    )
            yield {
                "id": audience_id,
                "name": audience.get("name"),
                "created_at": audience.get("created_at"),
                "contacts": contacts,
                DOCUMENT_SOURCE_ATTR: "resend",
            }


def resend_emails_resource(
    api_key: Optional[str] = None,
    limit: int = 100,
) -> Iterator[Dict[str, Any]]:
    connector = ResendConnector(api_key=api_key)
    yield from connector.get_emails(limit=limit)


def resend_audiences_resource(
    api_key: Optional[str] = None,
) -> Iterator[Dict[str, Any]]:
    connector = ResendConnector(api_key=api_key)
    yield from connector.get_audiences()
