"""API routes for rendering service."""

from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Response
from fastapi.responses import FileResponse, HTMLResponse

from ..core.config import settings
from ..models.rendering import (
    BrandConfig,
    ContentType,
    DeckRenderRequest,
    ExportFormat,
    PDFRenderRequest,
    RenderResult,
    RenderStatus,
    TemplateInfo,
    TemplateListResponse,
    WebDeckConfig,
    WebDeckRenderRequest,
    WebDeckResult,
)
from ..services.rendering import (
    BrandStyler,
    DeckRenderer,
    ExportService,
    HTMLRenderer,
    PDFRenderer,
)

router = APIRouter(prefix="/render", tags=["rendering"])


# ============================================================================
# PDF Rendering Endpoints
# ============================================================================


@router.post("/pdf", response_model=RenderResult)
async def render_pdf(request: PDFRenderRequest) -> RenderResult:
    """
    Render a PDF document from content JSON.

    Supports proposals, one-pagers, executive summaries, and case studies.
    The document will be professionally styled with brand colors and typography.
    """
    renderer = PDFRenderer()
    result = await renderer.render(request)

    if result.status == RenderStatus.FAILED:
        raise HTTPException(status_code=500, detail=result.error_message)

    return result


@router.post("/pdf/preview", response_class=HTMLResponse)
async def preview_pdf(request: PDFRenderRequest) -> HTMLResponse:
    """
    Generate an HTML preview of the PDF document.

    Useful for reviewing content before final PDF generation.
    """
    renderer = PDFRenderer()
    html_content = renderer.get_html_preview(request)
    return HTMLResponse(content=html_content)


# ============================================================================
# Deck Rendering Endpoints
# ============================================================================


@router.post("/deck", response_model=RenderResult)
async def render_deck(request: DeckRenderRequest) -> RenderResult:
    """
    Render a slide deck from content JSON.

    Supports pitch decks and QBR decks.
    Export formats: PDF, PPTX, HTML
    """
    renderer = DeckRenderer()
    result = await renderer.render(request)

    if result.status == RenderStatus.FAILED:
        raise HTTPException(status_code=500, detail=result.error_message)

    return result


@router.post("/deck/preview", response_class=HTMLResponse)
async def preview_deck(request: DeckRenderRequest) -> HTMLResponse:
    """
    Generate an HTML preview of the slide deck.

    Returns all slides as static HTML for review.
    """
    renderer = DeckRenderer()
    html_content = renderer.generate_html(request)
    return HTMLResponse(content=html_content)


# ============================================================================
# Web Deck Viewer Endpoints
# ============================================================================


@router.post("/web-deck", response_model=WebDeckResult)
async def create_web_deck(request: WebDeckRenderRequest) -> WebDeckResult:
    """
    Create an interactive web deck viewer.

    Generates a shareable link with navigation, fullscreen,
    and optional presenter mode.
    """
    renderer = HTMLRenderer()
    result = await renderer.render(request)

    if result.status == RenderStatus.FAILED:
        raise HTTPException(status_code=500, detail=result.error_message)

    return result


@router.get("/deck/{share_id}", response_class=HTMLResponse)
async def get_web_deck(share_id: str) -> HTMLResponse:
    """
    Retrieve a web deck by its share ID.

    Returns the interactive deck viewer HTML.
    """
    renderer = HTMLRenderer()
    html_content = renderer.get_viewer_by_share_id(share_id)

    if not html_content:
        raise HTTPException(status_code=404, detail="Deck not found")

    return HTMLResponse(content=html_content)


# ============================================================================
# Multi-Format Export Endpoints
# ============================================================================


@router.post("/export", response_model=RenderResult)
async def export_content(
    request: PDFRenderRequest | DeckRenderRequest,
) -> RenderResult:
    """
    Export content to the specified format.

    Unified endpoint that handles both PDF documents and slide decks.
    """
    service = ExportService()
    result = await service.export(request)

    if result.status == RenderStatus.FAILED:
        raise HTTPException(status_code=500, detail=result.error_message)

    return result


@router.post("/export/multiple", response_model=list[RenderResult])
async def export_multiple_formats(
    request: PDFRenderRequest | DeckRenderRequest,
    formats: list[ExportFormat] = Query(...),
) -> list[RenderResult]:
    """
    Export content to multiple formats simultaneously.

    Useful for generating PDF, PPTX, and HTML versions at once.
    """
    service = ExportService()
    results = await service.export_multiple(request, formats)
    return results


# ============================================================================
# Download Endpoints
# ============================================================================


@router.get("/download/{filename}")
async def download_file(filename: str) -> FileResponse:
    """
    Download a rendered file by filename.

    Returns the file with appropriate content-type headers.
    """
    file_path = settings.output_dir / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    # Determine media type
    suffix = file_path.suffix.lower()
    media_types = {
        ".pdf": "application/pdf",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".html": "text/html",
    }
    media_type = media_types.get(suffix, "application/octet-stream")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type,
    )


@router.get("/download/decks/{filename}")
async def download_deck_file(filename: str) -> FileResponse:
    """
    Download a deck file by filename.
    """
    file_path = settings.output_dir / "decks" / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="text/html",
    )


# ============================================================================
# Template & Configuration Endpoints
# ============================================================================


