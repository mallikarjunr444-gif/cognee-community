# Resend Data-Source Connector for Cognee

Extracts sent transactional emails, audience segments, and subscriber lists from [Resend](https://resend.com) into Cognee's cognitive memory graph.

## Features
- **Transactional Email Ingestion**: Extracts sent messages, subjects, timestamps, and full HTML/text content.
- **Audience & Contact Tracking**: Ingests audience lists and contact records.
- **Cognitive Document Mode**: Emits `DOCUMENT_SOURCE_ATTR = "resend"` for relationship extraction.
- **Resilient Transport**: Automatic retry on HTTP 429 with `Retry-After` backoff.

## Installation
```bash
pip install -e packages/connector/resend
```

## Configuration
Set your Resend API key:
```bash
export RESEND_API_KEY="re_..."
```

## Quickstart
```python
from cognee_community_connector_resend import ResendConnector

connector = ResendConnector()
for email in connector.get_emails():
    print(email["subject"])
```
