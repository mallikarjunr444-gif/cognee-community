"""Unit tests for Jotform community connector."""

from unittest.mock import MagicMock

import pytest
from cognee_community_connector_jotform.jotform import (
    fetch_jotform_submissions,
    format_answer_value,
    render_submission_document,
)


def test_format_answer_value():
    assert format_answer_value(None) == ""
    assert format_answer_value("123 Main St") == "123 Main St"
    assert format_answer_value(["HVAC", "Plumbing"]) == "HVAC, Plumbing"
    assert format_answer_value({"first": "John", "last": "Doe"}) == "first: John, last: Doe"


def test_render_submission_document():
    submission = {
        "id": "1001",
        "form_id": "form_888",
        "created_at": "2026-10-21 14:30:00",
        "status": "ACTIVE",
        "answers": {
            "1": {"text": "Property Address", "answer": "742 Evergreen Terrace"},
            "2": {"text": "Service Type", "answer": "HVAC Repair"},
        },
    }
    questions = {"1": "Address", "2": "Issue"}
    doc = render_submission_document(submission, "Maintenance Intake", questions)

    assert "Jotform Submission: Maintenance Intake (#1001)" in doc
    assert "742 Evergreen Terrace" in doc
    assert "HVAC Repair" in doc
    assert "Form ID:** form_888" in doc


def test_fetch_jotform_submissions():
    mock_questions_resp = MagicMock()
    mock_questions_resp.status_code = 200
    mock_questions_resp.json.return_value = {
        "content": {
            "1": {"text": "Full Name"},
            "2": {"text": "Problem Description"},
        }
    }

    mock_form_meta_resp = MagicMock()
    mock_form_meta_resp.status_code = 200
    mock_form_meta_resp.json.return_value = {"content": {"title": "Tenant Intake"}}

    mock_subs_resp = MagicMock()
    mock_subs_resp.status_code = 200
    mock_subs_resp.json.return_value = {
        "content": [
            {
                "id": "sub_99",
                "form_id": "form_1",
                "created_at": "2026-10-21",
                "status": "ACTIVE",
                "answers": {
                    "1": {"answer": "Alice Smith"},
                    "2": {"answer": "Heater stopped working"},
                },
            }
        ]
    }

    def mock_request(method, url, **kwargs):
        if "questions" in url:
            return mock_questions_resp
        elif "submissions" in url:
            return mock_subs_resp
        else:
            return mock_form_meta_resp

    mock_client = MagicMock()
    mock_client.request.side_effect = mock_request

    items = list(
        fetch_jotform_submissions(
            api_key="mock_key",
            form_ids=["form_1"],
            client=mock_client,
        )
    )
    assert len(items) == 1
    doc = items[0]
    assert doc["id"] == "jotform_form_1_sub_99"
    assert "Alice Smith" in doc["text"]
    assert "Heater stopped working" in doc["text"]
    assert doc["external_metadata"]["source"] == "jotform"
    assert doc["external_metadata"]["form_id"] == "form_1"


def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("JOTFORM_API_KEY", raising=False)
    with pytest.raises(ValueError, match="JOTFORM_API_KEY must be provided"):
        list(fetch_jotform_submissions(api_key=None))
