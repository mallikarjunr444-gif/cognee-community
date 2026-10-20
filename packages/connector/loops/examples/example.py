import os

from cognee_community_connector_loops import LoopsConnector


def main():
    api_key = os.environ.get("LOOPS_API_KEY", "loops_test_key")
    connector = LoopsConnector(api_key=api_key)

    print("--- Fetching Loops Contacts ---")
    for contact in connector.get_contacts():
        print(f"Contact: {contact['email']} (Subscribed: {contact['subscribed']})")

    print("\n--- Fetching Transactional Mails ---")
    for mail in connector.get_transactional_mails():
        print(f"Mail: {mail['name']} ({mail['status']})")


if __name__ == "__main__":
    main()
