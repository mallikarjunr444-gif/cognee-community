# Supabase Data-Source Connector for Cognee

Extracts relational tables, PostgreSQL records, and schema entities from [Supabase](https://supabase.com) into Cognee's cognitive graph memory.

## Features
- **Table Ingestion**: Connects via PostgREST to extract table rows as structured documents.
- **Cognitive Document Mode**: Emits `DOCUMENT_SOURCE_ATTR = "supabase"`.
- **Automatic Backoff**: Retries on transient HTTP errors and rate limits.

## Installation
```bash
pip install -e packages/connector/supabase
```

## Configuration
```bash
export SUPABASE_URL="https://yourproject.supabase.co"
export SUPABASE_KEY="your-anon-or-service-role-key"
```

## Quickstart
```python
from cognee_community_connector_supabase import SupabaseConnector

connector = SupabaseConnector()
for row in connector.get_table_records(table_name="products"):
    print(row["id"], row["data"])
```
