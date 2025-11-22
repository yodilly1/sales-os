"""
Content and Content Template Factories

Provides factory classes for creating content generation test data.
"""

from datetime import datetime, timezone
from typing import Any

import factory
from faker import Faker

fake = Faker()


class ContentFactory(factory.Factory):
    """Factory for creating Content test data."""

    class Meta:
        model = dict

    id = factory.LazyFunction(lambda: f"content-{fake.uuid4()[:8]}")
    type = factory.LazyFunction(lambda: fake.random_element(["proposal", "deck", "one-pager"]))
    title = factory.LazyFunction(lambda: f"{fake.random_element(['Sales Proposal', 'Product Deck', 'Executive Summary'])} - {fake.company()}")
    goal = factory.LazyFunction(lambda: fake.sentence(nb_words=10))
    product_info = factory.LazyFunction(lambda: fake.paragraph(nb_sentences=3))
    audience = factory.LazyFunction(lambda: fake.random_element(["C-level executives", "Sales team", "Technical buyers", "End users"]))
    tone = factory.LazyFunction(lambda: fake.random_element(["professional", "casual", "technical", "persuasive"]))
    generated_content = factory.LazyFunction(lambda: _generate_content_html())
    format = factory.LazyFunction(lambda: fake.random_element(["html", "pdf", "pptx"]))
    status = "completed"
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc).isoformat())
    user_id = factory.LazyFunction(lambda: f"user-{fake.uuid4()[:8]}")

    @classmethod
    def create_proposal(cls, **kwargs) -> dict[str, Any]:
        """Create a proposal-type content."""
        return cls.create(type="proposal", **kwargs)

    @classmethod
    def create_deck(cls, **kwargs) -> dict[str, Any]:
        """Create a deck-type content."""
        return cls.create(type="deck", **kwargs)

    @classmethod
    def create_one_pager(cls, **kwargs) -> dict[str, Any]:
        """Create a one-pager-type content."""
        return cls.create(type="one-pager", **kwargs)


class ContentTemplateFactory(factory.Factory):
    """Factory for creating Content Template test data."""

    class Meta:
        model = dict

    id = factory.LazyFunction(lambda: f"template-{fake.uuid4()[:8]}")
    name = factory.LazyFunction(lambda: fake.random_element([
        "Enterprise Proposal",
        "SMB Proposal",
        "Product Overview Deck",
        "Technical Deep Dive",
        "Executive One-Pager",
    ]))
    type = factory.LazyFunction(lambda: fake.random_element(["proposal", "deck", "one-pager"]))
    description = factory.LazyFunction(lambda: fake.paragraph(nb_sentences=2))
    template_content = factory.LazyFunction(lambda: _generate_template_structure())
    brand_colors = factory.LazyFunction(lambda: {
        "primary": fake.hex_color(),
        "secondary": fake.hex_color(),
        "accent": fake.hex_color(),
    })
    is_default = False
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc).isoformat())


def _generate_content_html() -> str:
    """Generate realistic HTML content."""
    company = fake.company()
    product = fake.catch_phrase()

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Sales Proposal - {company}</title>
    <style>
        body {{ font-family: 'Arial', sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background: #2563eb; color: white; padding: 40px; text-align: center; }}
        .section {{ padding: 30px; margin: 20px 0; }}
        h1 {{ margin: 0; }}
        h2 {{ color: #2563eb; border-bottom: 2px solid #2563eb; padding-bottom: 10px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Sales Proposal</h1>
        <p>Prepared for {company}</p>
    </div>

    <div class="section">
        <h2>Executive Summary</h2>
        <p>{fake.paragraph(nb_sentences=4)}</p>
        <p>Our solution, {product}, addresses your key challenges and delivers measurable ROI.</p>
    </div>

    <div class="section">
        <h2>Understanding Your Challenges</h2>
        <ul>
            <li>{fake.sentence()}</li>
            <li>{fake.sentence()}</li>
            <li>{fake.sentence()}</li>
        </ul>
    </div>

    <div class="section">
        <h2>Our Solution</h2>
        <p>{fake.paragraph(nb_sentences=3)}</p>
        <h3>Key Benefits</h3>
        <ul>
            <li><strong>Increased Efficiency:</strong> {fake.sentence()}</li>
            <li><strong>Better Insights:</strong> {fake.sentence()}</li>
            <li><strong>Scalable Growth:</strong> {fake.sentence()}</li>
        </ul>
    </div>

    <div class="section">
        <h2>Investment & ROI</h2>
        <p>{fake.paragraph(nb_sentences=2)}</p>
        <p><strong>Estimated ROI:</strong> {fake.random_int(min=200, max=500)}% in the first year</p>
    </div>

    <div class="section">
        <h2>Next Steps</h2>
        <ol>
            <li>Schedule a technical deep-dive session</li>
            <li>Complete proof of concept</li>
            <li>Finalize contract and implementation timeline</li>
        </ol>
    </div>
</body>
</html>
"""


def _generate_template_structure() -> dict[str, Any]:
    """Generate a template structure."""
    return {
        "sections": [
            {
                "id": "header",
                "type": "header",
                "fields": ["title", "subtitle", "date", "logo"],
            },
            {
                "id": "executive-summary",
                "type": "text",
                "title": "Executive Summary",
                "placeholder": "Enter executive summary...",
            },
            {
                "id": "challenges",
                "type": "bullet-list",
                "title": "Understanding Your Challenges",
                "min_items": 3,
                "max_items": 5,
            },
            {
                "id": "solution",
                "type": "text",
                "title": "Our Solution",
                "placeholder": "Describe the solution...",
            },
            {
                "id": "benefits",
                "type": "key-value-list",
                "title": "Key Benefits",
                "min_items": 3,
            },
            {
                "id": "investment",
                "type": "pricing-table",
                "title": "Investment & ROI",
            },
            {
                "id": "next-steps",
                "type": "numbered-list",
                "title": "Next Steps",
            },
        ],
        "styles": {
            "font_family": "Arial, sans-serif",
            "heading_font": "Arial, sans-serif",
            "base_font_size": "14px",
        },
    }
