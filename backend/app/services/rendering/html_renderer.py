"""HTML rendering service for web-based deck viewer."""

import hashlib
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from uuid import UUID

from ...core.config import settings
from ...models.rendering import (
    ContentType,
    ExportFormat,
    RenderStatus,
    Slide,
    WebDeckConfig,
    WebDeckRenderRequest,
    WebDeckResult,
)
from .brand_styler import BrandStyler
from .deck_renderer import DeckRenderer


class HTMLRenderer:
    """Renders web-based interactive deck viewer."""

    def __init__(self, brand_config: Optional[dict] = None):
        """Initialize the HTML renderer."""
        self.styler = BrandStyler(brand_config) if brand_config else BrandStyler()
        self.deck_renderer = DeckRenderer(brand_config)
        self._ensure_output_dir()

    def _ensure_output_dir(self) -> None:
        """Ensure output directory exists."""
        (settings.output_dir / "decks").mkdir(parents=True, exist_ok=True)

    def _generate_share_id(self) -> str:
        """Generate a unique share ID."""
        return secrets.token_urlsafe(16)

    def _get_viewer_js(self, config: WebDeckConfig) -> str:
        """Generate JavaScript for the deck viewer."""
        return f"""
class DeckViewer {{
    constructor(options) {{
        this.slides = document.querySelectorAll('.slide');
        this.currentSlide = 0;
        this.totalSlides = this.slides.length;
        this.config = options || {{}};
        this.isFullscreen = false;
        this.presenterMode = false;
        this.timer = null;
        this.startTime = null;

        this.init();
    }}

    init() {{
        this.setupControls();
        this.setupKeyboardNav();
        this.setupTouchNav();
        this.showSlide(0);

        if (this.config.autoAdvance) {{
            this.startAutoAdvance();
        }}
    }}

    setupControls() {{
        const controls = document.querySelector('.deck-controls');
        if (!controls) return;

        const prevBtn = controls.querySelector('.prev-btn');
        const nextBtn = controls.querySelector('.next-btn');
        const fullscreenBtn = controls.querySelector('.fullscreen-btn');
        const presenterBtn = controls.querySelector('.presenter-btn');
        const downloadBtn = controls.querySelector('.download-btn');

        if (prevBtn) prevBtn.addEventListener('click', () => this.prevSlide());
        if (nextBtn) nextBtn.addEventListener('click', () => this.nextSlide());
        if (fullscreenBtn) fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());
        if (presenterBtn) presenterBtn.addEventListener('click', () => this.togglePresenterMode());
        if (downloadBtn) downloadBtn.addEventListener('click', () => this.downloadDeck());

        this.updateCounter();
    }}

    setupKeyboardNav() {{
        document.addEventListener('keydown', (e) => {{
            switch(e.key) {{
                case 'ArrowRight':
                case 'Space':
                case 'PageDown':
                    e.preventDefault();
                    this.nextSlide();
                    break;
                case 'ArrowLeft':
                case 'PageUp':
                    e.preventDefault();
                    this.prevSlide();
                    break;
                case 'Home':
                    e.preventDefault();
                    this.showSlide(0);
                    break;
                case 'End':
                    e.preventDefault();
                    this.showSlide(this.totalSlides - 1);
                    break;
                case 'f':
                case 'F':
                    e.preventDefault();
                    this.toggleFullscreen();
                    break;
                case 'Escape':
                    if (this.isFullscreen) this.toggleFullscreen();
                    break;
            }}
        }});
    }}

    setupTouchNav() {{
        let touchStartX = 0;
        const container = document.querySelector('.deck-container');
        if (!container) return;

        container.addEventListener('touchstart', (e) => {{
            touchStartX = e.touches[0].clientX;
        }});

        container.addEventListener('touchend', (e) => {{
            const touchEndX = e.changedTouches[0].clientX;
            const diff = touchStartX - touchEndX;

            if (Math.abs(diff) > 50) {{
                if (diff > 0) {{
                    this.nextSlide();
                }} else {{
                    this.prevSlide();
                }}
            }}
        }});
    }}

    showSlide(index) {{
        if (index < 0 || index >= this.totalSlides) return;

        this.slides.forEach((slide, i) => {{
            slide.style.display = i === index ? 'flex' : 'none';
            if (i === index) {{
                slide.classList.add('slide-transition-fade');
            }}
        }});

        this.currentSlide = index;
        this.updateCounter();
        this.updateProgress();
    }}

    nextSlide() {{
        if (this.currentSlide < this.totalSlides - 1) {{
            this.showSlide(this.currentSlide + 1);
        }}
    }}

    prevSlide() {{
        if (this.currentSlide > 0) {{
            this.showSlide(this.currentSlide - 1);
        }}
    }}

    updateCounter() {{
        const counter = document.querySelector('.slide-counter');
        if (counter) {{
            counter.textContent = `${{this.currentSlide + 1}} / ${{this.totalSlides}}`;
        }}

        const prevBtn = document.querySelector('.prev-btn');
        const nextBtn = document.querySelector('.next-btn');
        if (prevBtn) prevBtn.disabled = this.currentSlide === 0;
        if (nextBtn) nextBtn.disabled = this.currentSlide === this.totalSlides - 1;
    }}

    updateProgress() {{
        const progress = document.querySelector('.progress');
        if (progress) {{
            const percent = ((this.currentSlide + 1) / this.totalSlides) * 100;
            progress.style.width = `${{percent}}%`;
        }}
    }}

    toggleFullscreen() {{
        const viewer = document.querySelector('.deck-viewer');
        if (!viewer) return;

        if (!document.fullscreenElement) {{
            viewer.requestFullscreen?.() ||
            viewer.webkitRequestFullscreen?.() ||
            viewer.msRequestFullscreen?.();
            this.isFullscreen = true;
            viewer.classList.add('fullscreen');
        }} else {{
            document.exitFullscreen?.() ||
            document.webkitExitFullscreen?.() ||
            document.msExitFullscreen?.();
            this.isFullscreen = false;
            viewer.classList.remove('fullscreen');
        }}
    }}

    togglePresenterMode() {{
        // Open presenter view in new window
        const presenterWindow = window.open('', 'presenter', 'width=1200,height=800');
        if (!presenterWindow) return;

        presenterWindow.document.write(this.getPresenterHTML());
        presenterWindow.document.close();

        // Sync slides between windows
        window.addEventListener('message', (e) => {{
            if (e.data.type === 'slideChange') {{
                this.showSlide(e.data.index);
            }}
        }});
    }}

    getPresenterHTML() {{
        return `
            <!DOCTYPE html>
            <html>
            <head>
                <title>Presenter View</title>
                <style>
                    ${{document.querySelector('style').textContent}}
                </style>
            </head>
            <body>
                <div class="presenter-view">
                    <div class="presenter-current-slide">
                        ${{this.slides[this.currentSlide].outerHTML}}
                    </div>
                    <div class="presenter-sidebar">
                        <div class="presenter-next-slide">
                            ${{this.currentSlide < this.totalSlides - 1 ?
                                this.slides[this.currentSlide + 1].outerHTML :
                                '<p>End of presentation</p>'
                            }}
                        </div>
                        <div class="presenter-notes">
                            ${{this.slides[this.currentSlide].dataset.notes || 'No notes for this slide'}}
                        </div>
                        <div class="presenter-timer">
                            <div class="time">00:00:00</div>
                        </div>
                    </div>
                </div>
            </body>
            </html>
        `;
    }}

    startAutoAdvance() {{
        const interval = this.config.autoAdvanceInterval || 10;
        this.timer = setInterval(() => {{
            if (this.currentSlide < this.totalSlides - 1) {{
                this.nextSlide();
            }} else {{
                this.stopAutoAdvance();
            }}
        }}, interval * 1000);
    }}

    stopAutoAdvance() {{
        if (this.timer) {{
            clearInterval(this.timer);
            this.timer = null;
        }}
    }}

    downloadDeck() {{
        // Trigger download of the original file
        const downloadUrl = document.querySelector('[data-download-url]')?.dataset.downloadUrl;
        if (downloadUrl) {{
            window.location.href = downloadUrl;
        }}
    }}
}}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {{
    new DeckViewer({{
        autoAdvance: {'true' if config.auto_advance else 'false'},
        autoAdvanceInterval: {config.auto_advance_interval},
        enableNavigation: {'true' if config.enable_navigation else 'false'},
        enableFullscreen: {'true' if config.enable_fullscreen else 'false'},
        enablePresenterMode: {'true' if config.enable_presenter_mode else 'false'},
        enableDownload: {'true' if config.enable_download else 'false'}
    }});
}});
"""

    def generate_web_viewer(self, request: WebDeckRenderRequest) -> str:
        """Generate complete HTML for web deck viewer."""
        config = request.config

        # Generate slides HTML using deck renderer
        slides_html = []
        total = len(request.slides)

        for i, slide in enumerate(request.slides):
            slide_html = self.deck_renderer._render_slide_html(
                slide, i, total, request.show_slide_numbers
            )
            # Add speaker notes as data attribute
            if slide.content.speaker_notes:
                slide_html = slide_html.replace(
                    f"id='slide-{slide.id}'",
                    f"id='slide-{slide.id}' data-notes='{slide.content.speaker_notes}'"
                )
            slides_html.append(slide_html)

        # Build control buttons based on config
        controls = []
        if config.enable_navigation:
            controls.append("<button class='prev-btn' title='Previous (←)'>←</button>")
            controls.append("<span class='slide-counter'>1 / {}</span>".format(total))
            controls.append("<button class='next-btn' title='Next (→)'>→</button>")
        if config.enable_fullscreen:
            controls.append("<button class='fullscreen-btn' title='Fullscreen (F)'>⛶</button>")
        if config.enable_presenter_mode:
            controls.append("<button class='presenter-btn' title='Presenter Mode'>📺</button>")
        if config.enable_download:
            controls.append("<button class='download-btn' title='Download'>⬇</button>")

        theme_class = "theme-dark" if config.theme == "dark" else "theme-light"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{request.title}</title>
    <meta name="description" content="{request.subtitle or request.title}">
    <meta property="og:title" content="{request.title}">
    <meta property="og:type" content="website">
    <style>
    {self.styler.get_web_viewer_styles()}

    .theme-dark {{
        --bg-color: #1a1a1a;
        --text-color: #ffffff;
    }}

    .theme-light {{
        --bg-color: #f5f5f5;
        --text-color: #1a1a1a;
    }}

    .deck-viewer {{
        background: var(--bg-color);
    }}

    /* Initial slide hidden state */
    .slide {{
        display: none;
    }}
    .slide:first-child {{
        display: flex;
    }}
    </style>
