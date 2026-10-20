# Loops.so Data-Source Connector for Cognee

Extracts contacts, audience properties, and transactional email campaigns from [Loops.so](https://loops.so) into Cognee's cognitive graph memory.

## Features
- **Contact Ingestion**: Ingests email addresses, user groups, custom attributes, and subscription statuses.
- **Transactional Campaigns**: Ingests transactional template identifiers and names.
- **Cognitive Document Mode**: Emits `DOCUMENT_SOURCE_ATTR = "loops"`.
- **Automatic Backoff**: Retries automatically on rate limits.

## Installation
```bash
pip install -e packages/connector/loops
```

## Configuration
```bash
export LOOPS_API_KEY="your-loops-api-key"
```

## Quickstart
```python
from cognee_community_connector_loops import LoopsConnector

connector = LoopsConnector()
for contact in connector.get_contacts():
    print(contact["email"], contact["userGroup"])
```
