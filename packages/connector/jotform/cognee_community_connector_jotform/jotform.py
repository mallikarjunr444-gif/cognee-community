"""DLT source for Jotform form submissions and operational memory.

Full snapshot + forget-on-delete.
Fetches form schemas and submissions from the Jotform REST API, translates raw field keys
into human-readable questions, and renders them into structured Markdown documents.
Yields them as a dlt resource for cognee's graph ingestion pipeline.

The source declares ``cognee_document_source = "jotform"``, routing submissions
through cognee's document-mode cognify pipeline.
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

logger = get_logger("jotform_connector")

JOTFORM_TABLE_NAME = "jotform_documents"
JOTFORM_SOURCE_NAME = "jotform"
JOTFORM_API_BASE = "https://api.jotform.com"

_MAX_RETRIES = 5
_BASE_BACKOFF = 1.0


def _request_with_retry(
    client: httpx.Client,
    method: str,
    url: str,
    **kwargs: Any,
) -> httpx.Response:
    """Executes an HTTP request with exponential backoff on HTTP 429 rate limits."""
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            resp = client.request(method, url, **kwargs)
            if resp.status_code == 429 and attempt < _MAX_RETRIES:
                retry_after_hdr = resp.headers.get("Retry-After")
                try:
                    sleep_s = (
                        float(retry_after_hdr)
                        if retry_after_hdr
                        else _BASE_BACKOFF * (2 ** (attempt - 1))
                    )
                except ValueError:
                    sleep_s = _BASE_BACKOFF * (2 ** (attempt - 1))
                logger.warning(
                    "Jotform API 429 rate limit hit. Backing off for %.2fs (attempt %d/%d)",
                    sleep_s,
                    attempt,
                    _MAX_RETRIES,
                )
                time.sleep(sleep_s)
                continue
            resp.raise_for_status()
            return resp
        except httpx.HTTPStatusError as e:
            if e.response.status_code in {500, 502, 503, 504} and attempt < _MAX_RETRIES:
                sleep_s = _BASE_BACKOFF * (2 ** (attempt - 1))
                logger.warning(
                    "Jotform API %d error. Retrying in %.2fs (attempt %d/%d)",
                    e.response.status_code,
                    sleep_s,
                    attempt,
                    _MAX_RETRIES,
                )
                time.sleep(sleep_s)
                continue
            raise
    raise RuntimeError("Unreachable: retry loop terminated without return or raise")


def fetch_form_questions(client: httpx.Client, form_id: str) -> dict[str, str]:
    """Retrieves field definitions and question labels for a form."""
    url = f"{JOTFORM_API_BASE}/form/{form_id}/questions"
    try:
        resp = _request_with_retry(client, "GET", url)
        data = resp.json()
        questions = {}
        for q_id, q_data in data.get("content", {}).items():
            text = q_data.get("text") or q_data.get("name") or f"Field_{q_id}"
            questions[str(q_id)] = text
        return questions
    except Exception as exc:
        logger.warning("Could not fetch questions for form %s: %s", form_id, exc)
        return {}


def format_answer_value(val: Any) -> str:
    """Formats complex Jotform answer structures into readable strings."""
    if val is None:
        return ""
    if isinstance(val, dict):
        parts = [f"{k}: {v}" for k, v in val.items() if v]
        return ", ".join(parts)
    if isinstance(val, list):
        return ", ".join(str(item) for item in val if item)
    return str(val).strip()


def render_submission_document(
    submission: dict[str, Any],
    form_title: str,
    questions: dict[str, str],
) -> str:
    """Renders a Jotform submission into a structured Markdown document."""
    sub_id = submission.get("id", "unknown")
    created_at = submission.get("created_at", "unknown")
    form_id = submission.get("form_id", "unknown")
    status = submission.get("status", "ACTIVE")

    lines = [
        f"# Jotform Submission: {form_title} (#{sub_id})",
        f"- **Form ID:** {form_id}",
        f"- **Submission ID:** {sub_id}",
        f"- **Created At:** {created_at}",
        f"- **Status:** {status}",
        "",
        "## Form Responses",
    ]

    answers = submission.get("answers", {})
    for q_id, a_data in answers.items():
        q_text = questions.get(str(q_id)) or a_data.get("text") or f"Question {q_id}"
        answer_raw = a_data.get("answer")
        ans_str = format_answer_value(answer_raw)
        if ans_str:
            lines.append(f"- **{q_text}:** {ans_str}")

    return "\n".join(lines)


def fetch_jotform_submissions(
    api_key: str | None = None,
    form_ids: list[str] | None = None,
    limit_per_form: int = 100,
    client: httpx.Client | None = None,
) -> Iterator[dict[str, Any]]:
    """Fetches forms and submissions from Jotform API."""
    key = api_key or os.environ.get("JOTFORM_API_KEY")
    if not key:
        raise ValueError("JOTFORM_API_KEY must be provided or set in environment variables.")

    headers = {"APIKEY": key, "Accept": "application/json"}
    http_client = client or httpx.Client(headers=headers, timeout=30.0)
    try:
        forms_to_sync: list[dict[str, str]] = []

        if form_ids:
            for fid in form_ids:
                f_url = f"{JOTFORM_API_BASE}/form/{fid}"
                try:
                    resp = _request_with_retry(http_client, "GET", f_url)
                    f_info = resp.json().get("content", {})
                    title = f_info.get("title", f"Form {fid}")
                    forms_to_sync.append({"id": fid, "title": title})
                except Exception as e:
                    logger.warning("Could not fetch form metadata for %s: %s", fid, e)
                    forms_to_sync.append({"id": fid, "title": f"Form {fid}"})
        else:
            forms_url = f"{JOTFORM_API_BASE}/user/forms"
            resp = _request_with_retry(http_client, "GET", forms_url, params={"limit": 50})
            forms_data = resp.json().get("content", [])
            for f in forms_data:
                if f.get("status") == "ENABLED":
                    forms_to_sync.append(
                        {"id": str(f.get("id")), "title": f.get("title", "Untitled")}
                    )

        for f_item in forms_to_sync:
            fid = f_item["id"]
            ftitle = f_item["title"]
            questions = fetch_form_questions(http_client, fid)

            subs_url = f"{JOTFORM_API_BASE}/form/{fid}/submissions"
            resp = _request_with_retry(
                http_client,
                "GET",
                subs_url,
                params={"limit": limit_per_form},
            )
            submissions = resp.json().get("content", [])

            for sub in submissions:
                sub_id = str(sub.get("id"))
                doc_text = render_submission_document(sub, ftitle, questions)
                yield {
                    "id": f"jotform_{fid}_{sub_id}",
                    "name": f"jotform_sub_{sub_id}.md",
                    "text": doc_text,
                    "mime_type": "text/markdown",
                    "external_metadata": {
                        "source": JOTFORM_SOURCE_NAME,
                        "form_id": fid,
                        "submission_id": sub_id,
                        "form_title": ftitle,
                    },
                }
    finally:
        if client is None:
            http_client.close()


def _make_dummy_dlt():
    """Fallback dlt decorator factory when dlt is not directly installed."""

    def decorator(*args, **kwargs):
        def wrapper(fn):
            fn.__dlt_resource__ = True
            return fn

        return wrapper

    return decorator


try:
    import dlt

    _resource = dlt.resource
    _source = dlt.source
except ImportError:
    _resource = _make_dummy_dlt()
    _source = _make_dummy_dlt()


@_resource(
    name=JOTFORM_TABLE_NAME,
    write_disposition="replace",
    primary_key="id",
)
def jotform_submissions(
    api_key: str | None = None,
    form_ids: list[str] | None = None,
    limit_per_form: int = 100,
) -> Iterator[dict[str, Any]]:
    """DLT resource yielding Jotform submissions as documents."""
    yield from fetch_jotform_submissions(
        api_key=api_key,
        form_ids=form_ids,
        limit_per_form=limit_per_form,
    )


@_source(name=JOTFORM_SOURCE_NAME)
def jotform(
    api_key: str | None = None,
    form_ids: list[str] | None = None,
    limit_per_form: int = 100,
):
    """DLT source for Jotform form submissions and operational memory."""
    res = jotform_submissions(
        api_key=api_key,
        form_ids=form_ids,
        limit_per_form=limit_per_form,
    )
    setattr(res, DOCUMENT_SOURCE_ATTR, JOTFORM_SOURCE_NAME)
    return res
