"""
Salesforce API routes for Sales OS.

Provides REST endpoints for Salesforce CRM integration including:
- OAuth2 authentication flow
- Lead management
- Contact management
- Opportunity management
- Task management
- Activity logging
- Record search
- Bulk operations
"""

import logging
import secrets
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from backend.app.integrations.salesforce import (
    SalesforceClient,
    SalesforceFieldMapper,
    SalesforceOAuth2Handler,
    SalesforceTokenManager,
)
from backend.app.models.salesforce import (
    AddTaskRequest,
    BulkJobRequest,
    BulkJobResponse,
    BulkJobResult,
    ContactResponse,
    CreateContactRequest,
    CreateLeadRequest,
    FieldMappingConfig,
    LeadResponse,
    LogActivityRequest,
    ActivityResponse,
    OpportunityResponse,
    SalesforceAPIError,
    SalesforceAuthConfig,
    SalesforceCredentials,
    SalesforceEnvironment,
    SearchRecordsRequest,
    SearchRecordsResponse,
    TaskResponse,
    UpdateOpportunityRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/salesforce", tags=["salesforce"])


# ==================== Request/Response Models ====================


class OAuthInitRequest(BaseModel):
    """Request to initiate OAuth2 flow."""
    environment: SalesforceEnvironment = SalesforceEnvironment.PRODUCTION
    redirect_uri: Optional[str] = None


class OAuthInitResponse(BaseModel):
    """Response with OAuth2 authorization URL."""
    authorization_url: str
    state: str


class OAuthCallbackRequest(BaseModel):
    """Request for OAuth2 callback."""
    code: str
    state: str


class OAuthCallbackResponse(BaseModel):
    """Response after successful OAuth2 authentication."""
    success: bool
    instance_url: str
    org_id: Optional[str] = None


class ConnectionStatusResponse(BaseModel):
    """Response for connection status."""
    connected: bool
    instance_url: Optional[str] = None
    org_id: Optional[str] = None
    environment: Optional[SalesforceEnvironment] = None
    user_info: Optional[dict] = None


class DisconnectResponse(BaseModel):
    """Response for disconnect operation."""
    success: bool
    message: str


class BulkLeadsRequest(BaseModel):
    """Request for bulk lead creation."""
    leads: list[CreateLeadRequest]
    wait_for_completion: bool = True


class BulkContactsRequest(BaseModel):
    """Request for bulk contact creation."""
    contacts: list[CreateContactRequest]
    wait_for_completion: bool = True


class FieldMappingResponse(BaseModel):
    """Response with field mappings."""
    mappings: list[dict[str, Any]]


class SobjectDescribeResponse(BaseModel):
    """Response for object describe."""
    name: str
    label: str
    fields: list[dict[str, Any]]
    custom_fields: list[dict[str, Any]]


# ==================== Dependency Injection ====================


# In-memory storage for demo purposes
# In production, use secure storage (database, encrypted secrets manager)
_oauth_states: dict[str, dict[str, Any]] = {}
_credentials_store: dict[str, SalesforceCredentials] = {}
_config_store: dict[str, SalesforceAuthConfig] = {}


def get_salesforce_config() -> SalesforceAuthConfig:
    """
    Get Salesforce OAuth2 configuration.

    In production, load from environment variables or secure config.
    """
    import os

    return SalesforceAuthConfig(
        client_id=os.getenv("SALESFORCE_CLIENT_ID", ""),
        client_secret=os.getenv("SALESFORCE_CLIENT_SECRET", ""),
        redirect_uri=os.getenv(
            "SALESFORCE_REDIRECT_URI",
            "http://localhost:8000/api/salesforce/oauth/callback"
        ),
        environment=SalesforceEnvironment(
            os.getenv("SALESFORCE_ENVIRONMENT", "production")
        ),
    )


async def get_salesforce_client(
    user_id: str = "default",  # In production, get from auth
) -> SalesforceClient:
    """
    Get an authenticated Salesforce client.

    Args:
        user_id: User ID for credential lookup

    Returns:
        Authenticated SalesforceClient

    Raises:
        HTTPException: If not connected to Salesforce
    """
    credentials = _credentials_store.get(user_id)
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Not connected to Salesforce. Please authenticate first.",
        )

    config = _config_store.get(user_id) or get_salesforce_config()
    oauth_handler = SalesforceOAuth2Handler(config)
    token_manager = SalesforceTokenManager(oauth_handler, credentials)

    return SalesforceClient(token_manager)


