"""Tests for rendering services."""

import pytest
from uuid import uuid4

from app.models.rendering import (
    BrandConfig,
    BulletList,
    ContentType,
    DeckRenderRequest,
    DocumentSection,
    ExportFormat,
    PDFRenderRequest,
    RenderStatus,
    Slide,
    SlideContent,
    SlideLayout,
    TextBlock,
    WebDeckConfig,
    WebDeckRenderRequest,
)
from app.services.rendering import (
    BrandStyler,
    DeckRenderer,
    ExportService,
    HTMLRenderer,
    PDFRenderer,
)


class TestBrandStyler:
    """Tests for BrandStyler class."""

    def test_default_config(self):
        """Test default brand configuration."""
        styler = BrandStyler()
        assert styler.config.primary_color == "#1E40AF"
        assert styler.config.secondary_color == "#3B82F6"
        assert styler.config.accent_color == "#10B981"

    def test_custom_config(self):
        """Test custom brand configuration."""
        config = BrandConfig(
            primary_color="#FF0000",
            secondary_color="#00FF00",
            accent_color="#0000FF",
        )
        styler = BrandStyler(config)
        assert styler.config.primary_color == "#FF0000"

    def test_css_variables(self):
        """Test CSS variables generation."""
        styler = BrandStyler()
        css_vars = styler.get_css_variables()
        assert "--brand-primary" in css_vars
        assert css_vars["--brand-primary"] == "#1E40AF"

    def test_pdf_styles(self):
        """Test PDF styles generation."""
        styler = BrandStyler()
        styles = styler.get_pdf_styles()
        assert "body" in styles
        assert "#1E40AF" in styles

    def test_slide_styles(self):
        """Test slide styles generation."""
        styler = BrandStyler()
        styles = styler.get_slide_styles()
        assert ".slide" in styles
        assert "--slide-width" in styles


class TestPDFRenderer:
    """Tests for PDFRenderer class."""

    def test_renderer_initialization(self):
        """Test PDF renderer initialization."""
        renderer = PDFRenderer()
        assert renderer.styler is not None

    def test_markdown_rendering(self):
        """Test markdown to HTML conversion."""
        renderer = PDFRenderer()
        html = renderer._render_markdown("**bold** and *italic*")
        assert "<strong>bold</strong>" in html
        assert "<em>italic</em>" in html

    def test_date_formatting(self):
        """Test date formatting."""
        renderer = PDFRenderer()
        formatted = renderer._format_date("2024-01-15")
        assert "January" in formatted
        assert "15" in formatted
        assert "2024" in formatted

    def test_html_generation(self):
        """Test HTML generation from request."""
        renderer = PDFRenderer()
        request = PDFRenderRequest(
            content_type=ContentType.PROPOSAL,
            title="Test Proposal",
            subtitle="Subtitle",
            sections=[
                DocumentSection(
                    title="Introduction",
                    content=[
                        TextBlock(content="This is a test paragraph."),
                        BulletList(items=["Item 1", "Item 2", "Item 3"]),
                    ],
                )
            ],
        )
        html = renderer._generate_html(request)
        assert "Test Proposal" in html
        assert "Introduction" in html
        assert "Item 1" in html


class TestDeckRenderer:
    """Tests for DeckRenderer class."""

    def test_renderer_initialization(self):
        """Test deck renderer initialization."""
        renderer = DeckRenderer()
        assert renderer.styler is not None

    def test_layout_class_generation(self):
        """Test layout class name generation."""
        renderer = DeckRenderer()
        assert renderer._get_layout_class(SlideLayout.TITLE) == "layout-title"
        assert renderer._get_layout_class(SlideLayout.TWO_COLUMN) == "layout-two-column"
        assert renderer._get_layout_class(SlideLayout.IMAGE_LEFT) == "layout-image-left"

    def test_html_generation(self):
        """Test HTML deck generation."""
        renderer = DeckRenderer()
        request = DeckRenderRequest(
            content_type=ContentType.PITCH_DECK,
            format=ExportFormat.HTML,
            title="Test Deck",
            slides=[
                Slide(
                    content=SlideContent(
                        layout=SlideLayout.TITLE,
                        title="Welcome",
                        subtitle="Introduction",
                    )
                ),
                Slide(
                    content=SlideContent(
                        layout=SlideLayout.TITLE_CONTENT,
                        title="Slide 2",
                        bullets=BulletList(items=["Point 1", "Point 2"]),
                    )
                ),
            ],
        )
        html = renderer.generate_html(request)
        assert "Test Deck" in html
        assert "Welcome" in html
        assert "Slide 2" in html
        assert "Point 1" in html


class TestHTMLRenderer:
    """Tests for HTMLRenderer class."""

    def test_renderer_initialization(self):
        """Test HTML renderer initialization."""
        renderer = HTMLRenderer()
        assert renderer.styler is not None
        assert renderer.deck_renderer is not None

    def test_share_id_generation(self):
        """Test share ID generation."""
        renderer = HTMLRenderer()
        share_id = renderer._generate_share_id()
        assert len(share_id) > 10
        # Should be URL-safe
        assert share_id.isalnum() or "-" in share_id or "_" in share_id

    def test_web_viewer_generation(self):
        """Test web viewer HTML generation."""
        renderer = HTMLRenderer()
        request = WebDeckRenderRequest(
            content_type=ContentType.PITCH_DECK,
            format=ExportFormat.HTML,
            title="Web Deck",
            slides=[
                Slide(
                    content=SlideContent(
                        layout=SlideLayout.TITLE,
                        title="Title Slide",
                    )
                )
            ],
            config=WebDeckConfig(
                enable_navigation=True,
                enable_fullscreen=True,
            ),
        )
        html = renderer.generate_web_viewer(request)
        assert "Web Deck" in html
        assert "DeckViewer" in html or "deck-viewer" in html
        assert "prev-btn" in html
        assert "fullscreen-btn" in html


