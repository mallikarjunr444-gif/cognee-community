# Cal.com Data-Source Connector for Cognee

Extracts bookings, meetings, attendees, and event types from [Cal.com](https://cal.com) into Cognee's cognitive graph memory.

## Features
- **Booking & Calendar Ingestion**: Extracts confirmed, cancelled, and upcoming meetings with attendee details.
- **Event Types**: Ingests scheduling slots and meeting lengths into contextual memory.
- **Cognitive Document Mode**: Emits `DOCUMENT_SOURCE_ATTR = "calcom"` for knowledge graph queries.
- **Resilient Transport**: Automatic retry on HTTP 429 rate limits.

## Installation
```bash
pip install -e packages/connector/calcom
```

## Configuration
```bash
export CALCOM_API_KEY="your-calcom-api-key"
```

## Quickstart
```python
from cognee_community_connector_calcom import CalcomConnector

connector = CalcomConnector()
for booking in connector.get_bookings():
    print(booking["title"], booking["startTime"])
```
