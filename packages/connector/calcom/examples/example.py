import os

from cognee_community_connector_calcom import CalcomConnector


def main():
    api_key = os.environ.get("CALCOM_API_KEY", "cal_test_dummy_key")
    connector = CalcomConnector(api_key=api_key)

    print("--- Fetching Bookings ---")
    for booking in connector.get_bookings():
        print(f"[{booking['id']}] {booking['title']} ({booking['status']})")

    print("\n--- Fetching Event Types ---")
    for event_type in connector.get_event_types():
        print(f"Event: {event_type['title']} ({event_type['length']} mins)")


if __name__ == "__main__":
    main()