# ==================== OAuth2 Endpoints ====================


@router.post("/oauth/init", response_model=OAuthInitResponse)
async def initiate_oauth(
    request: OAuthInitRequest,
    user_id: str = "default",
) -> OAuthInitResponse:
    """
    Initiate OAuth2 authorization flow.

    Returns an authorization URL to redirect the user to Salesforce login.
    """
    config = get_salesforce_config()

    # Override environment if specified
    if request.environment:
        config = SalesforceAuthConfig(
            client_id=config.client_id,
            client_secret=config.client_secret,
            redirect_uri=request.redirect_uri or config.redirect_uri,
            environment=request.environment,
        )

    _config_store[user_id] = config

    oauth_handler = SalesforceOAuth2Handler(config)

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = {"user_id": user_id, "config": config}

    auth_url = oauth_handler.get_authorization_url(state=state)

    return OAuthInitResponse(
        authorization_url=auth_url,
        state=state,
    )


@router.get("/oauth/callback")
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
) -> RedirectResponse:
    """
    Handle OAuth2 callback from Salesforce.

    Exchanges the authorization code for access tokens and stores credentials.
    """
    # Verify state
    state_data = _oauth_states.pop(state, None)
    if not state_data:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired state parameter",
        )

    user_id = state_data["user_id"]
    config = state_data["config"]

    oauth_handler = SalesforceOAuth2Handler(config)

    try:
        # Exchange code for tokens
        token_response = await oauth_handler.exchange_code_for_tokens(code)
        credentials = oauth_handler.create_credentials(token_response)

        # Store credentials
        _credentials_store[user_id] = credentials
        _config_store[user_id] = config

        logger.info(f"Successfully connected to Salesforce for user {user_id}")

        # Redirect to success page
        return RedirectResponse(
            url="/settings/integrations/salesforce?connected=true",
            status_code=302,
        )

    except SalesforceAPIError as e:
        logger.error(f"OAuth callback failed: {e.message}")
        return RedirectResponse(
            url=f"/settings/integrations/salesforce?error={e.message}",
            status_code=302,
        )
    finally:
        await oauth_handler.close()


@router.post("/oauth/callback", response_model=OAuthCallbackResponse)
async def oauth_callback_post(
    request: OAuthCallbackRequest,
    user_id: str = "default",
) -> OAuthCallbackResponse:
    """
    Handle OAuth2 callback via POST (for SPA flows).
    """
    state_data = _oauth_states.pop(request.state, None)
    if not state_data:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired state parameter",
        )

    config = state_data["config"]
    oauth_handler = SalesforceOAuth2Handler(config)

    try:
        token_response = await oauth_handler.exchange_code_for_tokens(request.code)
        credentials = oauth_handler.create_credentials(token_response)

        _credentials_store[user_id] = credentials
        _config_store[user_id] = config

        return OAuthCallbackResponse(
            success=True,
            instance_url=credentials.instance_url,
            org_id=credentials.org_id,
        )

    except SalesforceAPIError as e:
        raise HTTPException(status_code=400, detail=e.message)
    finally:
        await oauth_handler.close()


