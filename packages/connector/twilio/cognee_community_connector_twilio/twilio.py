"""DLT source for Twilio communication records (SMS, WhatsApp, and call logs).

Full snapshot + forget-on-delete.
Fetches message history (body, sender, recipient, delivery status, direction, timestamps)
from the Twilio REST API, rendering them into clean Markdown documents. Yields them as a
dlt resource for cognee's ingestion pipeline.

Unlike relational dlt paths, Twilio communications are ingested as *normal documents*:
the source declares ``cognee_document_source = "twilio"``, so ``resolve_dlt_sources``
tags each item with ``external_metadata["source"] = "twilio"``. This ensures each message
flows through cognee's standard cognify entity-extraction pipeline — extracting entities,
sender/recipient relationships, verification codes, and support context — instead of
the flat dlt-row path.

The source uses a full snapshot synchronization model: ``write_disposition="replace"``
rewrites staging on each run with the messages currently active in Twilio. Deletions
propagate cleanly — an expunged message drops out of the snapshot, so cognee's existing
``orphan_cleanup`` removes it from the graph and vector stores. Unchanged items preserve
stable content-hash ``data_id`` keys, preventing redundant re-ingestion.
"""

import os
import time
from collections.abc import Iterator
from typing import Any

import httpx

try:
    from cognee.shared.logging_utils import get_logger
except ImportError:
    import logging

    def get_logger(name: str):
        return logging.getLogger(name)


try:
    from cognee.tasks.ingestion.dlt_utils import DOCUMENT_SOURCE_ATTR
except ImportError:
    DOCUMENT_SOURCE_ATTR = "cognee_document_source"

logger = get_logger("twilio_connector")

TWILIO_TABLE_NAME = "twilio_documents"
TWILIO_SOURCE_NAME = "twilio"
TWILIO_BASE_URL = "https://api.twilio.com/2010-04-01"

# Retry budget for rate-limited (429) / transient Twilio API responses
_MAX_RETRIES = 5
_BASE_BACKOFF = 1.0


def _request_with_retry(
    client: httpx.Client,
    method: str,
    url: str,
    auth: tuple[str, str],
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute an HTTP request with exponential backoff on 429 rate limits and 5xx errors."""
    for attempt in range(_MAX_RETRIES):
        try:
            response = client.request(method, url, auth=auth, params=params, timeout=30.0)
            if response.status_code == 429:
                header_backoff = response.headers.get("Retry-After")
                retry_after = (
                    float(header_backoff) if header_backoff else _BASE_BACKOFF * (2**attempt)
                )
                logger.warning("Twilio rate limit reached, waiting %.1f seconds", retry_after)
                time.sleep(retry_after)
                continue
            response.raise_for_status()
            return response.json()
        except (httpx.TransportError, httpx.HTTPStatusError) as exc:
            if attempt == _MAX_RETRIES - 1:
                msg = f"Twilio request failed after {_MAX_RETRIES} attempts: {exc}"
                raise RuntimeError(msg) from exc
            time.sleep(_BASE_BACKOFF * (2**attempt))
    raise RuntimeError(f"Twilio request exceeded retry budget for {url}")


def _format_message_markdown(msg: dict[str, Any]) -> str:
    """Render a Twilio message deterministically into Markdown for entity extraction."""
    sid = msg.get("sid", "").strip()
    from_num = msg.get("from", "Unknown").strip()
    to_num = msg.get("to", "Unknown").strip()
    status = msg.get("status", "unknown").strip()
    direction = msg.get("direction", "unknown").strip()
    date_sent = msg.get("date_sent") or msg.get("date_created") or "Unknown"
    price = msg.get("price") or "0.00"
    price_unit = msg.get("price_unit") or "USD"
    body = (msg.get("body") or "").strip()

    is_whatsapp = from_num.startswith("whatsapp:") or to_num.startswith("whatsapp:")
    comm_type = "WhatsApp" if is_whatsapp else "SMS"

    doc_parts = [
        f"# Twilio Communication: [{comm_type}] {from_num} -> {to_num}",
        "",
        f"- **Message SID**: {sid}",
        f"- **Type**: {comm_type}",
        f"- **From**: {from_num}",
        f"- **To**: {to_num}",
        f"- **Status**: {status}",
        f"- **Direction**: {direction}",
        f"- **Date Sent**: {date_sent}",
        f"- **Price**: {price} {price_unit}",
        "",
        "## Message Body",
        body if body else "_No text content in message._",
    ]
    return "\n".join(doc_parts)


def twilio_source(
    account_sid: str | None = None,
    auth_token: str | None = None,
    page_size: int = 50,
    client: Any = None,
):
    """Create a dlt source yielding Twilio communication records as markdown documents.

    Args:
        account_sid: Twilio Account SID. Falls back to ``TWILIO_ACCOUNT_SID``.
        auth_token: Twilio Auth Token. Falls back to ``TWILIO_AUTH_TOKEN``.
        page_size: Number of messages per page (default: 50).
        client: Pre-built ``httpx.Client`` (primarily for test mock injection).

    Returns:
        A dlt source suitable for ``cognee.add(...)`` / ``cognee.remember(...)``.
    """
    try:
        import dlt
    except ImportError as exc:
        raise ImportError(
            'The Twilio connector requires dlt: pip install "dlt[sqlalchemy] httpx"'
        ) from exc

    resolved_sid = account_sid or os.environ.get("TWILIO_ACCOUNT_SID")
    resolved_token = auth_token or os.environ.get("TWILIO_AUTH_TOKEN")

    if not resolved_sid or not resolved_token:
        raise ValueError(
            "Twilio credentials required: pass account_sid= and auth_token= "
            "or set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN."
        )

    http_client = client or httpx.Client(timeout=30.0)
    auth = (resolved_sid, resolved_token)

    @dlt.resource(name=TWILIO_TABLE_NAME, primary_key="id", write_disposition="replace")
    def twilio_messages() -> Iterator[dict[str, Any]]:
        url = f"{TWILIO_BASE_URL}/Accounts/{resolved_sid}/Messages.json"
        params: dict[str, Any] | None = {"PageSize": page_size}

        while url:
            data = _request_with_retry(http_client, "GET", url, auth, params=params)
            messages = data.get("messages") or []

            for msg in messages:
                sid = str(msg["sid"])
                doc_text = _format_message_markdown(msg)
                yield {
                    "id": sid,
                    "from": msg.get("from", ""),
                    "to": msg.get("to", ""),
                    "status": msg.get("status", ""),
                    "body": doc_text,
                }

            # Check next page URI from Twilio response
            next_page_uri = data.get("next_page_uri")
            if next_page_uri:
                url = f"https://api.twilio.com{next_page_uri}"
                params = None  # Next page URI already has query params baked in
            else:
                url = ""

    @dlt.source(name=TWILIO_SOURCE_NAME)
    def source():
        return [twilio_messages]

    src = source()
    setattr(src, DOCUMENT_SOURCE_ATTR, "twilio")
    return src
