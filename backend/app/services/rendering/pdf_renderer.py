"""PDF rendering service for generating professional documents."""

import base64
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional
from uuid import UUID

import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

from ...core.config import settings
from ...models.rendering import (
    BulletList,
    ContentType,
    DocumentSection,
    ExportFormat,
    ImageBlock,
    MetricItem,
    PDFRenderRequest,
    RenderResult,
    RenderStatus,
    TextBlock,
)
from .brand_styler import BrandStyler


class PDFRenderer:
    """Renders professional PDF documents from content JSON."""

    def __init__(self, brand_config: Optional[dict] = None):
        """Initialize the PDF renderer."""
        self.styler = BrandStyler(brand_config) if brand_config else BrandStyler()
        self._setup_templates()
        self._ensure_output_dir()

    def _setup_templates(self) -> None:
        """Set up Jinja2 template environment."""
        template_dirs = [
            settings.templates_dir / "pdf",
            settings.templates_dir,
            Path(__file__).parent / "templates",
        ]
        existing_dirs = [str(d) for d in template_dirs if d.exists()]

        if existing_dirs:
            self.env = Environment(
                loader=FileSystemLoader(existing_dirs),
                autoescape=select_autoescape(["html", "xml"]),
            )
        else:
            self.env = Environment(autoescape=select_autoescape(["html", "xml"]))

        # Register custom filters
        self.env.filters["markdown"] = self._render_markdown
        self.env.filters["format_date"] = self._format_date

    def _ensure_output_dir(self) -> None:
        """Ensure output directory exists."""
        settings.output_dir.mkdir(parents=True, exist_ok=True)

    def _render_markdown(self, text: str) -> str:
        """Convert markdown to HTML."""
        return markdown.markdown(
            text,
            extensions=["tables", "fenced_code", "nl2br"],
        )

    def _format_date(self, date_str: Optional[str]) -> str:
        """Format date string for display."""
        if not date_str:
            return datetime.now().strftime("%B %d, %Y")
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime("%B %d, %Y")
        except ValueError:
            return date_str

    def _generate_html(self, request: PDFRenderRequest) -> str:
        """Generate HTML from the render request."""
        # Build the HTML document
        html_parts = [
            "<!DOCTYPE html>",
            "<html lang='en'>",
            "<head>",
            "<meta charset='UTF-8'>",
            f"<title>{request.title}</title>",
            "<style>",
            self.styler.get_pdf_styles(),
            "</style>",
            "</head>",
            "<body>",
        ]

        # Add header and footer runners
        if request.header_text:
            html_parts.append(f"<div class='page-header'>{request.header_text}</div>")

        footer_content = request.footer_text or ""
        if request.show_page_numbers:
            footer_content += " | Page <span class='page-number'></span>"
        if footer_content:
            html_parts.append(f"<div class='page-footer'>{footer_content.strip(' |')}</div>")

        # Cover page
        html_parts.extend(self._render_cover_page(request))

        # Table of contents
        if request.show_toc and request.sections:
            html_parts.extend(self._render_toc(request.sections))

        # Render sections
        for section in request.sections:
            html_parts.extend(self._render_section(section))

        html_parts.extend(["</body>", "</html>"])

        return "\n".join(html_parts)

    def _render_cover_page(self, request: PDFRenderRequest) -> list[str]:
        """Render the cover page."""
        parts = ["<div class='cover-page'>"]

        # Logo
        logo_path = self.styler.get_logo_path()
        if logo_path:
            parts.append(f"<img src='file://{logo_path}' alt='Logo' style='max-width: 200px; margin-bottom: 40px;'>")

        # Title
        parts.append(f"<h1 class='cover-title'>{request.title}</h1>")

        if request.subtitle:
            parts.append(f"<p class='cover-subtitle'>{request.subtitle}</p>")

        # Prospect info
        if request.prospect:
            parts.append(f"<p class='cover-meta'>Prepared for: {request.prospect.company_name}</p>")
            if request.prospect.contact_name:
                parts.append(f"<p class='cover-meta'>{request.prospect.contact_name}")
                if request.prospect.contact_title:
                    parts.append(f", {request.prospect.contact_title}")
                parts.append("</p>")

        # Author and date
        meta_parts = []
        if request.author:
            meta_parts.append(f"Prepared by: {request.author}")
        if request.date:
            meta_parts.append(f"Date: {self._format_date(request.date)}")
        else:
            meta_parts.append(f"Date: {self._format_date(None)}")

        if meta_parts:
            parts.append(f"<p class='cover-meta'>{' | '.join(meta_parts)}</p>")

        parts.append("</div>")
        parts.append("<div class='page-break'></div>")

        return parts

    def _render_toc(self, sections: list[DocumentSection]) -> list[str]:
        """Render table of contents."""
        parts = [
            "<div class='toc'>",
            "<h2>Table of Contents</h2>",
        ]

        for i, section in enumerate(sections, 1):
            parts.append(
                f"<div class='toc-item'>"
                f"<a href='#section-{section.id}'>{i}. {section.title}</a>"
                f"<span>{i}</span>"
                f"</div>"
            )

        parts.append("</div>")
        parts.append("<div class='page-break'></div>")

        return parts

    def _render_section(self, section: DocumentSection) -> list[str]:
        """Render a document section."""
        parts = []

        if section.page_break_before:
            parts.append("<div class='page-break'></div>")

        parts.append(f"<section id='section-{section.id}'>")
        parts.append(f"<h2>{section.title}</h2>")

        for item in section.content:
            if isinstance(item, TextBlock):
                parts.extend(self._render_text_block(item))
            elif isinstance(item, ImageBlock):
                parts.extend(self._render_image_block(item))
            elif isinstance(item, BulletList):
                parts.extend(self._render_bullet_list(item))
            elif isinstance(item, MetricItem):
                parts.extend(self._render_metric(item))
            elif isinstance(item, dict):
                # Handle dict objects from JSON
                if "content" in item and "style" in item:
                    parts.extend(self._render_text_block(TextBlock(**item)))
                elif "items" in item:
                    parts.extend(self._render_bullet_list(BulletList(**item)))
                elif "value" in item and "label" in item:
                    parts.extend(self._render_metric(MetricItem(**item)))
                elif "url" in item:
                    parts.extend(self._render_image_block(ImageBlock(**item)))

        parts.append("</section>")

        if section.page_break_after:
            parts.append("<div class='page-break'></div>")

        return parts

    def _render_text_block(self, block: TextBlock) -> list[str]:
        """Render a text block."""
        tag_map = {
            "heading1": "h1",
            "heading2": "h2",
            "heading3": "h3",
            "body": "p",
            "caption": "p",
        }
        tag = tag_map.get(block.style, "p")
        class_attr = f" class='{block.style}'" if block.style == "caption" else ""
        style_attr = ""

        if block.align.value != "left":
            style_attr += f"text-align: {block.align.value};"
        if block.color:
            style_attr += f"color: {block.color};"

        style_part = f" style='{style_attr}'" if style_attr else ""
        content = self._render_markdown(block.content)

        # Remove wrapping <p> if we're using a heading
        if tag.startswith("h") and content.startswith("<p>") and content.endswith("</p>"):
            content = content[3:-4]

        return [f"<{tag}{class_attr}{style_part}>{content}</{tag}>"]

    def _render_image_block(self, block: ImageBlock) -> list[str]:
        """Render an image block."""
        style_parts = []
        if block.width:
            style_parts.append(f"width: {block.width}px")
        if block.height:
            style_parts.append(f"height: {block.height}px")
        style_parts.append(f"object-fit: {block.fit}")

        style_attr = f" style='{'; '.join(style_parts)}'" if style_parts else ""

        # Handle base64 images
        if block.url.startswith("data:"):
            src = block.url
        elif block.url.startswith("http"):
            src = block.url
        else:
            src = f"file://{block.url}"

        return [
            "<figure class='image-block'>",
            f"<img src='{src}' alt='{block.alt_text}'{style_attr}>",
            "</figure>",
        ]

    def _render_bullet_list(self, bullet_list: BulletList) -> list[str]:
        """Render a bullet list."""
        list_class = f"{bullet_list.style}-list"
        tag = "ol" if bullet_list.style == "numbered" else "ul"

        parts = [f"<{tag} class='{list_class}'>"]
        for item in bullet_list.items:
            parts.append(f"<li>{item}</li>")
        parts.append(f"</{tag}>")

        return parts

    def _render_metric(self, metric: MetricItem) -> list[str]:
        """Render a metric display."""
        parts = [
            "<div class='metric'>",
            f"<div class='metric-value'>{metric.value}</div>",
            f"<div class='metric-label'>{metric.label}</div>",
        ]
        if metric.description:
            parts.append(f"<div class='metric-description'>{metric.description}</div>")
        parts.append("</div>")

        return parts

    async def render(self, request: PDFRenderRequest) -> RenderResult:
        """Render a PDF document from the request."""
        try:
            # Generate HTML
            html_content = self._generate_html(request)

            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c if c.isalnum() else "_" for c in request.title)[:50]
            filename = f"{safe_title}_{timestamp}.pdf"
            output_path = settings.output_dir / filename

            # Try WeasyPrint first, fall back to ReportLab
            try:
                await self._render_with_weasyprint(html_content, output_path)
            except ImportError:
                await self._render_with_reportlab(request, output_path)

            # Get file stats
            file_size = output_path.stat().st_size if output_path.exists() else 0

            return RenderResult(
                id=request.id,
                status=RenderStatus.COMPLETED,
                content_type=request.content_type,
                format=ExportFormat.PDF,
                completed_at=datetime.utcnow(),
                file_path=str(output_path),
                file_url=f"/downloads/{filename}",
                file_size=file_size,
                page_count=len(request.sections) + 1,  # +1 for cover
                metadata={"title": request.title},
            )

        except Exception as e:
            return RenderResult(
                id=request.id,
                status=RenderStatus.FAILED,
                content_type=request.content_type,
                format=ExportFormat.PDF,
                error_message=str(e),
            )

    async def _render_with_weasyprint(self, html_content: str, output_path: Path) -> None:
        """Render PDF using WeasyPrint."""
        from weasyprint import HTML

        html = HTML(string=html_content, base_url=str(settings.base_dir))
        html.write_pdf(output_path)

    async def _render_with_reportlab(
        self, request: PDFRenderRequest, output_path: Path
    ) -> None:
        """Render PDF using ReportLab (fallback)."""
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, letter
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            Image,
            PageBreak,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )

        page_size = A4 if settings.pdf_page_size == "A4" else letter

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=page_size,
            topMargin=settings.pdf_margin_top,
            bottomMargin=settings.pdf_margin_bottom,
            leftMargin=settings.pdf_margin_left,
            rightMargin=settings.pdf_margin_right,
        )

        styles = getSampleStyleSheet()

        # Custom styles based on brand
        styles.add(
            ParagraphStyle(
                "BrandTitle",
                parent=styles["Title"],
                textColor=colors.HexColor(self.styler.config.primary_color),
                fontSize=24,
                spaceAfter=20,
            )
        )
        styles.add(
            ParagraphStyle(
                "BrandHeading",
                parent=styles["Heading1"],
                textColor=colors.HexColor(self.styler.config.primary_color),
                fontSize=18,
                spaceAfter=12,
            )
        )

        story = []

        # Cover page
        story.append(Spacer(1, 2 * inch))
        story.append(Paragraph(request.title, styles["BrandTitle"]))
        if request.subtitle:
            story.append(Paragraph(request.subtitle, styles["Heading2"]))
        story.append(Spacer(1, inch))
        if request.prospect:
            story.append(
                Paragraph(f"Prepared for: {request.prospect.company_name}", styles["Normal"])
            )
        if request.author:
            story.append(Paragraph(f"Prepared by: {request.author}", styles["Normal"]))
        story.append(
            Paragraph(f"Date: {self._format_date(request.date)}", styles["Normal"])
        )
        story.append(PageBreak())

        # Sections
        for section in request.sections:
            if section.page_break_before:
                story.append(PageBreak())

            story.append(Paragraph(section.title, styles["BrandHeading"]))
            story.append(Spacer(1, 12))

            for item in section.content:
                if isinstance(item, TextBlock) or (isinstance(item, dict) and "content" in item):
                    content = item.content if isinstance(item, TextBlock) else item.get("content", "")
                    story.append(Paragraph(content, styles["Normal"]))
                    story.append(Spacer(1, 6))
                elif isinstance(item, BulletList) or (isinstance(item, dict) and "items" in item):
                    items = item.items if isinstance(item, BulletList) else item.get("items", [])
                    for bullet in items:
                        story.append(Paragraph(f"• {bullet}", styles["Normal"]))
                    story.append(Spacer(1, 6))

            if section.page_break_after:
                story.append(PageBreak())

        doc.build(story)

    def render_to_bytes(self, request: PDFRenderRequest) -> bytes:
        """Render PDF and return as bytes."""
        html_content = self._generate_html(request)

        try:
            from weasyprint import HTML

            html = HTML(string=html_content, base_url=str(settings.base_dir))
            return html.write_pdf()
        except ImportError:
            # Fallback: write to temp file and read
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                import asyncio

                asyncio.get_event_loop().run_until_complete(
                    self._render_with_reportlab(request, Path(f.name))
                )
                with open(f.name, "rb") as pdf_file:
                    return pdf_file.read()

    def get_html_preview(self, request: PDFRenderRequest) -> str:
        """Generate HTML preview of the PDF."""
        return self._generate_html(request)
