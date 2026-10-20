from unittest.mock import MagicMock, patch

import pytest
from cognee_community_connector_stripe.stripe import (
    DOCUMENT_SOURCE_ATTR,
    StripeConnector,
)


def test_init_missing_key(monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.delenv("STRIPE_API_KEY", raising=False)
    with pytest.raises(ValueError, match="Stripe API key must be provided"):
        StripeConnector()


def test_charges_mocked():
    connector = StripeConnector(api_key="sk_test_123")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [
            {
                "id": "ch_3Pq123",
                "amount": 4900,
                "currency": "usd",
                "customer": "cus_N789",
                "status": "succeeded",
                "paid": True,
                "description": "Monthly Agent Subscription",
                "created": 1729400000,
            }
        ]
    }

    with patch.object(connector.session, "get", return_value=mock_resp):
        charges = list(connector.get_charges(limit=10))
        assert len(charges) == 1
        assert charges[0]["id"] == "ch_3Pq123"
        assert charges[0]["amount"] == 4900
        assert charges[0][DOCUMENT_SOURCE_ATTR] == "stripe"
        assert charges[0]["status"] == "succeeded"


def test_subscriptions_mocked():
    connector = StripeConnector(api_key="sk_test_123")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [
            {
                "id": "sub_456",
                "customer": "cus_N789",
                "status": "active",
                "current_period_start": 1729400000,
                "current_period_end": 1732078400,
                "cancel_at_period_end": False,
            }
        ]
    }

    with patch.object(connector.session, "get", return_value=mock_resp):
        subs = list(connector.get_subscriptions(limit=10))
        assert len(subs) == 1
        assert subs[0]["id"] == "sub_456"
        assert subs[0]["customer"] == "cus_N789"
        assert subs[0][DOCUMENT_SOURCE_ATTR] == "stripe"
        assert subs[0]["status"] == "active"
