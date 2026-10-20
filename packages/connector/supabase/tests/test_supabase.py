from unittest.mock import MagicMock, patch

import pytest
from cognee_community_connector_supabase.supabase import (
    DOCUMENT_SOURCE_ATTR,
    SupabaseConnector,
)


def test_init_missing_env(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    with pytest.raises(ValueError, match="Supabase URL must be provided"):
        SupabaseConnector(supabase_key="key")

    with pytest.raises(ValueError, match="Supabase API key must be provided"):
        SupabaseConnector(supabase_url="https://xyz.supabase.co")


def test_table_records_mocked():
    connector = SupabaseConnector(
        supabase_url="https://test.supabase.co",
        supabase_key="dummy_key",
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {"id": 42, "name": "Antigravity Agent", "role": "developer"},
        {"id": 43, "name": "Cognee Brain", "role": "memory"},
    ]

    with patch.object(connector.session, "get", return_value=mock_resp):
        records = list(connector.get_table_records(table_name="users"))
        assert len(records) == 2
        assert records[0]["id"] == "users_42"
        assert records[0]["table"] == "users"
        assert records[0][DOCUMENT_SOURCE_ATTR] == "supabase"
        assert records[0]["data"]["name"] == "Antigravity Agent"
