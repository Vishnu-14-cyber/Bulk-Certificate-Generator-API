import os
import math
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont


class CertificateGenerationError(Exception):
    """Raised when certificate rendering or file writing fails."""
    pass


class CertificateTemplateGenerator:
    """
    Renders high-resolution certificates based on a predefined professional template.
    Produces both PNG images (for web preview) and PDF files (for printing/archival).
    """

    WIDTH = 1920
    HEIGHT = 1080

    THEMES = {
        "classic_gold": {
            "bg": (252, 252, 249),
            "primary": (22, 38, 66),          # Deep Navy
            "accent": (180, 138, 48),         # Metallic Gold
            "accent_light": (220, 185, 110),  # Light Gold
            "text_muted": (100, 116, 139),    # Slate
            "text_dark": (15, 23, 42),        # Obsidian
            "seal_bg": (180, 138, 48),
            "seal_border": (130, 95, 25),
        },
        "modern_blue": {
            "bg": (248, 250, 252),
            "primary": (14, 116, 144),        # Deep Cyan / Teal
            "accent": (2, 132, 199),          # Sky Blue
            "accent_light": (125, 211, 252),
            "text_muted": (71, 85, 105),
            "text_dark": (15, 23, 42),
            "seal_bg": (2, 132, 199),
            "seal_border": (3, 105, 161),
        },
        "emerald_honor": {
            "bg": (250, 252, 250),
            "primary": (6, 78, 59),           # Deep Emerald
            "accent": (16, 185, 129),         # Vivid Emerald
            "accent_light": (167, 243, 208),
            "text_muted": (82, 100, 90),
            "text_dark": (15, 23, 42),
            "seal_bg": (16, 185, 129),
            "seal_border": (4, 120, 87),
        }
    }

    def __init__(self, storage_dir: Path):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_font(self, font_type: str, size: int) -> ImageFont.ImageFont:
        """
        Safely loads a TrueType font with system font fallbacks.
        Supports Windows, Linux, and macOS fonts, with standard Pillow fallback.
        """
        candidate_paths = []
        if font_type == "serif_bold":
            candidate_paths = [
                "C:/Windows/Fonts/georgiab.ttf",
                "C:/Windows/Fonts/timesbd.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
                "/System/Library/Fonts/Times.ttc",
            ]
        elif font_type == "serif":
            candidate_paths = [
                "C:/Windows/Fonts/georgia.ttf",
                "C:/Windows/Fonts/times.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
                "/System/Library/Fonts/Times.ttc",
            ]
        elif font_type == "sans_bold":
            candidate_paths = [
                "C:/Windows/Fonts/arialbd.ttf",
                "C:/Windows/Fonts/calibrib.ttf",
                "C:/Windows/Fonts/segoeuib.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            ]
        elif font_type == "script" or font_type == "cursive":
            candidate_paths = [
                "C:/Windows/Fonts/georgiai.ttf",
                "C:/Windows/Fonts/timesi.ttf",
                "C:/Windows/Fonts/calibrii.ttf",
            ]
        else:  # sans regular
            candidate_paths = [
                "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/calibri.ttf",
                "C:/Windows/Fonts/segoeui.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            ]

        for path in candidate_paths:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    continue

        # Fallback to default pillow font
        return ImageFont.load_default()

    def _draw_ornamental_borders(self, draw: ImageDraw.ImageDraw, theme: Dict[str, Tuple[int, int, int]]) -> None:
        """Draws elegant outer double borders with decorative corner accents."""
        accent = theme["accent"]
        primary = theme["primary"]
        bg = theme["bg"]

        # Outer border
        draw.rectangle([(40, 40), (self.WIDTH - 40, self.HEIGHT - 40)], outline=accent, width=4)
        
        # Inner thin border
        draw.rectangle([(55, 55), (self.WIDTH - 55, self.HEIGHT - 55)], outline=primary, width=2)

        # Delicate pinstripe border
        draw.rectangle([(65, 65), (self.WIDTH - 65, self.HEIGHT - 65)], outline=theme["accent_light"], width=1)

        # Corner ornamental squares
        corner_offsets = [
            (55, 55),
            (self.WIDTH - 55, 55),
            (55, self.HEIGHT - 55),
            (self.WIDTH - 55, self.HEIGHT - 55)
        ]
        square_size = 14
        for cx, cy in corner_offsets:
            half = square_size // 2
            draw.rectangle(
                [(cx - half, cy - half), (cx + half, cy + half)],
                fill=accent,
                outline=primary,
                width=1
            )

    def _draw_decorative_seal(self, draw: ImageDraw.ImageDraw, cx: int, cy: int, theme: Dict[str, Tuple[int, int, int]]) -> None:
        """Renders a gold seal with radiating star burst and ribbon tails."""
        radius = 58
        seal_bg = theme["seal_bg"]
        seal_border = theme["seal_border"]

        # Ribbon tails
        tail_points_left = [(cx - 24, cy + 30), (cx - 48, cy + 105), (cx - 20, cy + 85), (cx - 5, cy + 35)]
        tail_points_right = [(cx + 24, cy + 30), (cx + 48, cy + 105), (cx + 20, cy + 85), (cx + 5, cy + 35)]
        draw.polygon(tail_points_left, fill=seal_border)
        draw.polygon(tail_points_right, fill=seal_border)

        # Star burst rosette rays
        num_rays = 24
        for i in range(num_rays):
            angle = i * (2 * math.pi / num_rays)
            r_outer = radius + 6
            r_inner = radius - 4
            x1 = cx + int(r_outer * math.cos(angle))
            y1 = cy + int(r_outer * math.sin(angle))
            x2 = cx + int(r_inner * math.cos(angle + math.pi / num_rays))
            y2 = cy + int(r_inner * math.sin(angle + math.pi / num_rays))
            draw.line([(cx, cy), (x1, y1)], fill=theme["accent_light"], width=3)

        # Outer seal circle
        draw.ellipse([(cx - radius, cy - radius), (cx + radius, cy + radius)], fill=seal_bg, outline=seal_border, width=3)
        
        # Inner dashed circle
        inner_r = radius - 8
        draw.ellipse([(cx - inner_r, cy - inner_r), (cx + inner_r, cy + inner_r)], outline=(255, 255, 255), width=2)

        # Inner seal emblem text
        font_seal = self._get_font("sans_bold", 13)
        font_star = self._get_font("serif_bold", 24)
        draw.text((cx, cy - 14), "*", fill=(255, 255, 255), font=font_star, anchor="mm")
        draw.text((cx, cy + 8), "VERIFIED", fill=(255, 255, 255), font=font_seal, anchor="mm")
        draw.text((cx, cy + 22), "EXCELLENCE", fill=(255, 255, 255), font=self._get_font("sans", 9), anchor="mm")

    def _draw_signature_line(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        issuer_name: str,
        issuer_title: str,
        theme: Dict[str, Tuple[int, int, int]]
    ) -> None:
        """Draws an authentic digital signature line with issuer metadata."""
        # Simulated cursive signature flourish
        sig_font = self._get_font("script", 32)
        draw.text((x, y - 32), issuer_name, fill=theme["primary"], font=sig_font, anchor="mm")

        # Signature separator line
        draw.line([(x - 140, y), (x + 140, y)], fill=theme["accent"], width=2)

        # Name and Title
        name_font = self._get_font("sans_bold", 17)
        title_font = self._get_font("sans", 14)
        draw.text((x, y + 20), issuer_name, fill=theme["text_dark"], font=name_font, anchor="mm")
        draw.text((x, y + 42), issuer_title, fill=theme["text_muted"], font=title_font, anchor="mm")

    def generate(
        self,
        recipient_name: str,
        event_name: str,
        issue_date: str,
        issuer_name: str,
        issuer_title: str = "Authorized Signatory",
        title: str = "Certificate of Completion",
        certificate_code: str = "CERT-0000-0000",
        template_style: str = "classic_gold",
        custom_attributes: Optional[Dict[str, Any]] = None,
        verify_url: Optional[str] = None,
        job_id: Optional[str] = None,
        cert_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Renders the certificate image and saves both PNG and PDF files.
        Returns metadata about generated assets.
        """
        try:
            theme = self.THEMES.get(template_style, self.THEMES["classic_gold"])

            # 1. Base Canvas
            img = Image.new("RGB", (self.WIDTH, self.HEIGHT), color=theme["bg"])
            draw = ImageDraw.Draw(img)

            # 2. Borders & Corner Accents
            self._draw_ornamental_borders(draw, theme)

            # 3. Top Organization Emblem / Badge
            emblem_cx = self.WIDTH // 2
            emblem_cy = 135
            draw.ellipse([(emblem_cx - 28, emblem_cy - 28), (emblem_cx + 28, emblem_cy + 28)], fill=theme["accent"], outline=theme["primary"], width=2)
            draw.text((emblem_cx, emblem_cy), "★", fill=(255, 255, 255), font=self._get_font("sans_bold", 24), anchor="mm")

            # 4. Certificate Title
            font_title = self._get_font("serif_bold", 44)
            draw.text((self.WIDTH // 2, 210), title.upper(), fill=theme["primary"], font=font_title, anchor="mm")

            # Divider line below title with diamond center
            draw.line([(self.WIDTH // 2 - 200, 245), (self.WIDTH // 2 - 25, 245)], fill=theme["accent"], width=2)
            draw.polygon([
                (self.WIDTH // 2 - 12, 245),
                (self.WIDTH // 2, 240),
                (self.WIDTH // 2 + 12, 245),
                (self.WIDTH // 2, 250)
            ], fill=theme["accent"])
            draw.line([(self.WIDTH // 2 + 25, 245), (self.WIDTH // 2 + 200, 245)], fill=theme["accent"], width=2)

            # 5. Subtitle: Presentation Statement
            font_subtitle = self._get_font("sans", 16)
            draw.text(
                (self.WIDTH // 2, 290),
                "THIS CERTIFICATE IS PROUDLY PRESENTED TO",
                fill=theme["text_muted"],
                font=font_subtitle,
                anchor="mm"
            )

            # 6. Recipient Name (Auto-scales down if name is lengthy)
            name_font_size = 56
            if len(recipient_name) > 30:
                name_font_size = 40
            elif len(recipient_name) > 22:
                name_font_size = 48
            
            font_name = self._get_font("serif_bold", name_font_size)
            draw.text((self.WIDTH // 2, 380), recipient_name, fill=theme["primary"], font=font_name, anchor="mm")

            # Gold underline accent under recipient name
            name_line_w = min(max(len(recipient_name) * 18, 300), 750)
            draw.line(
                [(self.WIDTH // 2 - (name_line_w // 2), 430), (self.WIDTH // 2 + (name_line_w // 2), 430)],
                fill=theme["accent"],
                width=2
            )

            # 7. Achievement Statement
            draw.text(
                (self.WIDTH // 2, 475),
                "for outstanding participation and successful completion of",
                fill=theme["text_muted"],
                font=self._get_font("sans", 17),
                anchor="mm"
            )

            # 8. Event / Course Name
            event_font_size = 38
            if len(event_name) > 40:
                event_font_size = 30
            font_event = self._get_font("serif_bold", event_font_size)
            draw.text((self.WIDTH // 2, 540), event_name, fill=theme["accent"], font=font_event, anchor="mm")

            # 9. Custom Attributes (e.g., Grade, Score, Hours) if provided
            if custom_attributes and isinstance(custom_attributes, dict):
                attr_parts = []
                for k, v in custom_attributes.items():
                    clean_k = str(k).replace("_", " ").title()
                    attr_parts.append(f"{clean_k}: {v}")
                attr_str = "   •   ".join(attr_parts)
                draw.text(
                    (self.WIDTH // 2, 600),
                    attr_str,
                    fill=theme["text_dark"],
                    font=self._get_font("sans_bold", 15),
                    anchor="mm"
                )

            # 10. Date of Issuance (Bottom Left)
            date_x = 340
            date_y = 820
            draw.line([(date_x - 120, date_y), (date_x + 120, date_y)], fill=theme["accent"], width=2)
            draw.text((date_x, date_y - 25), issue_date, fill=theme["text_dark"], font=self._get_font("sans_bold", 17), anchor="mm")
            draw.text((date_x, date_y + 22), "DATE OF ISSUANCE", fill=theme["text_muted"], font=self._get_font("sans", 14), anchor="mm")

            # 11. Center Seal
            self._draw_decorative_seal(draw, self.WIDTH // 2, 800, theme)

            # 12. Signature (Bottom Right)
            self._draw_signature_line(
                draw,
                x=self.WIDTH - 340,
                y=date_y,
                issuer_name=issuer_name,
                issuer_title=issuer_title,
                theme=theme
            )

            # 13. Security Verification Strip at the bottom
            verify_str = f"CERTIFICATE ID: {certificate_code}"
            if verify_url:
                verify_str += f"   |   VERIFY AT: {verify_url}"

            draw.text(
                (self.WIDTH // 2, self.HEIGHT - 75),
                verify_str,
                fill=theme["text_muted"],
                font=self._get_font("sans", 12),
                anchor="mm"
            )

            # 14. Save Files
            target_subfolder = self.storage_dir
            if job_id:
                target_subfolder = self.storage_dir / str(job_id)
                target_subfolder.mkdir(parents=True, exist_ok=True)

            file_stem = cert_id or certificate_code
            png_filename = f"{file_stem}.png"
            pdf_filename = f"{file_stem}.pdf"

            png_path = target_subfolder / png_filename
            pdf_path = target_subfolder / pdf_filename

            # Save PNG
            img.save(png_path, "PNG", optimize=True)

            # Save PDF (Direct high-resolution raster PDF conversion)
            img.save(pdf_path, "PDF", resolution=150.0)

            file_size_bytes = os.path.getsize(pdf_path)

            return {
                "png_filename": png_filename,
                "pdf_filename": pdf_filename,
                "png_path": str(png_path),
                "pdf_path": str(pdf_path),
                "file_size_bytes": file_size_bytes
            }

        except Exception as exc:
            raise CertificateGenerationError(f"Failed to generate certificate for '{recipient_name}': {str(exc)}") from exc
