# Cognee Community Connector: Jotform

Production-ready data-source connector integrating [Jotform](https://www.jotform.com/) form submissions into [Cognee](https://github.com/topoteretes/cognee) for AI agent operational memory and knowledge graph reasoning.

Resolves [cognee#5968](https://github.com/topoteretes/cognee/issues/5968).

## Features
- **Form Schema Resolution**: Dynamically maps Jotform internal question IDs to human-readable question titles.
- **Snapshot Synchronization**: `write_disposition="replace"` preserves active submissions and allows automatic orphan cleanup for deletions.
- **Cognify Document Pipeline**: Tags documents with `cognee_document_source = "jotform"`, extracting entities, issues, properties, and customer requests.
- **Rate Limit Resilience**: Built-in exponential backoff on HTTP 429 and transient errors.

## Installation
```bash
pip install cognee-community-connector-jotform
```

## Quick Start
```python
import os
import asyncio
import cognee
from cognee_community_connector_jotform import jotform


async def main():
    os.environ["JOTFORM_API_KEY"] = "your_jotform_api_key"

    # Ingest all active forms or select specific form IDs
    await cognee.add(jotform(form_ids=["241234567890"]))
    await cognee.cognify()

    # Query your agent memory
    results = await cognee.search("Which properties have reported repeated HVAC issues?")
    for res in results:
        print(res)


if __name__ == "__main__":
    asyncio.run(main())
```

## Testing
```bash
pytest packages/connector/jotform/tests/
```