@router.get("/status", response_model=ConnectionStatusResponse)
async def get_connection_status(
    user_id: str = "default",
) -> ConnectionStatusResponse:
    """
    Get current Salesforce connection status.
    """
    credentials = _credentials_store.get(user_id)

    if not credentials:
        return ConnectionStatusResponse(connected=False)

    try:
        client = await get_salesforce_client(user_id)
        user_info = await client.get_current_user()
        await client.close()

        return ConnectionStatusResponse(
            connected=True,
            instance_url=credentials.instance_url,
            org_id=credentials.org_id,
            environment=credentials.environment,
            user_info=user_info,
        )

    except Exception as e:
        logger.warning(f"Failed to verify connection: {e}")
        return ConnectionStatusResponse(
            connected=True,  # Credentials exist but might be expired
            instance_url=credentials.instance_url,
            org_id=credentials.org_id,
            environment=credentials.environment,
        )


@router.post("/disconnect", response_model=DisconnectResponse)
async def disconnect_salesforce(
    user_id: str = "default",
) -> DisconnectResponse:
    """
    Disconnect from Salesforce and revoke tokens.
    """
    credentials = _credentials_store.pop(user_id, None)
    config = _config_store.pop(user_id, None)

    if not credentials or not config:
        return DisconnectResponse(
            success=True,
            message="Already disconnected",
        )

    try:
        oauth_handler = SalesforceOAuth2Handler(config)
        await oauth_handler.revoke_token(credentials.access_token)
        await oauth_handler.close()
    except Exception as e:
        logger.warning(f"Failed to revoke token: {e}")

    return DisconnectResponse(
        success=True,
        message="Successfully disconnected from Salesforce",
    )


# ==================== Lead Endpoints ====================


@router.post("/leads", response_model=LeadResponse)
async def create_lead(
    request: CreateLeadRequest,
    user_id: str = "default",
) -> LeadResponse:
    """
    Create a new lead in Salesforce.
    """
    client = await get_salesforce_client(user_id)
    try:
        return await client.create_lead(request)
    except SalesforceAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    finally:
        await client.close()


@router.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    user_id: str = "default",
) -> LeadResponse:
    """
    Get a lead by ID.
    """
    client = await get_salesforce_client(user_id)
    try:
        return await client.get_lead(lead_id)
    except SalesforceAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    finally:
        await client.close()


@router.patch("/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    updates: dict[str, Any],
    user_id: str = "default",
) -> LeadResponse:
    """
    Update a lead.
    """
    client = await get_salesforce_client(user_id)
    try:
        return await client.update_lead(lead_id, updates)
    except SalesforceAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    finally:
        await client.close()


@router.delete("/leads/{lead_id}")
async def delete_lead(
    lead_id: str,
    user_id: str = "default",
) -> dict[str, bool]:
    """
    Delete a lead.
    """
    client = await get_salesforce_client(user_id)
    try:
        await client.delete_lead(lead_id)
        return {"success": True}
    except SalesforceAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    finally:
        await client.close()


@router.post("/leads/bulk", response_model=BulkJobResult)
async def bulk_create_leads(
    request: BulkLeadsRequest,
    user_id: str = "default",
) -> BulkJobResult:
    """
    Bulk create leads using Salesforce Bulk API.
    """
    client = await get_salesforce_client(user_id)
    try:
        return await client.bulk_create_leads(
            request.leads,
            wait_for_completion=request.wait_for_completion,
        )
    except SalesforceAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    finally:
        await client.close()


# ==================== Contact Endpoints ====================


@router.post("/contacts", response_model=ContactResponse)
async def create_contact(
    request: CreateContactRequest,
    user_id: str = "default",
) -> ContactResponse:
    """
    Create a new contact in Salesforce.
    """
    client = await get_salesforce_client(user_id)
    try:
        return await client.create_contact(request)
    except SalesforceAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    finally:
        await client.close()


@router.get("/contacts/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: str,
    user_id: str = "default",
) -> ContactResponse:
    """
    Get a contact by ID.
    """
    client = await get_salesforce_client(user_id)
    try:
        return await client.get_contact(contact_id)
    except SalesforceAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    finally:
        await client.close()


@router.patch("/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: str,
    updates: dict[str, Any],
    user_id: str = "default",
) -> ContactResponse:
    """
    Update a contact.
    """
    client = await get_salesforce_client(user_id)
    try:
        return await client.update_contact(contact_id, updates)
    except SalesforceAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    finally:
        await client.close()


