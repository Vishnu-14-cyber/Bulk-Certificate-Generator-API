import os
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CertificateStatus, Job, JobStatus, RecipientCertificate
from app.schemas import (
    CertificateDetailResponse,
    CreateJobRequest,
    JobCreateResponse,
    JobDetailResponse,
    JobSummaryResponse,
    RecipientStatusResponse,
    VerifyCertificateResponse,
)
from app.service import certificate_service

router = APIRouter(prefix="/api/v1", tags=["Certificates & Jobs"])


def _format_recipient_response(cert: RecipientCertificate) -> RecipientStatusResponse:
    import json
    custom_attrs = json.loads(cert.custom_attributes) if cert.custom_attributes else None
    
    download_pdf = f"/api/v1/certificates/{cert.id}/download?format=pdf" if cert.status == CertificateStatus.SUCCESS else None
    download_png = f"/api/v1/certificates/{cert.id}/download?format=png" if cert.status == CertificateStatus.SUCCESS else None
    view_url = f"/api/v1/certificates/{cert.id}/view?format=png" if cert.status == CertificateStatus.SUCCESS else None

    return RecipientStatusResponse(
        id=cert.id,
        job_id=cert.job_id,
        recipient_name=cert.recipient_name,
        recipient_email=cert.recipient_email,
        custom_attributes=custom_attrs,
        certificate_code=cert.certificate_code,
        status=cert.status.value,
        error_message=cert.error_message,
        pdf_filename=cert.pdf_filename,
        png_filename=cert.png_filename,
        file_size_bytes=cert.file_size_bytes,
        download_pdf_url=download_pdf,
        download_png_url=download_png,
        view_url=view_url,
        created_at=cert.created_at,
        generated_at=cert.generated_at
    )


def _format_job_summary(job: Job) -> JobSummaryResponse:
    zip_url = f"/api/v1/jobs/{job.id}/download-zip?format=pdf" if job.success_count > 0 else None
    return JobSummaryResponse(
        id=job.id,
        title=job.title,
        event_name=job.event_name,
        issue_date=job.issue_date,
        issuer_name=job.issuer_name,
        issuer_title=job.issuer_title,
        template_style=job.template_style,
        status=job.status.value,
        total_count=job.total_count,
        processed_count=job.processed_count,
        success_count=job.success_count,
        failed_count=job.failed_count,
        progress_percentage=job.progress_percentage(),
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
        completed_at=job.completed_at,
        status_url=f"/jobs/{job.id}",
        zip_download_url=zip_url
    )


@router.post(
    "/jobs",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit Bulk Certificate Generation Request (JSON)",
    description="Submits a list of recipients for bulk certificate generation. Defaults to async background processing."
)
def create_certificate_job(
    req: CreateJobRequest,
    process_sync: bool = Query(
        False,
        description="If True, processes synchronously before responding. If False (default), runs in background."
    ),
    db: Session = Depends(get_db)
):
    job = certificate_service.create_job(req, db=db, process_sync=process_sync)
    
    return JobCreateResponse(
        job_id=job.id,
        status=job.status.value,
        message="Certificate generation job created and processing has started." if not process_sync else "Job processing completed synchronously.",
        total_recipients=job.total_count,
        status_url=f"/jobs/{job.id}",
        check_status_api=f"/api/v1/jobs/{job.id}",
        created_at=job.created_at
    )


