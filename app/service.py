import csv
import io
import json
import logging
import uuid
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db_context
from app.models import CertificateStatus, Job, JobStatus, RecipientCertificate, utc_now
from app.schemas import CreateJobRequest, RecipientInput
from app.certificate_generator import CertificateTemplateGenerator, CertificateGenerationError

logger = logging.getLogger(__name__)


def generate_unique_code(prefix: str = "CERT") -> str:
    """Generates a human-readable, unique certificate verification code."""
    now = datetime.now(timezone.utc)
    short_uuid = uuid.uuid4().hex[:8].upper()
    return f"{prefix}-{now.year}-{short_uuid[:4]}-{short_uuid[4:]}"


class CertificateService:
    def __init__(self):
        self.generator = CertificateTemplateGenerator(settings.STORAGE_DIR)
        self.executor = ThreadPoolExecutor(
            max_workers=settings.MAX_WORKER_THREADS,
            thread_name_prefix="cert-worker"
        )

    def parse_csv_recipients(self, file_content: str) -> List[RecipientInput]:
        """
        Parses a CSV string into a list of RecipientInput objects.
        Supports standard headers: name, email, and any extra custom attributes.
        """
        csv_file = io.StringIO(file_content.strip())
        reader = csv.DictReader(csv_file)
        
        if not reader.fieldnames:
            raise ValueError("CSV file is empty or missing headers.")

        # Normalize field names to lowercase
        field_map = {orig.strip().lower(): orig for orig in reader.fieldnames}
        
        name_key = None
        for candidate in ["name", "recipient_name", "full_name", "recipient"]:
            if candidate in field_map:
                name_key = field_map[candidate]
                break

        if not name_key:
            raise ValueError("CSV must contain a 'name' or 'recipient_name' column header.")

        email_key = None
        for candidate in ["email", "recipient_email", "email_address"]:
            if candidate in field_map:
                email_key = field_map[candidate]
                break

        recipients = []
        for idx, row in enumerate(reader, start=2):  # line 2 is first data row
            raw_name = row.get(name_key, "").strip()
            raw_email = row.get(email_key, "").strip() if email_key else None
            
            # Extract additional custom attributes from other columns
            custom_attrs = {}
            for col, val in row.items():
                if col not in (name_key, email_key) and val and val.strip():
                    custom_attrs[col.strip()] = val.strip()

            recipients.append(
                RecipientInput(
                    name=raw_name,
                    email=raw_email if raw_email else None,
                    custom_attributes=custom_attrs if custom_attrs else None
                )
            )

        if not recipients:
            raise ValueError("CSV file contains no data rows.")

        return recipients

    def create_job(self, req: CreateJobRequest, db: Session, process_sync: bool = False) -> Job:
        """
        Validates recipients, persists Job and RecipientCertificate rows in the database,
        and launches processing (either synchronously or via background thread pool).
        """
        job = Job(
            id=str(uuid.uuid4()),
            title=req.title or "Certificate of Completion",
            event_name=req.event_name,
            issue_date=req.issue_date,
            issuer_name=req.issuer_name,
            issuer_title=req.issuer_title or "Authorized Signatory",
            template_style=req.template_style or "classic_gold",
            status=JobStatus.PENDING,
            total_count=len(req.recipients),
            processed_count=0,
            success_count=0,
            failed_count=0
        )
        db.add(job)

        recipient_records: List[RecipientCertificate] = []
        for r_input in req.recipients:
            cert_code = generate_unique_code()
            custom_attr_str = json.dumps(r_input.custom_attributes) if r_input.custom_attributes else None

            # Pre-validation check:
            # If recipient name is blank or invalid, flag immediately as FAILED
            is_valid = True
            error_reason = None

            if not r_input.name or not r_input.name.strip():
                is_valid = False
                error_reason = "Recipient name cannot be blank."

            cert = RecipientCertificate(
                id=str(uuid.uuid4()),
                job_id=job.id,
                recipient_name=r_input.name.strip() if r_input.name else "",
                recipient_email=r_input.email,
                custom_attributes=custom_attr_str,
                certificate_code=cert_code,
                status=CertificateStatus.PENDING if is_valid else CertificateStatus.FAILED,
                error_message=error_reason
            )
            recipient_records.append(cert)
            db.add(cert)

        db.commit()
        db.refresh(job)

        if process_sync:
            self._process_job_worker(job.id)
            db.refresh(job)
        else:
            # Trigger asynchronous background processing
            job.status = JobStatus.PROCESSING
            db.commit()
            self.executor.submit(self._process_job_worker, job.id)

        return job

    def _process_job_worker(self, job_id: str) -> None:
        """
        Background worker that processes all pending recipients for a job.
        Crucial design guarantee: Individual failures NEVER stop or corrupt the remaining batch!
        """
        logger.info(f"Starting certificate generation for job: {job_id}")

        with get_db_context() as db:
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                logger.error(f"Job not found for ID: {job_id}")
                return

            job.status = JobStatus.PROCESSING
            db.commit()

            pending_certs = (
                db.query(RecipientCertificate)
                .filter(
                    RecipientCertificate.job_id == job_id,
                    RecipientCertificate.status == CertificateStatus.PENDING
                )
                .all()
            )

            # Account for any that failed during initial schema/input validation
            already_failed = (
                db.query(RecipientCertificate)
                .filter(
                    RecipientCertificate.job_id == job_id,
                    RecipientCertificate.status == CertificateStatus.FAILED
                )
                .count()
            )
            
            job.failed_count = already_failed
            job.processed_count = already_failed
            db.commit()

            # Iterate over recipients with complete fault isolation
            for cert in pending_certs:
                try:
                    custom_attrs = json.loads(cert.custom_attributes) if cert.custom_attributes else None
                    verify_url = f"{settings.BASE_URL}/verify/{cert.certificate_code}"

                    # Call generation engine
                    result = self.generator.generate(
                        recipient_name=cert.recipient_name,
                        event_name=job.event_name,
                        issue_date=job.issue_date,
                        issuer_name=job.issuer_name,
                        issuer_title=job.issuer_title,
                        title=job.title,
                        certificate_code=cert.certificate_code,
                        template_style=job.template_style,
                        custom_attributes=custom_attrs,
                        verify_url=verify_url,
                        job_id=job.id,
                        cert_id=cert.id
                    )

                    cert.status = CertificateStatus.SUCCESS
                    cert.pdf_filename = result["pdf_filename"]
                    cert.png_filename = result["png_filename"]
                    cert.file_size_bytes = result["file_size_bytes"]
                    cert.generated_at = utc_now()
                    cert.error_message = None

                    job.success_count += 1

                except Exception as exc:
                    # Failure is isolated to this recipient!
                    logger.warning(f"Failed generating certificate for {cert.recipient_name}: {exc}")
                    cert.status = CertificateStatus.FAILED
                    cert.error_message = str(exc)
                    job.failed_count += 1

                finally:
                    job.processed_count += 1
                    cert.job = job
                    # Commit progress to database for live polling updates
                    db.commit()

            # Finalize Job Status
            job.updated_at = utc_now()
            job.completed_at = utc_now()

            if job.total_count == 0:
                job.status = JobStatus.COMPLETED
            elif job.failed_count == 0:
                job.status = JobStatus.COMPLETED
            elif job.success_count == 0:
                job.status = JobStatus.FAILED
            else:
                job.status = JobStatus.PARTIALLY_FAILED

            db.commit()
            logger.info(
                f"Job {job_id} finished: status={job.status.value}, "
                f"success={job.success_count}, failed={job.failed_count}"
            )

    def get_job(self, job_id: str, db: Session) -> Optional[Job]:
        return db.query(Job).filter(Job.id == job_id).first()

    def list_jobs(self, db: Session, limit: int = 20, offset: int = 0) -> List[Job]:
        return (
            db.query(Job)
            .order_by(Job.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_certificate(self, cert_id: str, db: Session) -> Optional[RecipientCertificate]:
        return db.query(RecipientCertificate).filter(RecipientCertificate.id == cert_id).first()

    def get_certificate_by_code(self, code: str, db: Session) -> Optional[RecipientCertificate]:
        return db.query(RecipientCertificate).filter(RecipientCertificate.certificate_code == code).first()

    def get_certificate_file_path(self, cert: RecipientCertificate, file_format: str = "pdf") -> Optional[Path]:
        """Resolves the physical filesystem path for a certificate file."""
        if cert.status != CertificateStatus.SUCCESS:
            return None

        filename = cert.pdf_filename if file_format.lower() == "pdf" else cert.png_filename
        if not filename:
            return None

        # Check in job folder
        job_path = settings.STORAGE_DIR / str(cert.job_id) / filename
        if job_path.exists():
            return job_path

        # Check in root storage folder
        root_path = settings.STORAGE_DIR / filename
        if root_path.exists():
            return root_path

        return None

    def create_job_zip_archive(self, job: Job, file_format: str = "pdf") -> Path:
        """
        Creates a ZIP archive containing all successful certificates for a job.
        Useful for bulk download by the organizer.
        """
        zip_filename = f"certificates_{job.id[:8]}_{file_format}.zip"
        job_dir = settings.STORAGE_DIR / str(job.id)
        job_dir.mkdir(parents=True, exist_ok=True)
        zip_path = job_dir / zip_filename

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_out:
            for cert in job.certificates:
                if cert.status == CertificateStatus.SUCCESS:
                    fpath = self.get_certificate_file_path(cert, file_format)
                    if fpath and fpath.exists():
                        # Give a friendly archive filename: "Jane_Doe_CERT-XXXX.pdf"
                        clean_name = "".join(c for c in cert.recipient_name if c.isalnum() or c in (" ", "-", "_")).strip()
                        clean_name = clean_name.replace(" ", "_") or "recipient"
                        arc_name = f"{clean_name}_{cert.certificate_code}.{file_format}"
                        zip_out.write(fpath, arcname=arc_name)

        return zip_path

    def delete_job(self, job_id: str, db: Session) -> bool:
        """Deletes a job and associated files on disk."""
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return False

        # Remove job directory on disk
        job_dir = settings.STORAGE_DIR / str(job.id)
        if job_dir.exists():
            import shutil
            shutil.rmtree(job_dir, ignore_errors=True)

        db.delete(job)
        db.commit()
        return True


# Global service singleton
certificate_service = CertificateService()
