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

    logger = get_logger("loops_connector")
except ImportError:
    logger = logging.getLogger("loops_connector")


class LoopsConnector:
    """Connector for extracting contacts and transactional events from Loops.so."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://app.loops.so/api/v1",
        max_retries: int = 3,
        backoff_factor: float = 1.0,
    ) -> None:
        self.api_key = api_key or os.environ.get("LOOPS_API_KEY")
        if not self.api_key:
            raise ValueError("Loops API key must be provided or set via LOOPS_API_KEY.")
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
    ) -> Any:
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
                        "Rate limit reached on Loops API. Backing off for %.2fs.",
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

    def get_contacts(self) -> Iterator[Dict[str, Any]]:
        """Fetch contacts from Loops."""
        data = self._request("contacts/find")
        if isinstance(data, list):
            contacts: List[Dict[str, Any]] = data
        else:
            contacts = data.get("contacts", [])
        for item in contacts:
            contact_id = str(item.get("id") or item.get("email"))
            yield {
                "id": contact_id,
                "email": item.get("email"),
                "firstName": item.get("firstName"),
                "lastName": item.get("lastName"),
                "subscribed": item.get("subscribed", True),
                "userGroup": item.get("userGroup"),
                "source": item.get("source"),
                DOCUMENT_SOURCE_ATTR: "loops",
            }

    def get_transactional_mails(self) -> Iterator[Dict[str, Any]]:
        """Fetch published transactional email configurations from Loops."""
        data = self._request("transactional")
        if isinstance(data, list):
            mails: List[Dict[str, Any]] = data
        else:
            mails = data.get("transactional", [])
        for item in mails:
            yield {
                "id": str(item.get("id")),
                "name": item.get("name"),
                "desc": item.get("desc"),
                "status": item.get("status"),
                DOCUMENT_SOURCE_ATTR: "loops",
            }


def loops_contacts_resource(
    api_key: Optional[str] = None,
) -> Iterator[Dict[str, Any]]:
    connector = LoopsConnector(api_key=api_key)
    yield from connector.get_contacts()


def loops_transactional_resource(
    api_key: Optional[str] = None,
) -> Iterator[Dict[str, Any]]:
    connector = LoopsConnector(api_key=api_key)
    yield from connector.get_transactional_mails()