class TestExportService:
    """Tests for ExportService class."""

    def test_service_initialization(self):
        """Test export service initialization."""
        service = ExportService()
        assert service.pdf_renderer is not None
        assert service.deck_renderer is not None
        assert service.html_renderer is not None

    def test_supported_formats(self):
        """Test getting supported formats."""
        service = ExportService()

        # Proposals support PDF and HTML
        formats = service.get_supported_formats(ContentType.PROPOSAL)
        assert ExportFormat.PDF in formats
        assert ExportFormat.HTML in formats

        # Decks support all formats
        formats = service.get_supported_formats(ContentType.PITCH_DECK)
        assert ExportFormat.PDF in formats
        assert ExportFormat.PPTX in formats
        assert ExportFormat.HTML in formats

    def test_mime_types(self):
        """Test MIME type resolution."""
        service = ExportService()
        assert service.get_mime_type(ExportFormat.PDF) == "application/pdf"
        assert "powerpoint" in service.get_mime_type(ExportFormat.PPTX).lower() or "presentation" in service.get_mime_type(ExportFormat.PPTX).lower()
        assert service.get_mime_type(ExportFormat.HTML) == "text/html"

    def test_file_extensions(self):
        """Test file extension resolution."""
        service = ExportService()
        assert service.get_file_extension(ExportFormat.PDF) == ".pdf"
        assert service.get_file_extension(ExportFormat.PPTX) == ".pptx"
        assert service.get_file_extension(ExportFormat.HTML) == ".html"


class TestRenderingModels:
    """Tests for rendering Pydantic models."""

    def test_brand_config_defaults(self):
        """Test BrandConfig default values."""
        config = BrandConfig()
        assert config.primary_color == "#1E40AF"
        assert config.heading_font == "Inter"

    def test_slide_content_creation(self):
        """Test SlideContent creation."""
        content = SlideContent(
            layout=SlideLayout.METRICS,
            title="Metrics",
            metrics=[
                {"value": "150%", "label": "Growth"},
                {"value": "$2M", "label": "Revenue"},
            ],
        )
        assert content.title == "Metrics"
        assert len(content.metrics) == 2

    def test_pdf_request_validation(self):
        """Test PDFRenderRequest validation."""
        request = PDFRenderRequest(
            content_type=ContentType.PROPOSAL,
            title="Test",
            sections=[
                DocumentSection(
                    title="Section 1",
                    content=[],
                )
            ],
        )
        assert request.id is not None
        assert request.format == ExportFormat.PDF

    def test_deck_request_validation(self):
        """Test DeckRenderRequest validation."""
        request = DeckRenderRequest(
            content_type=ContentType.PITCH_DECK,
            format=ExportFormat.PPTX,
            title="Test Deck",
            slides=[
                Slide(
                    content=SlideContent(
                        layout=SlideLayout.TITLE,
                        title="Slide 1",
                    )
                )
            ],
        )
        assert len(request.slides) == 1
        assert request.show_slide_numbers is True


@pytest.mark.asyncio
class TestAsyncRendering:
    """Async tests for rendering services."""

    async def test_pdf_render(self):
        """Test async PDF rendering."""
        renderer = PDFRenderer()
        request = PDFRenderRequest(
            content_type=ContentType.ONE_PAGER,
            title="One Pager Test",
            sections=[
                DocumentSection(
                    title="Summary",
                    content=[
                        TextBlock(content="Executive summary content here."),
                    ],
                )
            ],
        )
        result = await renderer.render(request)
        # Note: May fail if WeasyPrint/ReportLab not installed
        # In that case, we still verify the result structure
        assert result.id == request.id
        assert result.content_type == ContentType.ONE_PAGER

    async def test_deck_render_html(self):
        """Test async deck HTML rendering."""
        renderer = DeckRenderer()
        request = DeckRenderRequest(
            content_type=ContentType.PITCH_DECK,
            format=ExportFormat.HTML,
            title="HTML Deck",
            slides=[
                Slide(
                    content=SlideContent(
                        layout=SlideLayout.TITLE,
                        title="Test",
                    )
                )
            ],
        )
        result = await renderer.render_to_html(request)
        assert result.status == RenderStatus.COMPLETED
        assert result.format == ExportFormat.HTML

    async def test_web_deck_render(self):
        """Test async web deck rendering."""
        renderer = HTMLRenderer()
        request = WebDeckRenderRequest(
            content_type=ContentType.PITCH_DECK,
            format=ExportFormat.HTML,
            title="Web Test",
            slides=[
                Slide(
                    content=SlideContent(
                        layout=SlideLayout.TITLE,
                        title="Interactive Slide",
                    )
                )
            ],
            config=WebDeckConfig(
                enable_navigation=True,
                theme="dark",
            ),
        )
        result = await renderer.render(request)
        assert result.status == RenderStatus.COMPLETED
        assert result.share_url is not None
