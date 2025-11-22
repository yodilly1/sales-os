"""Export service for multiple format support."""

import asyncio
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Optional, Union
from uuid import UUID

from ...core.config import settings
from ...models.rendering import (
    ContentType,
    DeckRenderRequest,
    ExportFormat,
    PDFRenderRequest,
    RenderResult,
    RenderStatus,
    WebDeckRenderRequest,
)
from .brand_styler import BrandStyler
from .deck_renderer import DeckRenderer
from .html_renderer import HTMLRenderer
from .pdf_renderer import PDFRenderer


class ExportService:
    """Unified export service for all rendering formats."""

    def __init__(self, brand_config: Optional[dict] = None):
        """Initialize export service with renderers."""
        self.pdf_renderer = PDFRenderer(brand_config)
        self.deck_renderer = DeckRenderer(brand_config)
        self.html_renderer = HTMLRenderer(brand_config)
        self.styler = BrandStyler(brand_config) if brand_config else BrandStyler()

    async def export(
        self,
        request: Union[PDFRenderRequest, DeckRenderRequest, WebDeckRenderRequest],
    ) -> RenderResult:
        """Export content to the specified format."""
        if isinstance(request, PDFRenderRequest):
            return await self._export_pdf(request)
        elif isinstance(request, WebDeckRenderRequest):
            return await self._export_web_deck(request)
        elif isinstance(request, DeckRenderRequest):
            return await self._export_deck(request)
        else:
            return RenderResult(
                id=request.id,
                status=RenderStatus.FAILED,
                content_type=request.content_type,
                format=request.format,
                error_message="Unsupported request type",
            )

    async def _export_pdf(self, request: PDFRenderRequest) -> RenderResult:
        """Export as PDF document."""
        return await self.pdf_renderer.render(request)

    async def _export_deck(self, request: DeckRenderRequest) -> RenderResult:
        """Export as deck (PDF, PPTX, or HTML)."""
        return await self.deck_renderer.render(request)

    async def _export_web_deck(self, request: WebDeckRenderRequest) -> RenderResult:
        """Export as interactive web deck."""
        return await self.html_renderer.render(request)

    async def export_multiple(
        self,
        request: Union[PDFRenderRequest, DeckRenderRequest],
        formats: list[ExportFormat],
    ) -> list[RenderResult]:
        """Export content to multiple formats simultaneously."""
        tasks = []

        for fmt in formats:
            # Create a copy of the request with the new format
            request_copy = request.model_copy(update={"format": fmt})
            tasks.append(self.export(request_copy))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to failed results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(
                    RenderResult(
                        id=request.id,
                        status=RenderStatus.FAILED,
                        content_type=request.content_type,
                        format=formats[i],
                        error_message=str(result),
                    )
                )
            else:
                final_results.append(result)

        return final_results

    def get_supported_formats(self, content_type: ContentType) -> list[ExportFormat]:
        """Get supported export formats for a content type."""
        format_map = {
            ContentType.PROPOSAL: [ExportFormat.PDF, ExportFormat.HTML],
            ContentType.ONE_PAGER: [ExportFormat.PDF, ExportFormat.HTML],
            ContentType.PITCH_DECK: [ExportFormat.PDF, ExportFormat.PPTX, ExportFormat.HTML],
            ContentType.QBR_DECK: [ExportFormat.PDF, ExportFormat.PPTX, ExportFormat.HTML],
            ContentType.EXECUTIVE_SUMMARY: [ExportFormat.PDF, ExportFormat.HTML],
            ContentType.CASE_STUDY: [ExportFormat.PDF, ExportFormat.HTML],
        }
        return format_map.get(content_type, [ExportFormat.PDF])

    def get_mime_type(self, format: ExportFormat) -> str:
        """Get MIME type for export format."""
        mime_map = {
            ExportFormat.PDF: "application/pdf",
            ExportFormat.PPTX: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ExportFormat.HTML: "text/html",
        }
        return mime_map.get(format, "application/octet-stream")

    def get_file_extension(self, format: ExportFormat) -> str:
        """Get file extension for export format."""
        extension_map = {
            ExportFormat.PDF: ".pdf",
            ExportFormat.PPTX: ".pptx",
            ExportFormat.HTML: ".html",
        }
        return extension_map.get(format, "")

    async def get_download_info(self, file_path: str) -> Optional[dict]:
        """Get download information for a rendered file."""
        path = Path(file_path)
        if not path.exists():
            return None

        mime_type, _ = mimetypes.guess_type(str(path))

        return {
            "filename": path.name,
            "size": path.stat().st_size,
            "mime_type": mime_type or "application/octet-stream",
            "created_at": datetime.fromtimestamp(path.stat().st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
        }

    async def cleanup_old_exports(self, max_age_hours: int = 24) -> int:
        """Clean up exports older than specified age."""
        count = 0
        cutoff = datetime.now().timestamp() - (max_age_hours * 3600)

        for path in settings.output_dir.rglob("*"):
            if path.is_file() and path.stat().st_mtime < cutoff:
                path.unlink()
                count += 1

        return count


# Convenience functions for quick exports
async def quick_export_pdf(
    title: str,
    sections: list[dict],
    brand_config: Optional[dict] = None,
    **kwargs,
) -> RenderResult:
    """Quick helper to export a PDF document."""
    from ...models.rendering import DocumentSection

    request = PDFRenderRequest(
        content_type=ContentType.PROPOSAL,
        title=title,
        sections=[DocumentSection(**s) for s in sections],
        **kwargs,
    )

    service = ExportService(brand_config)
    return await service.export(request)


async def quick_export_deck(
    title: str,
    slides: list[dict],
    format: ExportFormat = ExportFormat.PPTX,
    brand_config: Optional[dict] = None,
    **kwargs,
) -> RenderResult:
    """Quick helper to export a slide deck."""
    from ...models.rendering import Slide, SlideContent

    request = DeckRenderRequest(
        content_type=ContentType.PITCH_DECK,
        format=format,
        title=title,
        slides=[
            Slide(content=SlideContent(**s)) if isinstance(s, dict) else s
            for s in slides
        ],
        **kwargs,
    )

    service = ExportService(brand_config)
    return await service.export(request)
