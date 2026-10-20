from unittest.mock import MagicMock, patch

import pytest

from cognee_community_connector_twilio.twilio import (
    DOCUMENT_SOURCE_ATTR,
    TWILIO_TABLE_NAME,
    _format_message_markdown,
    twilio_source,
)


@pytest.fixture
def sample_message():
    return {
        "sid": "SM998877665544332211",
        "from": "+15551234567",
        "to": "+15559876543",
        "status": "delivered",
        "direction": "outbound-api",
        "date_sent": "2026-10-19 15:45:00 UTC",
        "price": "-0.0075",
        "price_unit": "USD",
        "body": "Your security verification code is 849201. Do not share this code.",
    }


def test_missing_credentials_raises_error():
    """Verify that omitting Twilio credentials raises ValueError."""
    with (
        patch.dict("os.environ", {}, clear=True),
        pytest.raises(ValueError, match="Twilio credentials required"),
    ):
        twilio_source(account_sid=None, auth_token=None)


def test_message_markdown_formatting_deterministic(sample_message):
    """Verify Markdown rendering is deterministic, structured, and contains message attributes."""
    md1 = _format_message_markdown(sample_message)
    md2 = _format_message_markdown(sample_message)

    assert md1 == md2  # Determinism guarantee
    assert "# Twilio Communication: [SMS] +15551234567 -> +15559876543" in md1
    assert "- **Message SID**: SM998877665544332211" in md1
    assert "- **Type**: SMS" in md1
    assert "- **From**: +15551234567" in md1
    assert "- **To**: +15559876543" in md1
    assert "- **Status**: delivered" in md1
    assert "Your security verification code is 849201" in md1


def test_twilio_source_extracts_messages(sample_message):
    """Verify that twilio_source runs snapshot extraction with document-mode attribute."""
    mock_client = MagicMock()

    def mock_request(method, url, auth, params=None, timeout=None):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "messages": [sample_message],
            "next_page_uri": None,
        }
        return resp

    mock_client.request.side_effect = mock_request

    source = twilio_source(
        account_sid="AC1234567890abcdef",
        auth_token="auth_secret_token",
        client=mock_client,
    )

    # Verify document-mode attribute is set for entity extraction
    assert getattr(source, DOCUMENT_SOURCE_ATTR) == "twilio"

    # Evaluate the resource items
    resources = list(source.selected_resources.values())
    assert len(resources) == 1
    resource = resources[0]
    assert resource.name == TWILIO_TABLE_NAME
    assert resource.write_disposition == "replace"

    items = list(resource())
    assert len(items) == 1
    assert items[0]["id"] == "SM998877665544332211"
    assert items[0]["from"] == "+15551234567"
    assert items[0]["to"] == "+15559876543"
    assert "# Twilio Communication: [SMS]" in items[0]["body"]
