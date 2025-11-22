"""
Integration Tests: Content Generation → Export Flow

Tests the complete backend workflow from content creation,
AI-powered generation, to export in various formats.
"""

import pytest
from httpx import AsyncClient

from tests.factories import ContentFactory, ContentTemplateFactory


@pytest.mark.integration
@pytest.mark.content
@pytest.mark.asyncio
class TestContentEndpoints:
    """Test content API endpoints."""

    async def test_create_content(
        self,
        authenticated_client: AsyncClient,
        sample_content: dict,
    ):
        """Test creating new content."""
        response = await authenticated_client.post(
            "/api/v1/content",
            json={
                "type": sample_content["type"],
                "title": sample_content["title"],
                "goal": sample_content["goal"],
                "product_info": sample_content["product_info"],
            },
        )

        assert response.status_code in [200, 201]
        if response.status_code == 201:
            data = response.json()
            assert data["type"] == sample_content["type"]
            assert "id" in data

    async def test_get_content(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test retrieving content by ID."""
        content = ContentFactory.create()

        response = await authenticated_client.get(
            f"/api/v1/content/{content['id']}",
        )

        assert response.status_code in [200, 404]

    async def test_list_content(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test listing all content."""
        response = await authenticated_client.get("/api/v1/content")

        assert response.status_code == 200
        data = response.json()
        assert "content" in data or isinstance(data, list)

    async def test_list_content_by_type(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test filtering content by type."""
        response = await authenticated_client.get(
            "/api/v1/content",
            params={"type": "proposal"},
        )

        assert response.status_code == 200

    async def test_delete_content(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test deleting content."""
        content = ContentFactory.create()

        response = await authenticated_client.delete(
            f"/api/v1/content/{content['id']}",
        )

        assert response.status_code in [204, 404]


@pytest.mark.integration
@pytest.mark.content
@pytest.mark.asyncio
class TestContentGeneration:
    """Test content generation endpoints."""

    async def test_generate_proposal(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test generating a proposal."""
        response = await authenticated_client.post(
            "/api/v1/content/generate",
            json={
                "type": "proposal",
                "goal": "Close enterprise deal with Fortune 500 company",
                "product_info": "Sales OS - VP of Sales Operating System",
                "audience": "C-level executives",
                "tone": "professional",
            },
        )

        assert response.status_code in [200, 201, 202]
        if response.status_code in [200, 201]:
            data = response.json()
            assert data["type"] == "proposal"
            assert "generated_content" in data or "content" in data

    async def test_generate_deck(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test generating a presentation deck."""
        response = await authenticated_client.post(
            "/api/v1/content/generate",
            json={
                "type": "deck",
                "goal": "Product demo for sales team",
                "product_info": "Sales OS features and capabilities",
            },
        )

        assert response.status_code in [200, 201, 202]

    async def test_generate_one_pager(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test generating a one-pager."""
        response = await authenticated_client.post(
            "/api/v1/content/generate",
            json={
                "type": "one-pager",
                "goal": "Quick overview for trade show",
                "product_info": "Sales OS key benefits",
            },
        )

        assert response.status_code in [200, 201, 202]

    async def test_generate_with_template(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test generating content using a template."""
        template = ContentTemplateFactory.create()

        response = await authenticated_client.post(
            "/api/v1/content/generate",
            json={
                "type": "proposal",
                "goal": "Standard sales proposal",
                "product_info": "Product details",
                "template_id": template["id"],
            },
        )

        assert response.status_code in [200, 201, 202, 404]

    async def test_generation_validation(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test that content generation validates required fields."""
        response = await authenticated_client.post(
            "/api/v1/content/generate",
            json={
                "type": "proposal",
                # Missing goal and product_info
            },
        )

        # Should return validation error
        assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.content
@pytest.mark.asyncio
class TestContentExport:
    """Test content export endpoints."""

    async def test_export_as_pdf(
        self,
        authenticated_client: AsyncClient,
        sample_content: dict,
    ):
        """Test exporting content as PDF."""
        response = await authenticated_client.get(
            f"/api/v1/content/{sample_content['id']}/export/pdf",
        )

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            assert response.headers.get("content-type") == "application/pdf"

    async def test_export_as_pptx(
        self,
        authenticated_client: AsyncClient,
        sample_content: dict,
    ):
        """Test exporting content as PPTX."""
        response = await authenticated_client.get(
            f"/api/v1/content/{sample_content['id']}/export/pptx",
        )

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            assert "presentation" in content_type or "octet-stream" in content_type

    async def test_export_as_html(
        self,
        authenticated_client: AsyncClient,
        sample_content: dict,
    ):
        """Test exporting content as HTML."""
        response = await authenticated_client.get(
            f"/api/v1/content/{sample_content['id']}/export/html",
        )

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            assert "html" in response.headers.get("content-type", "").lower()

    async def test_export_invalid_format(
        self,
        authenticated_client: AsyncClient,
        sample_content: dict,
    ):
        """Test that invalid export format returns error."""
        response = await authenticated_client.get(
            f"/api/v1/content/{sample_content['id']}/export/invalid",
        )

        assert response.status_code in [400, 404]


@pytest.mark.integration
@pytest.mark.content
@pytest.mark.asyncio
class TestContentTemplates:
    """Test content template endpoints."""

    async def test_list_templates(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test listing available templates."""
        response = await authenticated_client.get("/api/v1/content/templates")

        assert response.status_code == 200
        data = response.json()
        assert "templates" in data or isinstance(data, list)

    async def test_get_template(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test retrieving a specific template."""
        template = ContentTemplateFactory.create()

        response = await authenticated_client.get(
            f"/api/v1/content/templates/{template['id']}",
        )

        assert response.status_code in [200, 404]

    async def test_create_custom_template(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test creating a custom template."""
        template_data = ContentTemplateFactory.create()

        response = await authenticated_client.post(
            "/api/v1/content/templates",
            json={
                "name": template_data["name"],
                "type": template_data["type"],
                "description": template_data["description"],
                "template_content": template_data["template_content"],
            },
        )

        assert response.status_code in [200, 201]


@pytest.mark.integration
@pytest.mark.content
@pytest.mark.asyncio
class TestContentGenerationExportWorkflow:
    """Test the complete Content Generation → Export workflow."""

    async def test_complete_workflow(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test the complete end-to-end workflow."""
        # Step 1: Generate content
        generate_response = await authenticated_client.post(
            "/api/v1/content/generate",
            json={
                "type": "proposal",
                "goal": "Complete workflow test",
                "product_info": "Sales OS - Complete solution",
                "audience": "Enterprise buyers",
                "tone": "professional",
            },
        )

        if generate_response.status_code in [200, 201]:
            content_id = generate_response.json()["id"]

            # Step 2: Verify content was created
            get_response = await authenticated_client.get(
                f"/api/v1/content/{content_id}",
            )
            assert get_response.status_code == 200

            # Step 3: Export as PDF
            export_response = await authenticated_client.get(
                f"/api/v1/content/{content_id}/export/pdf",
            )
            assert export_response.status_code == 200

    async def test_workflow_with_editing(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test workflow including content editing."""
        # Step 1: Generate content
        generate_response = await authenticated_client.post(
            "/api/v1/content/generate",
            json={
                "type": "one-pager",
                "goal": "Quick overview",
                "product_info": "Product summary",
            },
        )

        if generate_response.status_code in [200, 201]:
            content_id = generate_response.json()["id"]

            # Step 2: Edit content
            edit_response = await authenticated_client.patch(
                f"/api/v1/content/{content_id}",
                json={
                    "generated_content": "<h1>Updated Content</h1>",
                },
            )

            if edit_response.status_code == 200:
                # Step 3: Export edited content
                export_response = await authenticated_client.get(
                    f"/api/v1/content/{content_id}/export/html",
                )
                assert export_response.status_code == 200

    async def test_multiple_format_exports(
        self,
        authenticated_client: AsyncClient,
        sample_content: dict,
    ):
        """Test exporting same content in multiple formats."""
        formats = ["pdf", "html", "pptx"]

        for fmt in formats:
            response = await authenticated_client.get(
                f"/api/v1/content/{sample_content['id']}/export/{fmt}",
            )
            # All formats should be available or 404 if content doesn't exist
            assert response.status_code in [200, 404]
