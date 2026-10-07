import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


EMAIL_REGEX = re.compile(r"^[\w\.-]+@([\w-]+\.)+[\w-]{2,}$")


class RecipientInput(BaseModel):
    name: str = Field(..., description="Recipient full name", min_length=1, max_length=200)
    email: Optional[str] = Field(None, description="Optional recipient email address")
    custom_attributes: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional key-value pairs (e.g. score, grade, hours, role)"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Recipient name cannot be blank or whitespace only")
        return trimmed

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        if not trimmed:
            return None
        if not EMAIL_REGEX.match(trimmed):
            raise ValueError(f"Invalid email address format: '{v}'")
        return trimmed.lower()


class CreateJobRequest(BaseModel):
    title: Optional[str] = Field(
        default="Certificate of Completion",
        description="Title of the certificate (e.g. Certificate of Appreciation, Certificate of Achievement)"
    )
    event_name: str = Field(
        ...,
        description="Name of the course, event, workshop, or conference",
        min_length=1,
        max_length=255
    )
    issue_date: Optional[str] = Field(
        default=None,
        description="Issue date (YYYY-MM-DD or text like October 7, 2026). Defaults to today."
    )
    issuer_name: str = Field(
        ...,
        description="Name of the issuing authority or signatory",
        min_length=1,
        max_length=200
    )
    issuer_title: Optional[str] = Field(
        default="Authorized Signatory",
        description="Title of the issuer (e.g. Lead Instructor, Director, CEO)"
    )
    template_style: Optional[str] = Field(
        default="classic_gold",
        description="Visual style: 'classic_gold', 'modern_blue', 'emerald_honor'"
    )
    recipients: List[RecipientInput] = Field(
        ...,
        description="List of recipient records to generate certificates for"
    )

    @field_validator("event_name", "issuer_name")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Field cannot be empty or whitespace only")
        return trimmed

    @field_validator("issue_date")
    @classmethod
    def default_issue_date(cls, v: Optional[str]) -> str:
        if not v or not v.strip():
            return date.today().isoformat()
        return v.strip()

    @field_validator("recipients")
    @classmethod
    def validate_recipients(cls, v: List[RecipientInput]) -> List[RecipientInput]:
        if not v:
            raise ValueError("Recipients list cannot be empty. Please provide at least one recipient.")
        if len(v) > 5000:
            raise ValueError("Exceeded maximum batch limit of 5,000 recipients per request.")
        return v


class RecipientStatusResponse(BaseModel):
    id: str
    job_id: str
    recipient_name: str
    recipient_email: Optional[str] = None
    custom_attributes: Optional[Dict[str, Any]] = None
    certificate_code: str
    status: str
    error_message: Optional[str] = None
    pdf_filename: Optional[str] = None
    png_filename: Optional[str] = None
    file_size_bytes: Optional[int] = None
    download_pdf_url: Optional[str] = None
    download_png_url: Optional[str] = None
    view_url: Optional[str] = None
    created_at: datetime
    generated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobSummaryResponse(BaseModel):
    id: str
    title: str
    event_name: str
    issue_date: str
    issuer_name: str
    issuer_title: Optional[str] = None
    template_style: str
    status: str
    total_count: int
    processed_count: int
    success_count: int
    failed_count: int
    progress_percentage: float
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    status_url: str
    zip_download_url: Optional[str] = None

    class Config:
        from_attributes = True


class JobDetailResponse(JobSummaryResponse):
    recipients: List[RecipientStatusResponse] = []


class JobCreateResponse(BaseModel):
    job_id: str
    status: str
    message: str
    total_recipients: int
    status_url: str
    check_status_api: str
    created_at: datetime


class CertificateDetailResponse(BaseModel):
    id: str
    job_id: str
    recipient_name: str
    recipient_email: Optional[str] = None
    custom_attributes: Optional[Dict[str, Any]] = None
    certificate_code: str
    title: str
    event_name: str
    issue_date: str
    issuer_name: str
    issuer_title: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    file_size_bytes: Optional[int] = None
    download_pdf_url: Optional[str] = None
    download_png_url: Optional[str] = None
    view_url: Optional[str] = None
    verify_url: str
    created_at: datetime
    generated_at: Optional[datetime] = None


class VerifyCertificateResponse(BaseModel):
    valid: bool
    certificate_code: str
    recipient_name: Optional[str] = None
    title: Optional[str] = None
    event_name: Optional[str] = None
    issue_date: Optional[str] = None
    issuer_name: Optional[str] = None
    issuer_title: Optional[str] = None
    status: str
    verified_at: datetime
