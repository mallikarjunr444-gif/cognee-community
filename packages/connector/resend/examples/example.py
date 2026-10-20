import os

from cognee_community_connector_resend import ResendConnector


def main():
    api_key = os.environ.get("RESEND_API_KEY", "re_test_key_placeholder")
    connector = ResendConnector(api_key=api_key)

    print("--- Fetching Sent Emails ---")
    for email in connector.get_emails(limit=5):
        print(f"[{email['id']}] Subject: {email['subject']} (To: {email['to']})")

    print("\n--- Fetching Audiences ---")
    for audience in connector.get_audiences():
        print(f"Audience: {audience['name']} (Contacts: {len(audience.get('contacts', []))})")


if __name__ == "__main__":
    main()
