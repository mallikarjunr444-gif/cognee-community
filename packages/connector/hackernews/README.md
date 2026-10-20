# Hacker News Data-Source Connector for Cognee

Extracts top stories, Ask HN, and discussions from Hacker News via Firebase API into Cognee's cognitive graph memory.

## Features
- **Public & Unauthenticated**: Directly accesses the official Hacker News Firebase API without credentials.
- **Top Stories & Ask HN**: Ingests story titles, scores, authors, comments, and links.
- **Cognitive Document Mode**: Emits `DOCUMENT_SOURCE_ATTR = "hackernews"` for graph retrieval.

## Installation
```bash
pip install -e packages/connector/hackernews
```

## Quickstart
```python
from cognee_community_connector_hackernews import HackerNewsConnector

connector = HackerNewsConnector()
for story in connector.get_top_stories(limit=10):
    print(story["title"], story["score"])
```
