# Plausible Analytics Data-Source Connector for Cognee

Extracts privacy-preserving website analytics, aggregate metrics, and traffic breakdowns from [Plausible Analytics](https://plausible.io) into Cognee's cognitive knowledge graph.

## Features
- **Aggregate Metrics**: Ingests total visitors, pageviews, bounce rates, and visit durations.
- **Traffic Breakdowns**: Ingests top pages (`event:page`), referrers (`visit:source`), countries, and devices.
- **Realtime Traffic**: Ingests active visitor counts.
- **Cognitive Document Mode**: Emits `DOCUMENT_SOURCE_ATTR = "plausible"` for knowledge graph modeling.
- **Cloud & Self-Hosted**: Supports custom base URLs.

## Installation
```bash
pip install -e packages/connector/plausible
```

## Configuration
```bash
export PLAUSIBLE_API_KEY="your-plausible-api-key"
export PLAUSIBLE_SITE_ID="yourdomain.com"
```

## Quickstart
```python
from cognee_community_connector_plausible import PlausibleConnector

connector = PlausibleConnector()
for page in connector.get_breakdown("event:page"):
    print(page["value"], page["visitors"])
```
