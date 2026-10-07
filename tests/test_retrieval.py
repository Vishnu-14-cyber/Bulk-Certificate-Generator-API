import io
import zipfile
from fastapi.testclient import TestClient


def test_retrieve_certificate_metadata_and_downloads(client: TestClient):
    """Verifies single certificate retrieval in both PDF and PNG formats."""
    # Create and generate a certificate
    payload = {
        "event_name": "Cloud Security Conference",
        "issuer_name": "Chief Security Officer",
        "recipients": [
            {"name": "Evelyn Harper", "email": "evelyn@security.io"}
        ]
    }
    create_res = client.post("/api/v1/jobs?process_sync=true", json=payload)
    job_id = create_res.json()["job_id"]

    # Get job to find certificate ID
    job_res = client.get(f"/api/v1/jobs/{job_id}")
    cert_id = job_res.json()["recipients"][0]["id"]
    cert_code = job_res.json()["recipients"][0]["certificate_code"]

    # 1. Retrieve metadata
    meta_res = client.get(f"/api/v1/certificates/{cert_id}")
    assert meta_res.status_code == 200
    meta = meta_res.json()
    assert meta["recipient_name"] == "Evelyn Harper"
    assert meta["status"] == "SUCCESS"
    assert meta["certificate_code"] == cert_code

    # 2. Download PDF
    pdf_res = client.get(f"/api/v1/certificates/{cert_id}/download?format=pdf")
    assert pdf_res.status_code == 200
    assert "application/pdf" in pdf_res.headers["content-type"]
    assert pdf_res.content.startswith(b"%PDF")

    # 3. Download PNG
    png_res = client.get(f"/api/v1/certificates/{cert_id}/download?format=png")
    assert png_res.status_code == 200
    assert "image/png" in png_res.headers["content-type"]
    assert png_res.content.startswith(b"\x89PNG")

    # 4. View PNG (Inline)
    view_res = client.get(f"/api/v1/certificates/{cert_id}/view?format=png")
    assert view_res.status_code == 200
    assert "inline" in view_res.headers.get("content-disposition", "")


def test_retrieve_job_zip_archive(client: TestClient):
    """Verifies downloading all job certificates packaged in a ZIP archive."""
    payload = {
        "event_name": "Full Stack Intensive",
        "issuer_name": "Director of Admissions",
        "recipients": [
            {"name": "Student Alpha"},
            {"name": "Student Beta"}
        ]
    }
    create_res = client.post("/api/v1/jobs?process_sync=true", json=payload)
    job_id = create_res.json()["job_id"]

    zip_res = client.get(f"/api/v1/jobs/{job_id}/download-zip?format=pdf")
    assert zip_res.status_code == 200
    assert "application/zip" in zip_res.headers["content-type"]

    # Check zip contents
    zip_bytes = io.BytesIO(zip_res.content)
    with zipfile.ZipFile(zip_bytes, "r") as z:
        names = z.namelist()
        assert len(names) == 2
        for n in names:
            assert n.endswith(".pdf")


def test_verify_certificate_endpoint(client: TestClient):
    """Verifies public certificate verification API."""
    payload = {
        "event_name": "Blockchain & Cryptography",
        "issuer_name": "Dr. Satoshi",
        "recipients": [{"name": "Hal Finney"}]
    }
    create_res = client.post("/api/v1/jobs?process_sync=true", json=payload)
    job_id = create_res.json()["job_id"]

    job_res = client.get(f"/api/v1/jobs/{job_id}")
    cert_code = job_res.json()["recipients"][0]["certificate_code"]

    # Verify with valid code
    verify_res = client.get(f"/api/v1/certificates/verify/{cert_code}")
    assert verify_res.status_code == 200
    v_data = verify_res.json()
    assert v_data["valid"] is True
    assert v_data["recipient_name"] == "Hal Finney"
    assert v_data["status"] == "AUTHENTIC_AND_VERIFIED"

    # Verify with invalid code
    bad_res = client.get("/api/v1/certificates/verify/NON-EXISTENT-CODE")
    assert bad_res.status_code == 200
    bad_data = bad_res.json()
    assert bad_data["valid"] is False


def test_retrieval_404_handling(client: TestClient):
    """Test 404 for non-existent entities."""
    res_bad_job = client.get("/api/v1/jobs/00000000-0000-0000-0000-000000000000")
    assert res_bad_job.status_code == 404

    res_bad_cert = client.get("/api/v1/certificates/00000000-0000-0000-0000-000000000000")
    assert res_bad_cert.status_code == 404
