import os

from cognee_community_connector_plausible import PlausibleConnector


def main():
    api_key = os.environ.get("PLAUSIBLE_API_KEY", "plausible_key_test")
    site_id = os.environ.get("PLAUSIBLE_SITE_ID", "example.com")
    connector = PlausibleConnector(api_key=api_key, site_id=site_id)

    print("--- Aggregate Stats (30 Days) ---")
    for stat in connector.get_aggregate_stats(period="30d"):
        print(f"Visitors: {stat['visitors']} | Pageviews: {stat['pageviews']}")

    print("\n--- Top Pages ---")
    for page in connector.get_breakdown(property_name="event:page", limit=5):
        print(f"Page: {page['value']} -> {page['visitors']} visitors")


if __name__ == "__main__":
    main()
