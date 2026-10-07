import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    ForeignKey,
    Text,
    Enum as SAEnum,
    Index
)
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    PARTIALLY_FAILED = "PARTIALLY_FAILED"
    FAILED = "FAILED"


class CertificateStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False, default="Certificate of Completion")
    event_name = Column(String(255), nullable=False)
    issue_date = Column(String(50), nullable=False)
    issuer_name = Column(String(200), nullable=False)
    issuer_title = Column(String(200), nullable=True, default="Authorized Signatory")
    template_style = Column(String(50), nullable=False, default="classic_gold")
    
    # Status tracking
    status = Column(
        SAEnum(JobStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=JobStatus.PENDING,
        index=True
    )
    total_count = Column(Integer, nullable=False, default=0)
    processed_count = Column(Integer, nullable=False, default=0)
    success_count = Column(Integer, nullable=False, default=0)
    failed_count = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    certificates = relationship(
        "RecipientCertificate",
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="RecipientCertificate.created_at"
    )

    def progress_percentage(self) -> float:
        if self.total_count == 0:
            return 0.0
        return round((self.processed_count / self.total_count) * 100, 1)


class RecipientCertificate(Base):
    __tablename__ = "recipient_certificates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    recipient_name = Column(String(255), nullable=False)
    recipient_email = Column(String(255), nullable=True)
    custom_attributes = Column(Text, nullable=True)  # JSON-encoded string
    
    # Unique verification code
    certificate_code = Column(String(64), nullable=False, unique=True, index=True)
    
    # Generation status
    status = Column(
        SAEnum(CertificateStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=CertificateStatus.PENDING,
        index=True
    )
    
    # Generated asset paths
    pdf_filename = Column(String(255), nullable=True)
    png_filename = Column(String(255), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=utc_now)
    generated_at = Column(DateTime, nullable=True)

    # Relationship
    job = relationship("Job", back_populates="certificates")


Index("idx_cert_job_status", RecipientCertificate.job_id, RecipientCertificate.status)
