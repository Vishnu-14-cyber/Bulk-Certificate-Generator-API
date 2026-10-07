import pytest
from fastapi.testclient import TestClient
from app.certificate_generator import CertificateTemplateGenerator, CertificateGenerationError
from app.service import certificate_service


def test_individual_certificate_failure_isolation(client: TestClient, monkeypatch):
    """
    Critical requirement: A failure while generating one certificate must NOT
    prevent other valid certificates in the same job from being generated.
    The job status should identify successful and failed generations.
    """
    original_generate = certificate_service.generator.generate

    # Monkeypatch generator so that "ErrorProne User" fails, but others succeed
    def mock_generate(*args, **kwargs):
        recipient_name = kwargs.get("recipient_name", "")
        if "ErrorProne User" in recipient_name:
            raise CertificateGenerationError("Simulated font/filesystem corruption error for this recipient")
        return original_generate(*args, **kwargs)

    monkeypatch.setattr(certificate_service.generator, "generate", mock_generate)

    payload = {
        "event_name": "Resilient Systems Workshop",
        "issuer_name": "Chief Architect",
        "recipients": [
            {"name": "Valid Recipient One", "email": "one@example.com"},
            {"name": "ErrorProne User", "email": "error@example.com"},
            {"name": "Valid Recipient Two", "email": "two@example.com"}
        ]
    }

    # Execute synchronously to inspect results immediately
    response = client.post("/api/v1/jobs?process_sync=true", json=payload)
    assert response.status_code in (200, 202)
    job_id = response.json()["job_id"]

    # Retrieve job details
    status_res = client.get(f"/api/v1/jobs/{job_id}")
    assert status_res.status_code == 200
    job_data = status_res.json()

    # Verify overall job status is PARTIALLY_FAILED
    assert job_data["status"] == "PARTIALLY_FAILED"
    assert job_data["total_count"] == 3
    assert job_data["processed_count"] == 3
    assert job_data["success_count"] == 2
    assert job_data["failed_count"] == 1

    # Check recipient-level results
    recipients_by_name = {r["recipient_name"]: r for r in job_data["recipients"]}

    # Valid Recipient One must have SUCCEEDED
    assert recipients_by_name["Valid Recipient One"]["status"] == "SUCCESS"
    assert recipients_by_name["Valid Recipient One"]["download_pdf_url"] is not None

    # Valid Recipient Two must have SUCCEEDED
    assert recipients_by_name["Valid Recipient Two"]["status"] == "SUCCESS"
    assert recipients_by_name["Valid Recipient Two"]["download_pdf_url"] is not None

    # ErrorProne User must have FAILED with descriptive error
    failed_cert = recipients_by_name["ErrorProne User"]
    assert failed_cert["status"] == "FAILED"
    assert failed_cert["download_pdf_url"] is None
    assert "Simulated font/filesystem corruption error" in failed_cert["error_message"]


def test_job_with_all_failures_becomes_failed(client: TestClient, monkeypatch):
    """When all recipients in a job fail, the job status must be FAILED."""
    def mock_fail_all(*args, **kwargs):
        raise CertificateGenerationError("Global engine failure")

    monkeypatch.setattr(certificate_service.generator, "generate", mock_fail_all)

    payload = {
        "event_name": "Failure Test",
        "issuer_name": "Tester",
        "recipients": [
            {"name": "Alice"},
            {"name": "Bob"}
        ]
    }

    res = client.post("/api/v1/jobs?process_sync=true", json=payload)
    job_id = res.json()["job_id"]

    status_res = client.get(f"/api/v1/jobs/{job_id}")
    job_data = status_res.json()
    assert job_data["status"] == "FAILED"
    assert job_data["success_count"] == 0
    assert job_data["failed_count"] == 2