@router.get("/templates", response_model=TemplateListResponse)
async def list_templates(
    content_type: Optional[ContentType] = None,
) -> TemplateListResponse:
    """
    List available content templates.

    Optionally filter by content type.
    """
    # In a full implementation, this would query a database or file system
    templates = [
        TemplateInfo(
            id="proposal-standard",
            name="Standard Proposal",
            description="Professional proposal template with cover page, sections, and signature block",
            content_type=ContentType.PROPOSAL,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        ),
        TemplateInfo(
            id="one-pager-compact",
            name="Compact One-Pager",
            description="Single-page executive summary with key metrics",
            content_type=ContentType.ONE_PAGER,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        ),
        TemplateInfo(
            id="pitch-deck-modern",
            name="Modern Pitch Deck",
            description="Clean, modern pitch deck with gradient title slides",
            content_type=ContentType.PITCH_DECK,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        ),
        TemplateInfo(
            id="qbr-deck-executive",
            name="Executive QBR Deck",
            description="Quarterly business review deck with metrics and timeline",
            content_type=ContentType.QBR_DECK,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        ),
    ]

    if content_type:
        templates = [t for t in templates if t.content_type == content_type]

    return TemplateListResponse(templates=templates, total=len(templates))


@router.get("/formats/{content_type}", response_model=list[ExportFormat])
async def get_supported_formats(content_type: ContentType) -> list[ExportFormat]:
    """
    Get supported export formats for a content type.
    """
    service = ExportService()
    return service.get_supported_formats(content_type)


@router.get("/brand/preview", response_class=HTMLResponse)
async def preview_brand_styles(
    primary_color: str = Query(default="#1E40AF"),
    secondary_color: str = Query(default="#3B82F6"),
    accent_color: str = Query(default="#10B981"),
) -> HTMLResponse:
    """
    Preview brand styling with custom colors.

    Returns a sample page showing typography and components
    with the specified brand colors.
    """
    config = BrandConfig(
        primary_color=primary_color,
        secondary_color=secondary_color,
        accent_color=accent_color,
    )
    styler = BrandStyler(config)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Brand Preview</title>
        <style>
        {styler.get_pdf_styles()}
        body {{ padding: 40px; max-width: 800px; margin: 0 auto; }}
        </style>
    </head>
    <body>
        <h1>Brand Style Preview</h1>
        <p>This is a preview of your brand styling.</p>

        <h2>Typography</h2>
        <h3>Heading Level 3</h3>
        <p>Regular paragraph text with <strong>bold</strong> and <em>italic</em> styles.</p>

        <div class="highlight">
            <strong>Highlight Box:</strong> This is an important callout.
        </div>

        <h2>Metrics</h2>
        <div style="display: flex; gap: 20px;">
            <div class="metric">
                <div class="metric-value">150%</div>
                <div class="metric-label">Growth Rate</div>
            </div>
            <div class="metric">
                <div class="metric-value">$2.5M</div>
                <div class="metric-label">Revenue</div>
            </div>
        </div>

        <h2>Lists</h2>
        <ul class="bullet-list">
            <li>First bullet point</li>
            <li>Second bullet point</li>
            <li>Third bullet point</li>
        </ul>

        <ul class="check-list">
            <li>Completed item one</li>
            <li>Completed item two</li>
        </ul>

        <h2>Table</h2>
        <table>
            <thead>
                <tr>
                    <th>Feature</th>
                    <th>Basic</th>
                    <th>Pro</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Users</td>
                    <td>5</td>
                    <td>Unlimited</td>
                </tr>
                <tr>
                    <td>Storage</td>
                    <td>10GB</td>
                    <td>100GB</td>
                </tr>
            </tbody>
        </table>

        <blockquote>
            "This is a sample quote that demonstrates the blockquote styling."
        </blockquote>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


# ============================================================================
# Utility Endpoints
# ============================================================================


@router.delete("/cleanup")
async def cleanup_old_exports(
    max_age_hours: int = Query(default=24, ge=1, le=168),
    background_tasks: BackgroundTasks = None,
) -> dict:
    """
    Clean up old exported files.

    Removes files older than the specified age (default 24 hours).
    Runs in the background if background_tasks is available.
    """
    service = ExportService()

    async def do_cleanup():
        return await service.cleanup_old_exports(max_age_hours)

    if background_tasks:
        background_tasks.add_task(do_cleanup)
        return {"message": "Cleanup scheduled", "max_age_hours": max_age_hours}
    else:
        count = await do_cleanup()
        return {"message": "Cleanup completed", "files_removed": count}


@router.get("/health")
async def render_health_check() -> dict:
    """
    Health check for rendering service.

    Verifies that output directories exist and are writable.
    """
    checks = {
        "output_dir_exists": settings.output_dir.exists(),
        "output_dir_writable": settings.output_dir.exists()
        and (settings.output_dir / ".write_test").touch() is None,
        "templates_dir_exists": settings.templates_dir.exists(),
        "assets_dir_exists": settings.assets_dir.exists(),
    }

    # Clean up write test
    write_test = settings.output_dir / ".write_test"
    if write_test.exists():
        write_test.unlink()

    all_healthy = all(checks.values())

    return {
        "status": "healthy" if all_healthy else "degraded",
        "checks": checks,
    }
