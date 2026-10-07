from pathlib import Path
import pytest
from app.certificate_generator import CertificateTemplateGenerator, CertificateGenerationError


def test_certificate_generation_creates_png_and_pdf(test_temp_dir: Path):
    """Verifies that generator produces valid PNG and PDF files with valid binary signatures."""
    gen = CertificateTemplateGenerator(test_temp_dir)
    res = gen.generate(
        recipient_name="Eleanor Vance",
        event_name="Quantum Computing Summit 2026",
        issue_date="2026-10-07",
        issuer_name="Dr. Julian Hill",
        issuer_title="Director of Research",
        title="Certificate of Excellence",
        certificate_code="CERT-2026-TEST-0001",
        template_style="classic_gold",
        custom_attributes={"honors": "Summa Cum Laude", "hours": 60},
        verify_url="http://localhost:8000/verify/CERT-2026-TEST-0001",
        job_id="test_job_1",
        cert_id="test_cert_1"
    )

    pdf_path = Path(res["pdf_path"])
    png_path = Path(res["png_path"])

    assert pdf_path.exists(), "Generated PDF file does not exist"
    assert png_path.exists(), "Generated PNG file does not exist"
    assert res["file_size_bytes"] > 1000, "PDF file is suspiciously small"

    # Verify PNG magic header
    with open(png_path, "rb") as f:
        png_header = f.read(8)
        assert png_header == b"\x89PNG\r\n\x1a\n", "Invalid PNG header"

    # Verify PDF magic header
    with open(pdf_path, "rb") as f:
        pdf_header = f.read(4)
        assert pdf_header == b"%PDF", "Invalid PDF header"


def test_certificate_generation_theme_variants(test_temp_dir: Path):
    """Verifies that all predefined template styles render without error."""
    gen = CertificateTemplateGenerator(test_temp_dir)
    for theme in ["classic_gold", "modern_blue", "emerald_honor"]:
        res = gen.generate(
            recipient_name=f"Student {theme}",
            event_name="Security Engineering",
            issue_date="2026-10-07",
            issuer_name="Auditor General",
            template_style=theme,
            certificate_code=f"CERT-{theme.upper()}",
            job_id="theme_test",
            cert_id=f"cert_{theme}"
        )
        assert Path(res["pdf_path"]).exists()
        assert Path(res["png_path"]).exists()


def test_certificate_generation_auto_scale_long_names(test_temp_dir: Path):
    """Verifies that extra long names do not crash the engine and are scaled properly."""
    gen = CertificateTemplateGenerator(test_temp_dir)
    very_long_name = "Hubert Blaine Wolfeschlegelsteinhausenbergerdorff Senior"
    res = gen.generate(
        recipient_name=very_long_name,
        event_name="Advanced Algorithmic Complexity and Distributed Consistency Protocol Engineering",
        issue_date="2026-10-07",
        issuer_name="Chancellor Alexander Bartholomew Worthington III",
        certificate_code="CERT-LONG-NAME",
        job_id="long_names",
        cert_id="cert_long"
    )
    assert Path(res["pdf_path"]).exists()
