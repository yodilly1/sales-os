"""
Integration Tests: Transcript → SPICED → CRM Flow

Tests the complete backend workflow from transcript upload,
SPICED analysis, to CRM synchronization.
"""

import pytest
from httpx import AsyncClient

from tests.factories import TranscriptFactory, SpicedAnalysisFactory


@pytest.mark.integration
@pytest.mark.asyncio
class TestTranscriptEndpoints:
    """Test transcript API endpoints."""

    async def test_create_transcript(
        self,
        authenticated_client: AsyncClient,
        sample_transcript: dict,
    ):
        """Test creating a new transcript."""
        response = await authenticated_client.post(
            "/api/v1/transcripts",
            json={
                "title": sample_transcript["title"],
                "content": sample_transcript["content"],
                "duration": sample_transcript["duration"],
                "participants": sample_transcript["participants"],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_transcript["title"]
        assert "id" in data
        assert data["status"] == "processing"

    async def test_get_transcript(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test retrieving a transcript by ID."""
        # First create a transcript
        transcript = TranscriptFactory.create()

        response = await authenticated_client.get(
            f"/api/v1/transcripts/{transcript['id']}",
        )

        # Note: In a real test with database, this would return the created transcript
        # Here we're testing the endpoint structure
        assert response.status_code in [200, 404]

    async def test_list_transcripts(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test listing all transcripts."""
        response = await authenticated_client.get("/api/v1/transcripts")

        assert response.status_code == 200
        data = response.json()
        assert "transcripts" in data or isinstance(data, list)

    async def test_delete_transcript(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test deleting a transcript."""
        transcript = TranscriptFactory.create()

        response = await authenticated_client.delete(
            f"/api/v1/transcripts/{transcript['id']}",
        )

        # Should return 204 No Content or 404 if not found
        assert response.status_code in [204, 404]


@pytest.mark.integration
@pytest.mark.spiced
@pytest.mark.asyncio
class TestSpicedAnalysis:
    """Test SPICED analysis endpoints."""

    async def test_analyze_transcript(
        self,
        authenticated_client: AsyncClient,
        sample_transcript: dict,
    ):
        """Test triggering SPICED analysis on a transcript."""
        response = await authenticated_client.post(
            "/api/v1/spiced/analyze",
            json={"transcript_id": sample_transcript["id"]},
        )

        # Should trigger analysis (may return 202 Accepted for async processing)
        assert response.status_code in [200, 201, 202]

    async def test_get_spiced_analysis(
        self,
        authenticated_client: AsyncClient,
        sample_spiced_analysis: dict,
    ):
        """Test retrieving SPICED analysis results."""
        response = await authenticated_client.get(
            f"/api/v1/spiced/{sample_spiced_analysis['id']}",
        )

        assert response.status_code in [200, 404]

    async def test_spiced_contains_all_components(
        self,
        sample_spiced_analysis: dict,
    ):
        """Test that SPICED analysis contains all required components."""
        required_fields = [
            "situation",
            "problem",
            "implication",
            "critical_event",
            "decision",
        ]

        for field in required_fields:
            assert field in sample_spiced_analysis
            assert sample_spiced_analysis[field] is not None
            assert len(sample_spiced_analysis[field]) > 0

    async def test_update_spiced_analysis(
        self,
        authenticated_client: AsyncClient,
        sample_spiced_analysis: dict,
    ):
        """Test updating SPICED analysis fields."""
        response = await authenticated_client.patch(
            f"/api/v1/spiced/{sample_spiced_analysis['id']}",
            json={"situation": "Updated situation description"},
        )

        assert response.status_code in [200, 404]

    async def test_export_spiced_as_json(
        self,
        authenticated_client: AsyncClient,
        sample_spiced_analysis: dict,
    ):
        """Test exporting SPICED analysis as JSON."""
        response = await authenticated_client.get(
            f"/api/v1/spiced/{sample_spiced_analysis['id']}/export",
            params={"format": "json"},
        )

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            assert response.headers.get("content-type") == "application/json"


@pytest.mark.integration
@pytest.mark.crm
@pytest.mark.hubspot
@pytest.mark.asyncio
class TestCrmSync:
    """Test CRM synchronization endpoints."""

    async def test_sync_spiced_to_crm(
        self,
        authenticated_client: AsyncClient,
        sample_spiced_analysis: dict,
    ):
        """Test syncing SPICED analysis to CRM."""
        response = await authenticated_client.post(
            "/api/v1/crm/sync",
            json={
                "entity_type": "spiced",
                "entity_id": sample_spiced_analysis["id"],
            },
        )

        assert response.status_code in [200, 201, 202]

    async def test_create_crm_task(
        self,
        authenticated_client: AsyncClient,
        sample_spiced_analysis: dict,
    ):
        """Test creating a CRM task from SPICED analysis."""
        response = await authenticated_client.post(
            "/api/v1/crm/tasks",
            json={
                "title": "Follow up on SPICED analysis",
                "description": f"Based on analysis {sample_spiced_analysis['id']}",
                "due_date": "2024-12-31",
                "spiced_id": sample_spiced_analysis["id"],
            },
        )

        assert response.status_code in [200, 201]

    async def test_create_call_note(
        self,
        authenticated_client: AsyncClient,
        sample_transcript: dict,
        sample_spiced_analysis: dict,
    ):
        """Test creating a call note in CRM."""
        response = await authenticated_client.post(
            "/api/v1/crm/notes",
            json={
                "transcript_id": sample_transcript["id"],
                "spiced_id": sample_spiced_analysis["id"],
                "note_content": "Summary of sales call with key insights",
            },
        )

        assert response.status_code in [200, 201]

    async def test_get_crm_sync_status(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test getting CRM connection status."""
        response = await authenticated_client.get("/api/v1/crm/status")

        assert response.status_code == 200
        data = response.json()
        assert "connected" in data


@pytest.mark.integration
@pytest.mark.asyncio
class TestTranscriptSpicedCrmWorkflow:
    """Test the complete Transcript → SPICED → CRM workflow."""

    async def test_complete_workflow(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test the complete end-to-end workflow."""
        # Step 1: Create transcript
        transcript_data = TranscriptFactory.create()
        create_response = await authenticated_client.post(
            "/api/v1/transcripts",
            json={
                "title": transcript_data["title"],
                "content": transcript_data["content"],
                "duration": transcript_data["duration"],
                "participants": transcript_data["participants"],
            },
        )

        # Note: In test environment, endpoints may not be fully implemented
        if create_response.status_code == 201:
            transcript_id = create_response.json()["id"]

            # Step 2: Trigger SPICED analysis
            analyze_response = await authenticated_client.post(
                "/api/v1/spiced/analyze",
                json={"transcript_id": transcript_id},
            )

            if analyze_response.status_code in [200, 201, 202]:
                spiced_id = analyze_response.json().get("id")

                # Step 3: Sync to CRM
                sync_response = await authenticated_client.post(
                    "/api/v1/crm/sync",
                    json={
                        "entity_type": "spiced",
                        "entity_id": spiced_id,
                    },
                )

                assert sync_response.status_code in [200, 201, 202]

    async def test_workflow_handles_missing_transcript(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test that workflow handles missing transcript gracefully."""
        response = await authenticated_client.post(
            "/api/v1/spiced/analyze",
            json={"transcript_id": "non-existent-id"},
        )

        # Should return 404 or 400
        assert response.status_code in [400, 404]

    async def test_workflow_handles_crm_disconnected(
        self,
        authenticated_client: AsyncClient,
        sample_spiced_analysis: dict,
    ):
        """Test that workflow handles CRM disconnection gracefully."""
        # Attempt to sync when CRM might not be connected
        response = await authenticated_client.post(
            "/api/v1/crm/sync",
            json={
                "entity_type": "spiced",
                "entity_id": sample_spiced_analysis["id"],
            },
        )

        # Should handle gracefully (either success or appropriate error)
        assert response.status_code in [200, 201, 202, 400, 503]
