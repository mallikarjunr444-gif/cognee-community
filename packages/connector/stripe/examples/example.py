import os

from cognee_community_connector_stripe import StripeConnector


def main():
    api_key = os.environ.get("STRIPE_SECRET_KEY", "sk_test_dummy_key")
    connector = StripeConnector(api_key=api_key)

    print("--- Fetching Stripe Charges ---")
    for charge in connector.get_charges(limit=5):
        ch_id = charge["id"]
        amt = f"{charge['amount']} {charge['currency']}"
        print(f"Charge: {ch_id} -> {amt} ({charge['status']})")

    print("\n--- Fetching Stripe Subscriptions ---")
    for sub in connector.get_subscriptions(limit=5):
        print(f"Sub: {sub['id']} -> Customer: {sub['customer']} ({sub['status']})")


if __name__ == "__main__":
    main()
