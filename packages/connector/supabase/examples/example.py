import os

from cognee_community_connector_supabase import SupabaseConnector


def main():
    url = os.environ.get("SUPABASE_URL", "https://xyzcompany.supabase.co")
    key = os.environ.get("SUPABASE_KEY", "sb_anon_test_key")
    connector = SupabaseConnector(supabase_url=url, supabase_key=key)

    print("--- Fetching Supabase Table Records ---")
    for record in connector.get_table_records(table_name="users", limit=5):
        print(f"Record: {record['id']} -> {record['data']}")


if __name__ == "__main__":
    main()