@router.delete("/contacts/{contact_id}")
async def delete_contact(
    contact_id: str,
    user_id: str = "default",
) -> dict[str, bool]:
    """
    Delete a contact.
    """
    client = await get_salesforce_client(user_id)
    try:
        await client.delete_contact(contact_id)
        return {"success": True}
    except SalesforceAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    finally:
        await client.close()


@router.post("/contacts/bulk", response_model=BulkJobResult)
async def bulk_create_contacts(
    request: BulkContactsRequest,
    user_id: str = "default",
) -> BulkJobResult:
    """
    Bulk create contacts using Salesforce Bulk API.
    """
    client = await get_salesforce_client(user_id)
    try:
        return await client.bulk_create_contacts(
            request.contacts,
            wait_for_completion=request.wait_for_completion,
        )
    except SalesforceAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    finally:
        await client.close()


# ==================== Opportunity Endpoints ====================


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(
    opportunity_id: str,
    user_id: str = "default",
) -> OpportunityResponse:
    """
    Get an opportunity by ID.
    """
    client = await get_salesforce_client(user_id)
    try:
        return await client.get_opportunity(opportunity_id)
    except SalesforceAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    finally:
        await client.close()


@router.patch("/opportunities/{opportunity_id}", response_model=OpportunityResponse)
async def update_opportunity(
    opportunity_id: str,
    request: UpdateOpportunityRequest,
    user_id: str = "default",
) -> OpportunityResponse:
    """
    Update an opportunity.
    """
    client = await get_salesforce_client(user_id)
    try:
        return await client.update_opportunity(opportunity_id, request)
    except SalesforceAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    finally:
        await client.close()


# ==================== Task Endpoints ====================


@router.post("/tasks", response_model=TaskResponse)
async def add_task(
    request: AddTaskRequest,
    user_id: str = "default",
) -> TaskResponse:
    """
    Add a new task in Salesforce.
    """
    client = await get_salesforce_client(user_id)
    try:
        return await client.add_task(request)
    except SalesforceAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    finally:
        await client.close()


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    user_id: str = "default",
) -> TaskResponse:
    """
    Get a task by ID.
    """
    client = await get_salesforce_client(user_id)
    try:
        return await client.get_task(task_id)
    except SalesforceAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    finally:
        await client.close()


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    updates: dict[str, Any],
    user_id: str = "default",
) -> TaskResponse:
    """
    Update a task.
    """
    client = await get_salesforce_client(user_id)
    try:
        return await client.update_task(task_id, updates)
    except SalesforceAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    finally:
        await client.close()


@router.post("/tasks/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: str,
    user_id: str = "default",
) -> TaskResponse:
    """
    Mark a task as completed.
    """
    client = await get_salesforce_client(user_id)
    try:
        return await client.complete_task(task_id)
    except SalesforceAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    finally:
        await client.close()


# ==================== Activity Endpoints ====================


@router.post("/activities", response_model=ActivityResponse)
async def log_activity(
    request: LogActivityRequest,
    user_id: str = "default",
) -> ActivityResponse:
    """
    Log an activity (call, email, meeting) in Salesforce.
    """
    client = await get_salesforce_client(user_id)
    try:
        return await client.log_activity(request)
    except SalesforceAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    finally:
        await client.close()


# ==================== Search Endpoints ====================


@router.post("/search", response_model=SearchRecordsResponse)
async def search_records(
    request: SearchRecordsRequest,
    user_id: str = "default",
) -> SearchRecordsResponse:
    """
    Search for records in Salesforce.
    """
    client = await get_salesforce_client(user_id)
    try:
        return await client.search_records(request)
    except SalesforceAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    finally:
        await client.close()


