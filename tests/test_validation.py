import pytest
from fastapi.testclient import TestClient


def test_validation_empty_recipients_fails(client: TestClient):
    """Submitting a request with an empty recipients list must fail validation."""
    payload = {
        "event_name": "Python Mastery",
        "issuer_name": "Dr. Sarah",
        "recipients": []
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "recipients" in str(data)


def test_validation_missing_event_name_fails(client: TestClient):
    """Submitting a request without event_name must fail validation."""
    payload = {
        "issuer_name": "Dr. Sarah",
        "recipients": [{"name": "Alice"}]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422


def test_validation_whitespace_event_name_fails(client: TestClient):
    """Submitting empty whitespace for event_name must fail validation."""
    payload = {
        "event_name": "   ",
        "issuer_name": "Dr. Sarah",
        "recipients": [{"name": "Alice"}]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422


def test_validation_missing_issuer_name_fails(client: TestClient):
    """Submitting a request without issuer_name must fail validation."""
    payload = {
        "event_name": "Cloud Summit",
        "recipients": [{"name": "Bob"}]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422


def test_validation_blank_recipient_name_fails(client: TestClient):
    """Submitting a recipient with blank/whitespace name must fail validation."""
    payload = {
        "event_name": "Cloud Summit",
        "issuer_name": "Director",
        "recipients": [
            {"name": "   "}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422


def test_validation_invalid_email_format_fails(client: TestClient):
    """Submitting a recipient with a malformed email must fail validation."""
    payload = {
        "event_name": "Cloud Summit",
        "issuer_name": "Director",
        "recipients": [
            {"name": "Charlie", "email": "not-an-email-address"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422


def test_validation_valid_input_succeeds(client: TestClient):
    """Submitting valid data should be accepted with HTTP 202."""
    payload = {
        "title": "Certificate of Achievement",
        "event_name": "Full Stack Mastery",
        "issue_date": "2026-10-07",
        "issuer_name": "Prof. Miller",
        "issuer_title": "Head of Faculty",
        "template_style": "classic_gold",
        "recipients": [
            {
                "name": "Diana Prince",
                "email": "diana@example.com",
                "custom_attributes": {"score": "98%", "grade": "Distinction"}
            }
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["total_recipients"] == 1
    assert data["status"] in ("PENDING", "PROCESSING", "COMPLETED")
