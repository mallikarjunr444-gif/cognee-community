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

    logger = get_logger("supabase_connector")
except ImportError:
    logger = logging.getLogger("supabase_connector")


class SupabaseConnector:
    """Connector for extracting table rows and records from Supabase."""

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
    ) -> None:
        self.supabase_url = (supabase_url or os.environ.get("SUPABASE_URL") or "").rstrip("/")
        if not self.supabase_url:
            raise ValueError("Supabase URL must be provided or set via SUPABASE_URL.")
        env_key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY") or ""
        self.supabase_key = supabase_key or env_key
        if not self.supabase_key:
            raise ValueError("Supabase API key must be provided or set via SUPABASE_KEY.")
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.session = requests.Session()
        self.session.headers.update(
            {
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}",
                "Content-Type": "application/json",
            }
        )

    def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        url = f"{self.supabase_url}/rest/v1/{endpoint.lstrip('/')}"
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
                        "Rate limit reached on Supabase API. Backing off for %.2fs.",
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

    def get_table_records(
        self,
        table_name: str,
        select: str = "*",
        limit: int = 100,
        offset: int = 0,
    ) -> Iterator[Dict[str, Any]]:
        """Fetch records from a given Supabase table."""
        data = self._request(
            table_name,
            params={
                "select": select,
                "limit": limit,
                "offset": offset,
            },
        )
        for row in data:
            record_id = str(row.get("id") or row.get("uuid") or hash(frozenset(row.items())))
            yield {
                "id": f"{table_name}_{record_id}",
                "table": table_name,
                "data": row,
                DOCUMENT_SOURCE_ATTR: "supabase",
            }


def supabase_table_resource(
    table_name: str,
    supabase_url: Optional[str] = None,
    supabase_key: Optional[str] = None,
    select: str = "*",
    limit: int = 100,
) -> Iterator[Dict[str, Any]]:
    connector = SupabaseConnector(supabase_url=supabase_url, supabase_key=supabase_key)
    yield from connector.get_table_records(table_name=table_name, select=select, limit=limit)