@router.get("/query")
async def execute_query(
    q: str = Query(..., description="SOQL query string"),
    user_id: str = "default",
) -> dict[str, Any]:
    """
    Execute a SOQL query.
    """
    client = await get_salesforce_client(user_id)
    try:
        records = await client.query(q)
        return {"records": records, "totalSize": len(records)}
    except SalesforceAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    finally:
        await client.close()


# ==================== Bulk API Endpoints ====================


@router.post("/bulk/jobs", response_model=BulkJobResult)
async def execute_bulk_job(
    request: BulkJobRequest,
    wait_for_completion: bool = Query(True),
    user_id: str = "default",
) -> BulkJobResult:
    """
    Execute a bulk operation.
    """
    client = await get_salesforce_client(user_id)
    try:
        bulk_api = await client.get_bulk_api()
        return await bulk_api.execute_bulk_operation(
            request,
            wait_for_completion=wait_for_completion,
        )
    except SalesforceAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    finally:
        await client.close()


@router.get("/bulk/jobs/{job_id}", response_model=BulkJobResponse)
async def get_bulk_job_status(
    job_id: str,
    user_id: str = "default",
) -> BulkJobResponse:
    """
    Get the status of a bulk job.
    """
    client = await get_salesforce_client(user_id)
    try:
        bulk_api = await client.get_bulk_api()
        return await bulk_api.get_job_status(job_id)
    except SalesforceAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    finally:
        await client.close()


@router.post("/bulk/jobs/{job_id}/abort", response_model=BulkJobResponse)
async def abort_bulk_job(
    job_id: str,
    user_id: str = "default",
) -> BulkJobResponse:
    """
    Abort a running bulk job.
    """
    client = await get_salesforce_client(user_id)
    try:
        bulk_api = await client.get_bulk_api()
        return await bulk_api.abort_job(job_id)
    except SalesforceAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    finally:
        await client.close()


# ==================== Metadata Endpoints ====================


@router.get("/describe/{sobject_type}", response_model=SobjectDescribeResponse)
async def describe_sobject(
    sobject_type: str,
    user_id: str = "default",
) -> SobjectDescribeResponse:
    """
    Get metadata about a Salesforce object type.
    """
    client = await get_salesforce_client(user_id)
    try:
        metadata = await client.describe_sobject(sobject_type)
        custom_fields = await client.get_custom_fields(sobject_type)

        return SobjectDescribeResponse(
            name=metadata["name"],
            label=metadata["label"],
            fields=metadata.get("fields", []),
            custom_fields=custom_fields,
        )
    except SalesforceAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    finally:
        await client.close()


@router.get("/picklist/{sobject_type}/{field_name}")
async def get_picklist_values(
    sobject_type: str,
    field_name: str,
    user_id: str = "default",
) -> dict[str, Any]:
    """
    Get picklist values for a field.
    """
    client = await get_salesforce_client(user_id)
    try:
        values = await client.get_picklist_values(sobject_type, field_name)
        return {"values": values}
    except SalesforceAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    finally:
        await client.close()


# ==================== Field Mapping Endpoints ====================


@router.get("/mappings/{sobject_type}", response_model=FieldMappingResponse)
async def get_field_mappings(
    sobject_type: str,
) -> FieldMappingResponse:
    """
    Get current field mappings for an object type.
    """
    mapper = SalesforceFieldMapper()
    mappings = mapper.get_mappings(sobject_type)

    return FieldMappingResponse(
        mappings=[m.model_dump() for m in mappings]
    )


@router.put("/mappings")
async def update_field_mappings(
    config: FieldMappingConfig,
) -> dict[str, bool]:
    """
    Update field mappings configuration.

    Note: In production, this should persist to database.
    """
    # In production, save to database
    logger.info(f"Field mappings updated for org {config.org_id}")
    return {"success": True}


# ==================== User Endpoints ====================


@router.get("/me")
async def get_current_user(
    user_id: str = "default",
) -> dict[str, Any]:
    """
    Get current authenticated Salesforce user info.
    """
    client = await get_salesforce_client(user_id)
    try:
        return await client.get_current_user()
    except SalesforceAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    finally:
        await client.close()
