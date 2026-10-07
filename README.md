# CertiForge - Bulk Certificate Generator API & Dashboard

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)](https://www.sqlalchemy.org/)
[![Tests](https://img.shields.io/badge/pytest-Passing-brightgreen.svg)](https://docs.pytest.org/)

**CertiForge** is a high-throughput, fault-isolated backend API and real-time interactive frontend dashboard for generating, tracking, and retrieving professional certificates in bulk.

Built specifically to handle large rosters of participants after events, workshops, or training courses with **guaranteed recipient-level fault isolation**, concurrent background generation, dual PDF/PNG exports, automated ZIP archive bundling, and public certificate verification.

---

## 📑 Table of Contents

1. [Features & Capabilities](#-features--capabilities)
2. [Project Architecture](#-project-architecture)
3. [Setup & Installation](#-setup--installation)
4. [Running the Application](#-running-the-application)
5. [Running Tests](#-running-tests)
6. [Submitting Certificate Requests](#-submitting-certificate-requests)
   - [A. Via Interactive Web Dashboard](#a-via-interactive-web-dashboard)
   - [B. Via JSON API (`POST /api/v1/jobs`)](#b-via-json-api-post-apiv1jobs)
   - [C. Via CSV File Upload (`POST /api/v1/jobs/upload-csv`)](#c-via-csv-file-upload-post-apiv1jobsupload-csv)
7. [Tracking Status & Progress](#-tracking-status--progress)
8. [Retrieving Generated Certificates](#-retrieving-generated-certificates)
   - [Individual PDF / PNG Download](#individual-pdf--png-download)
   - [Inline Image / PDF Preview](#inline-image--pdf-preview)
   - [Bulk ZIP Archive Download](#bulk-zip-archive-download)
9. [Public Certificate Verification](#-public-certificate-verification)
10. [Important Implementation & Design Decisions](#-important-implementation--design-decisions)
    - [Framework Choice: FastAPI](#1-framework-choice-fastapi)
    - [Relational Database & Concurrency: SQLite with WAL Mode](#2-relational-database--concurrency-sqlite-with-wal-mode)
    - [Bulk Generation: Asynchronous Worker Threadpool](#3-bulk-generation-asynchronous-worker-threadpool)
    - [Fault Isolation: Independent Recipient Processing](#4-fault-isolation-independent-recipient-processing)
    - [Certificate Template Engine: High-Resolution Pillow Vector & Raster](#5-certificate-template-engine-high-resolution-pillow-vector--raster)
11. [API Endpoints Reference](#-api-endpoints-reference)
12. [Interview FAQ & Design Justifications](#-interview-faq--design-justifications)

---

## 🚀 Features & Capabilities

- **⚡ Bulk Processing Engine**: Accepts hundreds or thousands of recipients in a single API call via JSON or CSV file upload.
- **🛡️ Strict Fault Isolation**: A bad record or failure during generation for one recipient **never prevents** other valid certificates in the same batch from completing.
- **📄 Dual Format Generation**: Every certificate is rendered in both crisp **PDF** (for official printing) and high-res **PNG** (for web displays and social sharing).
- **📦 1-Click ZIP Archive Packaging**: Download all successfully generated certificates in an entire job as a single compressed ZIP file.
- **🎨 Predefined Professional Template**: Includes double-rule ornamental borders, star burst crests, presentation typography, digital signature lines, and security verification strips with multiple theme styles (`classic_gold`, `modern_blue`, `emerald_honor`).
- **🔍 Public Authenticity Verification**: Verify any certificate instantly by its unique verification code (e.g. `CERT-2026-F98B-2A10`) or UUID.
- **💻 Embedded Web Studio & Monitor**: Full-featured web UI at `http://127.0.0.1:8000/` featuring real-time polling progress bars, template mockup preview, recipient rosters, image modal previews, and verification portal.
- **📖 Auto-Generated OpenAPI Docs**: Interactive Swagger documentation at `/docs` and ReDoc at `/redoc`.

---

## 🏗️ Project Architecture

```
Bulk Certificate Generator API/
├── app/
│   ├── __init__.py
│   ├── config.py                 # Application configuration & storage settings
│   ├── database.py               # SQLAlchemy engine, WAL pragma, session management
│   ├── models.py                 # DB models: Job and RecipientCertificate
│   ├── schemas.py                # Pydantic schemas (validations, responses)
│   ├── certificate_generator.py  # Predefined template rendering engine (Pillow)
│   ├── service.py                # Job orchestration, background workers, ZIP packaging
│   ├── main.py                   # FastAPI application factory, lifespan, CORS, web UI
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py             # REST API endpoints
│   ├── static/
│   │   ├── style.css             # Responsive modern stylesheet
│   │   └── app.js                # Frontend controller (live polling, previews)
│   └── templates/
│       └── index.html            # Web dashboard
├── storage/
│   └── certificates/             # Generated certificate PDF and PNG assets
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # Isolated test database and storage fixtures
│   ├── test_validation.py        # Input validation test suite
│   ├── test_generation.py        # Template rendering & file validation tests
│   ├── test_jobs_api.py          # Job creation, polling, CSV upload tests
│   ├── test_failures.py          # Individual failure isolation tests
│   └── test_retrieval.py         # File downloads, ZIP archive, and verification tests
├── requirements.txt              # Production dependencies
├── run.py                        # Server launcher script
├── run_tests.py                  # Automated test runner script
├── sample_recipients.csv         # Clean demo batch CSV
├── fault_demo_recipients.csv     # Demo batch with intentional errors for testing
└── README.md                     # Comprehensive documentation
```

---

## 🛠️ Setup & Installation

### 1. Prerequisites
- Python 3.10 or higher (Tested and fully compatible with Python 3.10 through Python 3.14 on Windows, Linux, and macOS).

### 2. Create and Activate Virtual Environment
```bash
# Clone or open the repository directory
cd "Bulk Certificate Generator API"

# Create a virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (CMD):
.\venv\Scripts\activate.bat
# Linux/macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🚦 Running the Application

### Option A: Using the Launcher Script
```bash
python run.py
```

### Option B: Using Uvicorn CLI Directly
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Once started, access:
- **Web UI & Dashboard**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative ReDoc Docs**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 🧪 Running Tests

A comprehensive test suite covers all requirements:
1. **Input validation** (missing fields, blank names, invalid emails, batch limits)
2. **Template generation** (file creation, binary headers, theme variants, auto-scaling)
3. **Job creation and progress tracking** (synchronous vs asynchronous background execution)
4. **Fault isolation** (simulated recipient errors ensuring valid certificates succeed)
5. **Retrieving generated certificates** (single PDF/PNG downloads, inline preview, ZIP archives, public verification)

Run all tests with:
```bash
# Run using the test runner script:
python run_tests.py

# Or run pytest directly:
pytest tests/ -v
```

---

## 📤 Submitting Certificate Requests

### A. Via Interactive Web Dashboard
1. Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in any browser.
2. Enter Event Name, Certificate Title, and Issuer Information.
3. Choose a template theme (`Classic Gold`, `Modern Blue`, or `Emerald Honor`).
4. Click **"Load Sample Batch"** or drag-and-drop the provided `sample_recipients.csv`.
5. Click **"Generate Certificates in Bulk"**. The dashboard immediately opens the live monitor showing real-time progress bars and certificate cards!

---

### B. Via JSON API (`POST /api/v1/jobs`)

#### Request:
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Certificate of Completion",
    "event_name": "Cloud Native Architecture Masterclass 2026",
    "issue_date": "2026-10-07",
    "issuer_name": "Dr. Arthur Pendelton",
    "issuer_title": "Chief Academic Officer",
    "template_style": "classic_gold",
    "recipients": [
      {
        "name": "Sophia Reynolds",
        "email": "sophia.reynolds@example.com",
        "custom_attributes": { "grade": "Distinction", "score": "99%" }
      },
      {
        "name": "Marcus Chen",
        "email": "marcus.chen@example.com",
        "custom_attributes": { "grade": "Honors", "score": "94%" }
      }
    ]
  }'
```

#### Response (`HTTP 202 Accepted`):
```json
{
  "job_id": "a9e63481-9b1e-450a-9d93-36c1e34b9d01",
  "status": "PROCESSING",
  "message": "Certificate generation job created and processing has started.",
  "total_recipients": 2,
  "status_url": "/jobs/a9e63481-9b1e-450a-9d93-36c1e34b9d01",
  "check_status_api": "/api/v1/jobs/a9e63481-9b1e-450a-9d93-36c1e34b9d01",
  "created_at": "2026-10-07T06:30:00Z"
}
```

> **Note on Synchronous Processing**: To process synchronously before responding, simply append `?process_sync=true` to the URL.

---

### C. Via CSV File Upload (`POST /api/v1/jobs/upload-csv`)

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/jobs/upload-csv" \
  -F "file=@sample_recipients.csv" \
  -F "event_name=Cloud Native Architecture Masterclass" \
  -F "issuer_name=Dr. Arthur Pendelton" \
  -F "issuer_title=Chief Academic Officer" \
  -F "template_style=classic_gold"
```

---

## 📊 Tracking Status & Progress

Clients can poll `GET /api/v1/jobs/{job_id}` at any time.

```bash
curl -X GET "http://127.0.0.1:8000/api/v1/jobs/a9e63481-9b1e-450a-9d93-36c1e34b9d01"
```

#### Response Example:
```json
{
  "id": "a9e63481-9b1e-450a-9d93-36c1e34b9d01",
  "title": "Certificate of Completion",
  "event_name": "Cloud Native Architecture Masterclass 2026",
  "issue_date": "2026-10-07",
  "issuer_name": "Dr. Arthur Pendelton",
  "issuer_title": "Chief Academic Officer",
  "template_style": "classic_gold",
  "status": "COMPLETED",
  "total_count": 2,
  "processed_count": 2,
  "success_count": 2,
  "failed_count": 0,
  "progress_percentage": 100.0,
  "created_at": "2026-10-07T06:30:00Z",
  "updated_at": "2026-10-07T06:30:02Z",
  "completed_at": "2026-10-07T06:30:02Z",
  "status_url": "/jobs/a9e63481-9b1e-450a-9d93-36c1e34b9d01",
  "zip_download_url": "/api/v1/jobs/a9e63481-9b1e-450a-9d93-36c1e34b9d01/download-zip?format=pdf",
  "recipients": [
    {
      "id": "6d1234a5-9271-460b-8d5f-1482f3478912",
      "job_id": "a9e63481-9b1e-450a-9d93-36c1e34b9d01",
      "recipient_name": "Sophia Reynolds",
      "recipient_email": "sophia.reynolds@example.com",
      "certificate_code": "CERT-2026-A1B2-C3D4",
      "status": "SUCCESS",
      "error_message": null,
      "pdf_filename": "6d1234a5-9271-460b-8d5f-1482f3478912.pdf",
      "png_filename": "6d1234a5-9271-460b-8d5f-1482f3478912.png",
      "file_size_bytes": 142580,
      "download_pdf_url": "/api/v1/certificates/6d1234a5-9271-460b-8d5f-1482f3478912/download?format=pdf",
      "download_png_url": "/api/v1/certificates/6d1234a5-9271-460b-8d5f-1482f3478912/download?format=png",
      "view_url": "/api/v1/certificates/6d1234a5-9271-460b-8d5f-1482f3478912/view?format=png"
    }
  ]
}
```

---

## 📥 Retrieving Generated Certificates

### Individual PDF / PNG Download
Downloads the file as an attachment:
```bash
# Download PDF
curl -O -J "http://127.0.0.1:8000/api/v1/certificates/{certificate_id}/download?format=pdf"

# Download PNG
curl -O -J "http://127.0.0.1:8000/api/v1/certificates/{certificate_id}/download?format=png"
```

### Inline Image / PDF Preview
Opens the certificate preview in the browser (`Content-Disposition: inline`):
```bash
http://127.0.0.1:8000/api/v1/certificates/{certificate_id}/view?format=png
```

### Bulk ZIP Archive Download
Downloads an archive containing all successfully generated certificates in the batch:
```bash
curl -O -J "http://127.0.0.1:8000/api/v1/jobs/{job_id}/download-zip?format=pdf"
```

---

## 🔐 Public Certificate Verification

Anyone can verify an issued certificate using its unique code:
```bash
curl "http://127.0.0.1:8000/api/v1/certificates/verify/CERT-2026-A1B2-C3D4"
```

#### Response:
```json
{
  "valid": true,
  "certificate_code": "CERT-2026-A1B2-C3D4",
  "recipient_name": "Sophia Reynolds",
  "title": "Certificate of Completion",
  "event_name": "Cloud Native Architecture Masterclass 2026",
  "issue_date": "2026-10-07",
  "issuer_name": "Dr. Arthur Pendelton",
  "issuer_title": "Chief Academic Officer",
  "status": "AUTHENTIC_AND_VERIFIED",
  "verified_at": "2026-10-07T06:35:00Z"
}
```

---

## 💡 Important Implementation & Design Decisions

### 1. Framework Choice: FastAPI
- **Decision**: Selected **FastAPI** over Flask or Django.
- **Reasoning**:
  - Native asynchronous concurrency support and non-blocking I/O.
  - Automatic JSON schema generation and interactive Swagger/OpenAPI documentation at `/docs`.
  - Type-safe data validation via Pydantic v2.
  - Minimal boilerplate with fast execution speeds.

### 2. Relational Database & Concurrency: SQLite with WAL Mode
- **Decision**: SQLite with SQLAlchemy 2.0 ORM, configured with **Write-Ahead Logging (`WAL`)** mode.
- **Reasoning**:
  - Zero-configuration setup: runs immediately on any developer workstation or evaluation environment without requiring Docker or external PostgreSQL servers.
  - Enabling `PRAGMA journal_mode=WAL` allows multiple concurrent readers (e.g. status polling requests) while the background worker thread writes updates, completely avoiding `sqlite3.OperationalError: database is locked` issues.
  - Clean abstraction: Simply setting `DATABASE_URL=postgresql://user:pass@localhost:5432/cert_db` in `.env` immediately switches the engine to PostgreSQL for production deployments.

### 3. Bulk Generation: Asynchronous Worker Threadpool
- **Decision**: The API returns `202 Accepted` immediately upon receiving a batch and offloads generation to a dedicated `ThreadPoolExecutor` worker pool.
- **Reasoning**:
  - Generating 500 certificates involves rendering and file I/O that could take 10–30 seconds. A synchronous HTTP request would risk client-side network timeouts.
  - The client receives a `job_id` and can monitor real-time progress via polling.
  - An optional query parameter (`?process_sync=true`) is also provided for test suites and scripts that prefer synchronous completion.

### 4. Fault Isolation: Independent Recipient Processing
- **Decision**: Individual failures never abort the batch.
- **Reasoning**:
  - In real-world events, 1 or 2 invalid recipient entries (e.g. corrupt characters, missing fonts, or bad email format) must never discard certificates for the other 98 attendees.
  - The generation loop wraps each recipient in a try/except block. Failed certificates are marked `status=FAILED` with a detailed `error_message`, while valid certificates continue processing.
  - Overall job status transparently reflects the outcome: `COMPLETED` (100% success), `PARTIALLY_FAILED` (mixed), or `FAILED` (0% success).

### 5. Certificate Template Engine: High-Resolution Pillow Vector & Raster
- **Decision**: Pillow (PIL) for graphics rendering, outputting both PNG and high-resolution PDF.
- **Reasoning**:
  - Heavy HTML-to-PDF libraries like WeasyPrint require complex OS-level C libraries (`pango`, `cairo`, `glib`) that frequently fail to install across Windows and macOS developer machines.
  - Pillow is self-contained, blazingly fast (renders in ~15-25ms per certificate), produces pixel-perfect ornamental borders, seals, and text, and converts directly to official PDF.
  - Dynamic font auto-scaling prevents text overflow for long names.

---

## 📋 API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/jobs` | Submit bulk certificate generation job (JSON) |
| `POST` | `/api/v1/jobs/upload-csv` | Submit bulk certificate generation job via CSV upload |
| `GET` | `/api/v1/jobs` | List recent jobs with status summaries & pagination |
| `GET` | `/api/v1/jobs/{job_id}` | Get job status, percentage, metrics, and recipient list |
| `GET` | `/api/v1/jobs/{job_id}/download-zip` | Download all generated certificates as a single ZIP |
| `GET` | `/api/v1/certificates/{id}` | Get metadata for an individual certificate |
| `GET` | `/api/v1/certificates/{id}/download` | Download single certificate file (PDF or PNG) |
| `GET` | `/api/v1/certificates/{id}/view` | Inline browser preview of certificate (PNG or PDF) |
| `GET` | `/api/v1/certificates/verify/{code_or_id}` | Public verification of certificate authenticity |
| `DELETE` | `/api/v1/jobs/{job_id}` | Delete a job and delete generated assets from disk |
| `GET` | `/health` | Health check endpoint |
| `GET` | `/` | Web Application Dashboard |
| `GET` | `/docs` | Interactive OpenAPI Swagger UI |

---

## 🎯 Interview FAQ & Design Justifications

**Q1: How does your system isolate failures?**  
> **Answer**: In `CertificateService._process_job_worker`, each recipient is processed independently within an isolated `try...except` block. If Pillow encounters an error or recipient validation fails, that specific recipient row is committed with `status=FAILED` and `error_message=<reason>`, and the loop immediately advances to the next recipient. The overall job status is flagged as `PARTIALLY_FAILED` if some succeeded and some failed.

**Q2: How would you scale this to 100,000 certificates?**  
> **Answer**: 
> 1. **Message Broker**: Swap the local `ThreadPoolExecutor` with **Celery + Redis / RabbitMQ**.
> 2. **Object Storage**: Store certificate files in **AWS S3 / Google Cloud Storage** with pre-signed download URLs rather than local disk.
> 3. **Batch Splitting**: Partition 100,000 recipients into chunks of 100 and distribute them across auto-scaling worker nodes.
> 4. **Database**: Use a managed PostgreSQL cluster with connection pooling (e.g. PgBouncer).

**Q3: Why did you provide both PNG and PDF?**  
> **Answer**: Organizations need PDFs for printing, signing, and archival, whereas recipients need instant PNG previews to display on web dashboards and share on social media. Supporting both formats directly from the same rendering pipeline provides the optimal user experience.