@router.post(
    "/jobs/upload-csv",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit Bulk Certificate Generation via CSV Upload",
    description="Upload a CSV file containing recipient names, emails, and custom attributes."
)
async def create_job_from_csv(
    file: UploadFile = File(..., description="CSV file containing 'name' column"),
    event_name: str = Form(..., description="Event or Course Name"),
    issuer_name: str = Form(..., description="Issuer Name"),
    title: Optional[str] = Form("Certificate of Completion"),
    issue_date: Optional[str] = Form(None),
    issuer_title: Optional[str] = Form("Authorized Signatory"),
    template_style: Optional[str] = Form("classic_gold"),
    process_sync: bool = Form(False),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a CSV file (.csv).")

    content = await file.read()
    try:
        csv_text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        csv_text = content.decode("latin-1")

    try:
        recipients = certificate_service.parse_csv_recipients(csv_text)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")

    req = CreateJobRequest(
        title=title,
        event_name=event_name,
        issue_date=issue_date,
        issuer_name=issuer_name,
        issuer_title=issuer_title,
        template_style=template_style,
        recipients=recipients
    )

    job = certificate_service.create_job(req, db=db, process_sync=process_sync)
    return JobCreateResponse(
        job_id=job.id,
        status=job.status.value,
        message=f"Created job with {len(recipients)} recipients from CSV.",
        total_recipients=job.total_count,
        status_url=f"/jobs/{job.id}",
        check_status_api=f"/api/v1/jobs/{job.id}",
        created_at=job.created_at
    )


@router.get(
    "/jobs",
    response_model=List[JobSummaryResponse],
    summary="List Certificate Generation Jobs"
)
def list_jobs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    jobs = certificate_service.list_jobs(db=db, limit=limit, offset=offset)
    return [_format_job_summary(j) for j in jobs]


@router.get(
    "/jobs/{job_id}",
    response_model=JobDetailResponse,
    summary="Get Job Status and Recipient Progress"
)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = certificate_service.get_job(job_id, db=db)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID '{job_id}' not found.")

    summary = _format_job_summary(job)
    recipient_responses = [_format_recipient_response(c) for c in job.certificates]

    return JobDetailResponse(
        **summary.model_dump(),
        recipients=recipient_responses
    )


@router.get(
    "/jobs/{job_id}/download-zip",
    summary="Download All Generated Certificates for a Job as ZIP Archive"
)
def download_job_zip(
    job_id: str,
    format: str = Query("pdf", pattern="^(pdf|png)$"),
    db: Session = Depends(get_db)
):
    job = certificate_service.get_job(job_id, db=db)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    if job.success_count == 0:
        raise HTTPException(
            status_code=400,
            detail="No certificates have been successfully generated for this job yet."
        )

    zip_path = certificate_service.create_job_zip_archive(job, file_format=format)
    if not zip_path.exists():
        raise HTTPException(status_code=500, detail="Failed to create zip archive.")

    clean_title = "".join(c for c in job.event_name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
    zip_download_name = f"{clean_title}_Certificates_{format.upper()}.zip"

    return FileResponse(
        path=str(zip_path),
        media_type="application/zip",
        filename=zip_download_name
    )


@router.get(
    "/certificates/{certificate_id}",
    response_model=CertificateDetailResponse,
    summary="Get Certificate Details"
)
def get_certificate_details(certificate_id: str, db: Session = Depends(get_db)):
    cert = certificate_service.get_certificate(certificate_id, db=db)
    if not cert:
        raise HTTPException(status_code=404, detail=f"Certificate '{certificate_id}' not found.")

    import json
    custom_attrs = json.loads(cert.custom_attributes) if cert.custom_attributes else None
    download_pdf = f"/api/v1/certificates/{cert.id}/download?format=pdf" if cert.status == CertificateStatus.SUCCESS else None
    download_png = f"/api/v1/certificates/{cert.id}/download?format=png" if cert.status == CertificateStatus.SUCCESS else None
    view_url = f"/api/v1/certificates/{cert.id}/view?format=png" if cert.status == CertificateStatus.SUCCESS else None

    return CertificateDetailResponse(
        id=cert.id,
        job_id=cert.job_id,
        recipient_name=cert.recipient_name,
        recipient_email=cert.recipient_email,
        custom_attributes=custom_attrs,
        certificate_code=cert.certificate_code,
        title=cert.job.title,
        event_name=cert.job.event_name,
        issue_date=cert.job.issue_date,
        issuer_name=cert.job.issuer_name,
        issuer_title=cert.job.issuer_title,
        status=cert.status.value,
        error_message=cert.error_message,
        file_size_bytes=cert.file_size_bytes,
        download_pdf_url=download_pdf,
        download_png_url=download_png,
        view_url=view_url,
        verify_url=f"/verify/{cert.certificate_code}",
        created_at=cert.created_at,
        generated_at=cert.generated_at
    )


@router.get(
    "/certificates/{certificate_id}/download",
    summary="Download Certificate File (PDF or PNG attachment)"
)
def download_certificate(
    certificate_id: str,
    format: str = Query("pdf", pattern="^(pdf|png)$"),
    db: Session = Depends(get_db)
):
    cert = certificate_service.get_certificate(certificate_id, db=db)
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found.")

    if cert.status != CertificateStatus.SUCCESS:
        raise HTTPException(status_code=400, detail=f"Certificate generation status is: {cert.status.value}. File unavailable.")

    file_path = certificate_service.get_certificate_file_path(cert, file_format=format)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="Certificate file not found on disk.")

    media_type = "application/pdf" if format == "pdf" else "image/png"
    clean_name = "".join(c for c in cert.recipient_name if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")
    download_filename = f"{clean_name}_Certificate.{format}"

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=download_filename,
        headers={"Content-Disposition": f'attachment; filename="{download_filename}"'}
    )


@router.get(
    "/certificates/{certificate_id}/view",
    summary="View Certificate Inline (Image or PDF preview)"
)
def view_certificate(
    certificate_id: str,
    format: str = Query("png", pattern="^(pdf|png)$"),
    db: Session = Depends(get_db)
):
    cert = certificate_service.get_certificate(certificate_id, db=db)
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found.")

    if cert.status != CertificateStatus.SUCCESS:
        raise HTTPException(status_code=400, detail="Certificate has not been generated successfully.")

    file_path = certificate_service.get_certificate_file_path(cert, file_format=format)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="Certificate file not found on disk.")

    media_type = "image/png" if format == "png" else "application/pdf"

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        headers={"Content-Disposition": "inline"}
    )


@router.get(
    "/certificates/verify/{certificate_code_or_id}",
    response_model=VerifyCertificateResponse,
    summary="Verify Certificate Authenticity by Code or ID"
)
def verify_certificate(
    certificate_code_or_id: str,
    db: Session = Depends(get_db)
):
    from datetime import datetime, timezone

    # Try finding by certificate_code first, then by UUID id
    cert = certificate_service.get_certificate_by_code(certificate_code_or_id, db=db)
    if not cert:
        cert = certificate_service.get_certificate(certificate_code_or_id, db=db)

    if not cert or cert.status != CertificateStatus.SUCCESS:
        return VerifyCertificateResponse(
            valid=False,
            certificate_code=certificate_code_or_id,
            status="NOT_FOUND_OR_INVALID",
            verified_at=datetime.now(timezone.utc)
        )

    return VerifyCertificateResponse(
        valid=True,
        certificate_code=cert.certificate_code,
        recipient_name=cert.recipient_name,
        title=cert.job.title,
        event_name=cert.job.event_name,
        issue_date=cert.job.issue_date,
        issuer_name=cert.job.issuer_name,
        issuer_title=cert.job.issuer_title,
        status="AUTHENTIC_AND_VERIFIED",
        verified_at=datetime.now(timezone.utc)
    )


@router.delete(
    "/jobs/{job_id}",
    summary="Delete Job and its Generated Assets"
)
def delete_job(job_id: str, db: Session = Depends(get_db)):
    deleted = certificate_service.delete_job(job_id, db=db)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return {"message": f"Job '{job_id}' and all associated files deleted successfully."}
