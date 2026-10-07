import io
import time
from fastapi.testclient import TestClient


def test_create_job_sync_execution(client: TestClient):
    """Creating a job with process_sync=true must process and complete immediately."""
    payload = {
        "event_name": "API Mastery Bootcamp",
        "issuer_name": "Jane Doe",
        "recipients": [
            {"name": "Alice Johnson", "email": "alice@example.com"},
            {"name": "Bob Smith", "email": "bob@example.com"}
        ]
    }
    response = client.post("/api/v1/jobs?process_sync=true", json=payload)
    assert response.status_code == 202 or response.status_code == 200
    job_id = response.json()["job_id"]

    # Fetch status
    status_res = client.get(f"/api/v1/jobs/{job_id}")
    assert status_res.status_code == 200
    job_data = status_res.json()
    assert job_data["status"] == "COMPLETED"
    assert job_data["total_count"] == 2
    assert job_data["processed_count"] == 2
    assert job_data["success_count"] == 2
    assert job_data["failed_count"] == 0
    assert job_data["progress_percentage"] == 100.0
    assert len(job_data["recipients"]) == 2
    for r in job_data["recipients"]:
        assert r["status"] == "SUCCESS"
        assert r["download_pdf_url"] is not None
        assert r["download_png_url"] is not None


def test_create_job_async_background(client: TestClient):
    """Creating a job asynchronously must return 202 and finish in background."""
    payload = {
        "event_name": "Async Concurrency Workshop",
        "issuer_name": "Dr. Worker",
        "recipients": [
            {"name": "Charlie Chaplin"},
            {"name": "David Copperfield"}
        ]
    }
    response = client.post("/api/v1/jobs?process_sync=false", json=payload)
    assert response.status_code == 202
    data = response.json()
    job_id = data["job_id"]
    assert data["total_recipients"] == 2

    # Poll until background thread finishes
    max_wait = 15
    start = time.time()
    completed = False
    while time.time() - start < max_wait:
        status_res = client.get(f"/api/v1/jobs/{job_id}")
        assert status_res.status_code == 200
        job_data = status_res.json()
        if job_data["status"] == "COMPLETED":
            completed = True
            assert job_data["success_count"] == 2
            break
        time.sleep(0.3)

    assert completed, "Background job did not finish in time"


def test_list_jobs_endpoint(client: TestClient):
    """GET /api/v1/jobs should list all jobs."""
    # Create two jobs
    for i in range(2):
        client.post(
            "/api/v1/jobs?process_sync=true",
            json={
                "event_name": f"Event {i}",
                "issuer_name": "Issuer",
                "recipients": [{"name": f"User {i}"}]
            }
        )

    res = client.get("/api/v1/jobs?limit=10")
    assert res.status_code == 200
    jobs = res.json()
    assert isinstance(jobs, list)
    assert len(jobs) >= 2


def test_create_job_csv_upload(client: TestClient):
    """POST /api/v1/jobs/upload-csv should parse CSV and generate certificates."""
    csv_content = (
        "name,email,score,grade\n"
        "Grace Hopper,grace@navy.mil,99%,Distinction\n"
        "Ada Lovelace,ada@math.org,100%,Honors\n"
    )
    files = {"file": ("recipients.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    data = {
        "event_name": "Pioneers in Computing",
        "issuer_name": "Alan Turing",
        "process_sync": "true"
    }

    response = client.post("/api/v1/jobs/upload-csv", files=files, data=data)
    assert response.status_code == 202 or response.status_code == 200
    job_id = response.json()["job_id"]

    # Verify status
    status_res = client.get(f"/api/v1/jobs/{job_id}")
    assert status_res.status_code == 200
    job_data = status_res.json()
    assert job_data["status"] == "COMPLETED"
    assert job_data["total_count"] == 2
    assert job_data["success_count"] == 2
