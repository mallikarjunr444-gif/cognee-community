# Stripe Data-Source Connector for Cognee

Extracts charges, customer subscriptions, and billing transactions from [Stripe](https://stripe.com) into Cognee's cognitive graph memory.

## Features
- **Charge & Payment Ingestion**: Ingests charge amounts, currencies, payment statuses, and customer references.
- **Subscription Tracking**: Ingests active subscriptions, plans, and renewal dates.
- **Cognitive Document Mode**: Emits `DOCUMENT_SOURCE_ATTR = "stripe"`.
- **Automatic Backoff**: Retries automatically on rate limits.

## Installation
```bash
pip install -e packages/connector/stripe
```

## Configuration
```bash
export STRIPE_SECRET_KEY="sk_live_or_test_key"
```

## Quickstart
```python
from cognee_community_connector_stripe import StripeConnector

connector = StripeConnector()
for charge in connector.get_charges():
    print(charge["id"], charge["amount"], charge["currency"])
```
