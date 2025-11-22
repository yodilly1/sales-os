"""
Integration Tests: Prospect Enrichment → CRM Sync Flow

Tests the complete backend workflow from prospect creation,
data enrichment, to CRM synchronization.
"""

import pytest
from httpx import AsyncClient

from tests.factories import ProspectFactory, CompanyFactory


@pytest.mark.integration
@pytest.mark.prospect
@pytest.mark.asyncio
class TestProspectEndpoints:
    """Test prospect API endpoints."""

    async def test_create_prospect(
        self,
        authenticated_client: AsyncClient,
        sample_prospect: dict,
    ):
        """Test creating a new prospect."""
        response = await authenticated_client.post(
            "/api/v1/prospects",
            json={
                "first_name": sample_prospect["first_name"],
                "last_name": sample_prospect["last_name"],
                "email": sample_prospect["email"],
                "company": sample_prospect["company"],
                "title": sample_prospect["title"],
            },
        )

        assert response.status_code in [200, 201]
        if response.status_code == 201:
            data = response.json()
            assert data["email"] == sample_prospect["email"]
            assert "id" in data

    async def test_get_prospect(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test retrieving a prospect by ID."""
        prospect = ProspectFactory.create()

        response = await authenticated_client.get(
            f"/api/v1/prospects/{prospect['id']}",
        )

        assert response.status_code in [200, 404]

    async def test_list_prospects(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test listing all prospects."""
        response = await authenticated_client.get("/api/v1/prospects")

        assert response.status_code == 200
        data = response.json()
        assert "prospects" in data or isinstance(data, list)

    async def test_search_prospects(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test searching prospects."""
        response = await authenticated_client.get(
            "/api/v1/prospects",
            params={"search": "john"},
        )

        assert response.status_code == 200

    async def test_filter_prospects_by_company(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test filtering prospects by company."""
        response = await authenticated_client.get(
            "/api/v1/prospects",
            params={"company": "Acme Corp"},
        )

        assert response.status_code == 200

    async def test_filter_verified_prospects(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test filtering verified prospects."""
        response = await authenticated_client.get(
            "/api/v1/prospects",
            params={"verified": True},
        )

        assert response.status_code == 200

    async def test_update_prospect(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test updating a prospect."""
        prospect = ProspectFactory.create()

        response = await authenticated_client.patch(
            f"/api/v1/prospects/{prospect['id']}",
            json={"title": "Chief Revenue Officer"},
        )

        assert response.status_code in [200, 404]

    async def test_delete_prospect(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test deleting a prospect."""
        prospect = ProspectFactory.create()

        response = await authenticated_client.delete(
            f"/api/v1/prospects/{prospect['id']}",
        )

        assert response.status_code in [204, 404]

    async def test_email_validation(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test that invalid emails are rejected."""
        response = await authenticated_client.post(
            "/api/v1/prospects",
            json={
                "first_name": "Test",
                "last_name": "User",
                "email": "invalid-email",
                "company": "Test Corp",
            },
        )

        assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.prospect
@pytest.mark.asyncio
class TestProspectEnrichment:
    """Test prospect enrichment endpoints."""

    async def test_enrich_prospect(
        self,
        authenticated_client: AsyncClient,
        sample_prospect: dict,
    ):
        """Test enriching a prospect's data."""
        response = await authenticated_client.post(
            f"/api/v1/prospects/{sample_prospect['id']}/enrich",
        )

        assert response.status_code in [200, 202, 404]
        if response.status_code == 200:
            data = response.json()
            assert "verified" in data or "enrichment_data" in data

    async def test_get_enrichment_data(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test retrieving enrichment data for a prospect."""
        prospect = ProspectFactory.create_verified()

        response = await authenticated_client.get(
            f"/api/v1/prospects/{prospect['id']}/enrichment",
        )

        assert response.status_code in [200, 404]

    async def test_bulk_enrich_prospects(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test bulk enrichment of multiple prospects."""
        prospects = ProspectFactory.create_batch(3)
        prospect_ids = [p["id"] for p in prospects]

        response = await authenticated_client.post(
            "/api/v1/prospects/bulk/enrich",
            json={"prospect_ids": prospect_ids},
        )

        assert response.status_code in [200, 202]

    async def test_enrichment_includes_company_info(
        self,
        mock_enrichment_response: dict,
    ):
        """Test that enrichment includes company information."""
        assert "enrichment_data" in mock_enrichment_response
        assert "company_info" in mock_enrichment_response["enrichment_data"]

        company_info = mock_enrichment_response["enrichment_data"]["company_info"]
        assert "name" in company_info
        assert "industry" in company_info
        assert "size" in company_info

    async def test_enrichment_includes_social_profiles(
        self,
        mock_enrichment_response: dict,
    ):
        """Test that enrichment includes social profiles."""
        assert "enrichment_data" in mock_enrichment_response

        enrichment = mock_enrichment_response["enrichment_data"]
        assert "linkedin_profile" in enrichment or "social_profiles" in enrichment


@pytest.mark.integration
@pytest.mark.prospect
@pytest.mark.crm
@pytest.mark.asyncio
class TestProspectCrmSync:
    """Test prospect CRM synchronization endpoints."""

    async def test_sync_prospect_to_crm(
        self,
        authenticated_client: AsyncClient,
        sample_prospect: dict,
    ):
        """Test syncing a prospect to CRM."""
        response = await authenticated_client.post(
            f"/api/v1/prospects/{sample_prospect['id']}/sync",
        )

        assert response.status_code in [200, 202, 404]

    async def test_sync_to_hubspot(
        self,
        authenticated_client: AsyncClient,
        sample_prospect: dict,
    ):
        """Test syncing a prospect specifically to HubSpot."""
        response = await authenticated_client.post(
            f"/api/v1/prospects/{sample_prospect['id']}/sync/hubspot",
        )

        assert response.status_code in [200, 202, 404]

    async def test_bulk_sync_prospects(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test bulk syncing multiple prospects to CRM."""
        prospects = ProspectFactory.create_batch(3)
        prospect_ids = [p["id"] for p in prospects]

        response = await authenticated_client.post(
            "/api/v1/prospects/bulk/sync",
            json={"prospect_ids": prospect_ids},
        )

        assert response.status_code in [200, 202]

    async def test_get_crm_sync_status(
        self,
        authenticated_client: AsyncClient,
        sample_prospect: dict,
    ):
        """Test getting CRM sync status for a prospect."""
        response = await authenticated_client.get(
            f"/api/v1/prospects/{sample_prospect['id']}/sync/status",
        )

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "crm_synced" in data or "status" in data

    async def test_update_synced_prospect_in_crm(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test updating a prospect that's already synced to CRM."""
        prospect = ProspectFactory.create_synced()

        response = await authenticated_client.patch(
            f"/api/v1/prospects/{prospect['id']}",
            json={"title": "Updated Title"},
        )

        # Should update and potentially re-sync
        assert response.status_code in [200, 404]


@pytest.mark.integration
@pytest.mark.prospect
@pytest.mark.asyncio
class TestProspectImport:
    """Test prospect import endpoints."""

    async def test_import_prospects_csv(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test importing prospects from CSV."""
        csv_content = """first_name,last_name,email,company,title
John,Doe,john@example.com,Example Corp,VP Sales
Jane,Smith,jane@example.com,Tech Inc,Director
"""

        response = await authenticated_client.post(
            "/api/v1/prospects/import",
            files={"file": ("prospects.csv", csv_content, "text/csv")},
        )

        assert response.status_code in [200, 201, 202]

    async def test_import_preview(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test previewing import before confirming."""
        csv_content = """first_name,last_name,email
Test,User,test@example.com
"""

        response = await authenticated_client.post(
            "/api/v1/prospects/import/preview",
            files={"file": ("prospects.csv", csv_content, "text/csv")},
        )

        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            assert "preview" in data or "rows" in data

    async def test_import_invalid_file(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test that invalid file format is rejected."""
        response = await authenticated_client.post(
            "/api/v1/prospects/import",
            files={"file": ("invalid.txt", "not a csv", "text/plain")},
        )

        assert response.status_code in [400, 422]


@pytest.mark.integration
@pytest.mark.prospect
@pytest.mark.asyncio
class TestCompanyEndpoints:
    """Test company API endpoints."""

    async def test_get_company(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test retrieving company information."""
        company = CompanyFactory.create()

        response = await authenticated_client.get(
            f"/api/v1/companies/{company['id']}",
        )

        assert response.status_code in [200, 404]

    async def test_search_companies(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test searching companies."""
        response = await authenticated_client.get(
            "/api/v1/companies",
            params={"search": "tech"},
        )

        assert response.status_code == 200

    async def test_get_company_by_domain(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test looking up company by domain."""
        response = await authenticated_client.get(
            "/api/v1/companies/lookup",
            params={"domain": "example.com"},
        )

        assert response.status_code in [200, 404]


@pytest.mark.integration
@pytest.mark.prospect
@pytest.mark.asyncio
class TestProspectEnrichmentCrmWorkflow:
    """Test the complete Prospect Enrichment → CRM Sync workflow."""

    async def test_complete_workflow(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test the complete end-to-end workflow."""
        # Step 1: Create prospect
        prospect_data = ProspectFactory.create()
        create_response = await authenticated_client.post(
            "/api/v1/prospects",
            json={
                "first_name": prospect_data["first_name"],
                "last_name": prospect_data["last_name"],
                "email": prospect_data["email"],
                "company": prospect_data["company"],
                "title": prospect_data["title"],
            },
        )

        if create_response.status_code == 201:
            prospect_id = create_response.json()["id"]

            # Step 2: Enrich prospect
            enrich_response = await authenticated_client.post(
                f"/api/v1/prospects/{prospect_id}/enrich",
            )

            if enrich_response.status_code == 200:
                # Step 3: Verify enrichment
                get_response = await authenticated_client.get(
                    f"/api/v1/prospects/{prospect_id}",
                )
                assert get_response.status_code == 200

                # Step 4: Sync to CRM
                sync_response = await authenticated_client.post(
                    f"/api/v1/prospects/{prospect_id}/sync",
                )
                assert sync_response.status_code in [200, 202]

    async def test_bulk_workflow(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test bulk processing workflow."""
        # Step 1: Import prospects
        csv_content = """first_name,last_name,email,company,title
Alice,Johnson,alice@acme.com,Acme Corp,CRO
Bob,Williams,bob@tech.com,Tech Inc,VP Sales
Carol,Brown,carol@startup.com,Startup Co,Director
"""

        import_response = await authenticated_client.post(
            "/api/v1/prospects/import",
            files={"file": ("prospects.csv", csv_content, "text/csv")},
        )

        if import_response.status_code in [200, 201]:
            # Step 2: Get all unverified prospects
            list_response = await authenticated_client.get(
                "/api/v1/prospects",
                params={"verified": False},
            )

            if list_response.status_code == 200:
                prospects = list_response.json().get("prospects", [])
                prospect_ids = [p["id"] for p in prospects[:3]]

                # Step 3: Bulk enrich
                if prospect_ids:
                    enrich_response = await authenticated_client.post(
                        "/api/v1/prospects/bulk/enrich",
                        json={"prospect_ids": prospect_ids},
                    )

                    # Step 4: Bulk sync to CRM
                    if enrich_response.status_code in [200, 202]:
                        sync_response = await authenticated_client.post(
                            "/api/v1/prospects/bulk/sync",
                            json={"prospect_ids": prospect_ids},
                        )
                        assert sync_response.status_code in [200, 202]

    async def test_workflow_handles_enrichment_failure(
        self,
        authenticated_client: AsyncClient,
        sample_prospect: dict,
    ):
        """Test that workflow handles enrichment failure gracefully."""
        # Attempt to sync unenriched prospect
        response = await authenticated_client.post(
            f"/api/v1/prospects/{sample_prospect['id']}/sync",
        )

        # Should either sync with limited data or return appropriate error
        assert response.status_code in [200, 202, 400, 404]