</head>
<body>
    <div class="deck-viewer {theme_class}" data-download-url="/api/render/download/{request.share_id}">
        <div class="deck-container">
            <div class="slide-wrapper">
                {''.join(slides_html)}
            </div>
        </div>

        <div class="deck-controls">
            {''.join(controls)}
        </div>

        <div class="progress-bar">
            <div class="progress" style="width: {100 / total}%"></div>
        </div>
    </div>

    <script>
    {self._get_viewer_js(config)}
    </script>
</body>
</html>"""
        return html

    async def render(self, request: WebDeckRenderRequest) -> WebDeckResult:
        """Render web deck viewer."""
        try:
            # Generate share ID if not provided
            share_id = request.share_id or self._generate_share_id()

            # Generate HTML
            html_content = self.generate_web_viewer(request)

            # Save to output directory
            filename = f"{share_id}.html"
            output_path = settings.output_dir / "decks" / filename
            output_path.write_text(html_content, encoding="utf-8")

            # Generate URLs
            share_url = f"/deck/{share_id}"
            embed_code = (
                f'<iframe src="{share_url}" width="100%" height="600" '
                f'frameborder="0" allowfullscreen></iframe>'
            )

            # Calculate expiry
            expires_at = None
            if request.config.share_expires_at:
                expires_at = request.config.share_expires_at

            return WebDeckResult(
                id=request.id,
                status=RenderStatus.COMPLETED,
                content_type=request.content_type,
                format=ExportFormat.HTML,
                completed_at=datetime.utcnow(),
                file_path=str(output_path),
                file_url=f"/downloads/decks/{filename}",
                file_size=output_path.stat().st_size,
                page_count=len(request.slides),
                share_url=share_url,
                embed_code=embed_code,
                expires_at=expires_at,
                metadata={
                    "title": request.title,
                    "share_id": share_id,
                },
            )

        except Exception as e:
            return WebDeckResult(
                id=request.id,
                status=RenderStatus.FAILED,
                content_type=request.content_type,
                format=ExportFormat.HTML,
                error_message=str(e),
            )

    def get_viewer_by_share_id(self, share_id: str) -> Optional[str]:
        """Get viewer HTML by share ID."""
        file_path = settings.output_dir / "decks" / f"{share_id}.html"
        if file_path.exists():
            return file_path.read_text(encoding="utf-8")
        return None
