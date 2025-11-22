"""Brand styling service for consistent rendering."""

from pathlib import Path
from typing import Optional

from ...core.config import settings
from ...models.rendering import BrandConfig


class BrandStyler:
    """Manages brand styling for rendered content."""

    def __init__(self, brand_config: Optional[BrandConfig] = None):
        """Initialize with optional brand configuration."""
        self.config = brand_config or BrandConfig()
        self._load_assets()

    def _load_assets(self) -> None:
        """Load brand assets (logos, fonts)."""
        self.logos_dir = settings.assets_dir / "logos"
        self.fonts_dir = settings.assets_dir / "fonts"

    def get_logo_path(self) -> Optional[Path]:
        """Get the path to the brand logo."""
        if self.config.logo_url:
            # If it's a local path, return it
            logo_path = Path(self.config.logo_url)
            if logo_path.exists():
                return logo_path
        # Try default logo
        default_logo = self.logos_dir / "logo.png"
        if default_logo.exists():
            return default_logo
        return None

    def get_css_variables(self) -> dict[str, str]:
        """Get CSS custom properties for brand styling."""
        return {
            "--brand-primary": self.config.primary_color,
            "--brand-secondary": self.config.secondary_color,
            "--brand-accent": self.config.accent_color,
            "--brand-text": self.config.text_color,
            "--brand-light": self.config.light_color,
            "--font-heading": self.config.heading_font,
            "--font-body": self.config.body_font,
        }

    def get_pdf_styles(self) -> str:
        """Generate CSS styles for PDF rendering."""
        return f"""
        :root {{
            --brand-primary: {self.config.primary_color};
            --brand-secondary: {self.config.secondary_color};
            --brand-accent: {self.config.accent_color};
            --brand-text: {self.config.text_color};
            --brand-light: {self.config.light_color};
        }}

        @page {{
            size: {settings.pdf_page_size};
            margin: {settings.pdf_margin_top}pt {settings.pdf_margin_right}pt
                    {settings.pdf_margin_bottom}pt {settings.pdf_margin_left}pt;
        }}

        body {{
            font-family: {self.config.body_font}, system-ui, sans-serif;
            color: {self.config.text_color};
            line-height: 1.6;
            font-size: 11pt;
        }}

        h1, h2, h3, h4, h5, h6 {{
            font-family: {self.config.heading_font}, system-ui, sans-serif;
            color: {self.config.primary_color};
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            line-height: 1.3;
        }}

        h1 {{
            font-size: 24pt;
            border-bottom: 2px solid {self.config.primary_color};
            padding-bottom: 0.3em;
        }}

        h2 {{
            font-size: 18pt;
        }}

        h3 {{
            font-size: 14pt;
        }}

        p {{
            margin-bottom: 1em;
        }}

        .highlight {{
            background-color: {self.config.light_color};
            padding: 1em;
            border-left: 4px solid {self.config.primary_color};
            margin: 1em 0;
        }}

        .metric {{
            text-align: center;
            padding: 1em;
        }}

        .metric-value {{
            font-size: 32pt;
            font-weight: bold;
            color: {self.config.primary_color};
        }}

        .metric-label {{
            font-size: 12pt;
            color: {self.config.text_color};
            opacity: 0.8;
        }}

        .bullet-list {{
            list-style-type: disc;
            margin-left: 2em;
            margin-bottom: 1em;
        }}

        .numbered-list {{
            list-style-type: decimal;
            margin-left: 2em;
            margin-bottom: 1em;
        }}

        .check-list {{
            list-style-type: none;
            margin-left: 0;
        }}

        .check-list li::before {{
            content: "✓ ";
            color: {self.config.accent_color};
            font-weight: bold;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1em 0;
        }}

        th, td {{
            padding: 0.75em;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
        }}

        th {{
            background-color: {self.config.light_color};
            font-weight: 600;
            color: {self.config.primary_color};
        }}

        .page-header {{
            position: running(header);
            font-size: 9pt;
            color: #6b7280;
            border-bottom: 1px solid #e5e7eb;
            padding-bottom: 0.5em;
        }}

        .page-footer {{
            position: running(footer);
            font-size: 9pt;
            color: #6b7280;
            text-align: center;
        }}

        @page {{
            @top-center {{
                content: element(header);
            }}
            @bottom-center {{
                content: element(footer);
            }}
        }}

        .page-number::after {{
            content: counter(page);
        }}

        .page-break {{
            page-break-after: always;
        }}

        .cover-page {{
            text-align: center;
            padding-top: 200pt;
        }}

        .cover-title {{
            font-size: 36pt;
            color: {self.config.primary_color};
            margin-bottom: 0.5em;
        }}

        .cover-subtitle {{
            font-size: 18pt;
            color: {self.config.secondary_color};
            margin-bottom: 2em;
        }}

        .cover-meta {{
            font-size: 12pt;
            color: #6b7280;
        }}

        blockquote {{
            border-left: 4px solid {self.config.accent_color};
            padding-left: 1em;
            margin: 1em 0;
            font-style: italic;
            color: #4b5563;
        }}

        .toc {{
            margin: 2em 0;
        }}

        .toc-item {{
            display: flex;
            justify-content: space-between;
            padding: 0.5em 0;
            border-bottom: 1px dotted #d1d5db;
        }}

        .toc-item a {{
            color: {self.config.text_color};
            text-decoration: none;
        }}
        """

    def get_slide_styles(self) -> str:
        """Generate CSS styles for slide rendering."""
        return f"""
        :root {{
            --brand-primary: {self.config.primary_color};
            --brand-secondary: {self.config.secondary_color};
            --brand-accent: {self.config.accent_color};
            --brand-text: {self.config.text_color};
            --brand-light: {self.config.light_color};
            --slide-width: {settings.deck_width}px;
            --slide-height: {settings.deck_height}px;
        }}

        .slide {{
            width: var(--slide-width);
            height: var(--slide-height);
            background: white;
            font-family: {self.config.body_font}, system-ui, sans-serif;
            color: {self.config.text_color};
            position: relative;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            padding: 60px 80px;
            box-sizing: border-box;
        }}

        .slide-title {{
            font-family: {self.config.heading_font}, system-ui, sans-serif;
            font-size: 48px;
            font-weight: 700;
            color: {self.config.primary_color};
            margin-bottom: 40px;
            line-height: 1.2;
        }}

        .slide-subtitle {{
            font-size: 28px;
            color: {self.config.secondary_color};
            margin-top: -30px;
            margin-bottom: 40px;
        }}

        .slide-body {{
            flex: 1;
            font-size: 24px;
            line-height: 1.5;
        }}

        .slide-body p {{
            margin-bottom: 20px;
        }}

        .slide-body ul {{
            margin-left: 40px;
        }}

        .slide-body li {{
            margin-bottom: 16px;
        }}

        .slide-logo {{
            position: absolute;
            top: 30px;
            right: 40px;
            max-height: 50px;
            max-width: 150px;
        }}

        .slide-number {{
            position: absolute;
            bottom: 30px;
            right: 40px;
            font-size: 18px;
            color: #9ca3af;
        }}

        /* Title slide layout */
        .slide.layout-title {{
            justify-content: center;
            align-items: center;
            text-align: center;
            background: linear-gradient(135deg, {self.config.primary_color} 0%, {self.config.secondary_color} 100%);
        }}

        .slide.layout-title .slide-title {{
            font-size: 64px;
            color: white;
            margin-bottom: 20px;
        }}

        .slide.layout-title .slide-subtitle {{
            font-size: 32px;
            color: rgba(255, 255, 255, 0.9);
        }}

        /* Two column layout */
        .slide.layout-two-column .slide-content {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 60px;
            flex: 1;
        }}

        /* Image layouts */
        .slide.layout-image-left .slide-content,
        .slide.layout-image-right .slide-content {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 60px;
            flex: 1;
            align-items: center;
        }}

        .slide.layout-image-right .slide-content {{
            grid-template-columns: 1fr 1fr;
        }}

        .slide.layout-image-right .slide-image {{
            order: 2;
        }}

        .slide-image {{
            width: 100%;
            height: 100%;
            object-fit: contain;
        }}

        /* Full image layout */
        .slide.layout-full-image {{
            padding: 0;
        }}

        .slide.layout-full-image .slide-image {{
            position: absolute;
            inset: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}

        .slide.layout-full-image .slide-overlay {{
            position: absolute;
            inset: 0;
            background: linear-gradient(to bottom, rgba(0,0,0,0.3), rgba(0,0,0,0.7));
        }}

        .slide.layout-full-image .slide-title {{
            position: absolute;
            bottom: 100px;
            left: 80px;
            right: 80px;
            color: white;
        }}

        /* Quote layout */
        .slide.layout-quote {{
            justify-content: center;
            align-items: center;
            text-align: center;
            background: {self.config.light_color};
        }}

        .slide.layout-quote .quote-text {{
            font-size: 36px;
            font-style: italic;
            color: {self.config.text_color};
            max-width: 80%;
            line-height: 1.6;
        }}

        .slide.layout-quote .quote-text::before {{
            content: '"';
            font-size: 72px;
            color: {self.config.accent_color};
            display: block;
            margin-bottom: -20px;
        }}

        .slide.layout-quote .quote-author {{
            font-size: 24px;
            color: {self.config.secondary_color};
            margin-top: 30px;
        }}

        /* Metrics layout */
        .slide.layout-metrics .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 40px;
            flex: 1;
            align-content: center;
        }}

        .metric-card {{
            text-align: center;
            padding: 30px;
            background: {self.config.light_color};
            border-radius: 12px;
        }}

        .metric-card .metric-value {{
            font-size: 56px;
            font-weight: 700;
            color: {self.config.primary_color};
            line-height: 1;
        }}

        .metric-card .metric-label {{
            font-size: 20px;
            color: {self.config.text_color};
            margin-top: 10px;
        }}

        .metric-card .metric-trend {{
            font-size: 18px;
            margin-top: 8px;
        }}

        .metric-card .metric-trend.up {{
            color: #10b981;
        }}

        .metric-card .metric-trend.down {{
            color: #ef4444;
        }}

        /* CTA layout */
        .slide.layout-cta {{
            justify-content: center;
            align-items: center;
            text-align: center;
            background: {self.config.primary_color};
        }}

        .slide.layout-cta .slide-title {{
            color: white;
            font-size: 56px;
        }}

        .slide.layout-cta .cta-button {{
            display: inline-block;
            padding: 20px 60px;
            background: white;
            color: {self.config.primary_color};
            font-size: 24px;
            font-weight: 600;
            border-radius: 8px;
            text-decoration: none;
            margin-top: 40px;
        }}

        /* Team layout */
        .slide.layout-team .team-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 40px;
            flex: 1;
            align-content: center;
        }}

        .team-member {{
            text-align: center;
        }}

        .team-member img {{
            width: 120px;
            height: 120px;
            border-radius: 60px;
            object-fit: cover;
            margin-bottom: 16px;
        }}

        .team-member .member-name {{
            font-size: 22px;
            font-weight: 600;
            color: {self.config.text_color};
        }}

        .team-member .member-role {{
            font-size: 18px;
            color: {self.config.secondary_color};
        }}

        /* Pricing layout */
        .slide.layout-pricing .pricing-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 30px;
            flex: 1;
            align-content: center;
        }}

        .pricing-tier {{
            padding: 30px;
            border: 2px solid #e5e7eb;
            border-radius: 12px;
            text-align: center;
        }}

        .pricing-tier.highlighted {{
            border-color: {self.config.primary_color};
            transform: scale(1.05);
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}

        .pricing-tier .tier-name {{
            font-size: 24px;
            font-weight: 600;
            color: {self.config.text_color};
        }}

        .pricing-tier .tier-price {{
            font-size: 42px;
            font-weight: 700;
            color: {self.config.primary_color};
            margin: 16px 0;
        }}

        .pricing-tier .tier-features {{
            text-align: left;
            list-style: none;
            padding: 0;
            margin: 20px 0;
        }}

        .pricing-tier .tier-features li {{
            padding: 8px 0;
            font-size: 16px;
        }}

        .pricing-tier .tier-features li::before {{
            content: "✓ ";
            color: {self.config.accent_color};
        }}

        /* Timeline layout */
        .slide.layout-timeline .timeline {{
            display: flex;
            flex-direction: column;
            gap: 30px;
            flex: 1;
            justify-content: center;
        }}

        .timeline-item {{
            display: flex;
            gap: 30px;
            align-items: flex-start;
        }}

        .timeline-item .timeline-date {{
            min-width: 150px;
            font-size: 18px;
            font-weight: 600;
            color: {self.config.primary_color};
        }}

        .timeline-item .timeline-content {{
            flex: 1;
            padding-left: 30px;
            border-left: 3px solid {self.config.accent_color};
        }}

        .timeline-item .timeline-title {{
            font-size: 22px;
            font-weight: 600;
            margin-bottom: 8px;
        }}

        .timeline-item .timeline-description {{
            font-size: 18px;
            color: #6b7280;
        }}

        /* Comparison layout */
        .slide.layout-comparison .comparison-table {{
            width: 100%;
            border-collapse: collapse;
            flex: 1;
        }}

        .comparison-table th,
        .comparison-table td {{
            padding: 20px;
            text-align: center;
            border-bottom: 1px solid #e5e7eb;
            font-size: 18px;
        }}

        .comparison-table th {{
            background: {self.config.light_color};
            font-weight: 600;
        }}

        .comparison-table th.highlighted {{
            background: {self.config.primary_color};
            color: white;
        }}

        .comparison-table td.highlighted {{
            background: rgba(30, 64, 175, 0.05);
        }}
        """

    def get_web_viewer_styles(self) -> str:
        """Generate CSS styles for web deck viewer."""
        base_styles = self.get_slide_styles()
        viewer_styles = f"""
        /* Web viewer specific styles */
        .deck-viewer {{
            width: 100vw;
            height: 100vh;
            background: #1a1a1a;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}

        .deck-container {{
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}

        .slide-wrapper {{
            background: white;
            box-shadow: 0 25px 100px rgba(0,0,0,0.5);
            transform-origin: center;
        }}

        .deck-controls {{
            display: flex;
            justify-content: center;
            gap: 20px;
            padding: 20px;
            background: rgba(0,0,0,0.8);
        }}

        .deck-controls button {{
            padding: 12px 24px;
            background: {self.config.primary_color};
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            transition: background 0.2s;
        }}

        .deck-controls button:hover {{
            background: {self.config.secondary_color};
        }}

        .deck-controls button:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}

        .slide-counter {{
            color: white;
            font-size: 18px;
            display: flex;
            align-items: center;
        }}

        .progress-bar {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: rgba(255,255,255,0.2);
        }}

        .progress-bar .progress {{
            height: 100%;
            background: {self.config.accent_color};
            transition: width 0.3s;
        }}

        /* Fullscreen mode */
        .deck-viewer.fullscreen {{
            position: fixed;
            inset: 0;
            z-index: 9999;
        }}

        /* Presenter mode */
        .presenter-view {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
            padding: 20px;
            height: 100vh;
            background: #1a1a1a;
        }}

        .presenter-current-slide {{
            background: white;
        }}

        .presenter-sidebar {{
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}

        .presenter-next-slide {{
            flex: 1;
            background: white;
            opacity: 0.7;
        }}

        .presenter-notes {{
            background: #2d2d2d;
            color: white;
            padding: 20px;
            border-radius: 8px;
            font-size: 18px;
            line-height: 1.6;
            overflow-y: auto;
            max-height: 300px;
        }}

        .presenter-timer {{
            background: #2d2d2d;
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}

        .presenter-timer .time {{
            font-size: 48px;
            font-weight: bold;
            font-family: monospace;
        }}

        /* Transitions */
        .slide-transition-fade {{
            animation: fadeIn 0.3s ease-in-out;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}

        .slide-transition-slide {{
            animation: slideIn 0.3s ease-in-out;
        }}

        @keyframes slideIn {{
            from {{ transform: translateX(100%); }}
            to {{ transform: translateX(0); }}
        }}
        """
        return base_styles + viewer_styles
