# Cognee Community Connector: Twilio

A production-ready community data-source connector for [Twilio](https://twilio.com). Ingests SMS messages, WhatsApp conversations, delivery statuses, and verification history into [Cognee](https://github.com/topoteretes/cognee) as structured documents for AI agent memory and graph reasoning.

---

## Capabilities

* **Customer Messaging Memory**: Ingests SMS and WhatsApp communications, sender/recipient numbers, message bodies, timestamps, and delivery statuses.
* **Document Mode Support**: Marks resources with `DOCUMENT_SOURCE_ATTR = "twilio"` to route communication items through Cognee's cognify entity-extraction pipeline.
* **Full Snapshot with Forget-on-Delete**: Synchronizes with `write_disposition="replace"`. Deleted messages or privacy-scrubbed records in Twilio automatically drop out of the snapshot, triggering Cognee's `orphan_cleanup` to prune them from the knowledge graph and vector stores.
* **Resilient HTTP Transport**: Automatically handles rate limiting (HTTP 429) with exponential backoff and `Retry-After` header parsing.

---

## Installation

```bash
pip install cognee-community-connector-twilio
```

Or from source:

```bash
pip install -e packages/connector/twilio
```

---

## Quickstart

```python
import asyncio
import os
import cognee
from cognee_community_connector_twilio import twilio_source


async def main():
    # Configure Cognee dataset
    dataset_name = "customer_support_communications"

    # Create Twilio source
    source = twilio_source(
        account_sid=os.environ.get("TWILIO_ACCOUNT_SID"),
        auth_token=os.environ.get("TWILIO_AUTH_TOKEN"),
    )

    # Ingest and cognify into memory
    print("Syncing Twilio messages into Cognee memory ...")
    await cognee.remember(source, dataset_name=dataset_name)

    # Search knowledge graph for SMS conversations
    answer = await cognee.search(
        query_text="What verification codes or support messages were sent to customer +15551234567?",
        query_type=cognee.SearchType.GRAPH_COMPLETION,
        datasets=[dataset_name],
    )
    print("Graph search result:\n", answer)


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Running Tests

```bash
pytest packages/connector/twilio/tests
```
