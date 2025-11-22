"""
HubSpot API Routes

FastAPI router providing REST endpoints for HubSpot CRM operations including
contacts, deals, notes, tasks, and OAuth authentication.
"""

import logging
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.integrations.hubspot import (
    HubSpotAuthenticationError,
    HubSpotAuthorizationError,
    HubSpotClient,
    HubSpotConflictError,
    HubSpotConnectionError,
    HubSpotException,
    HubSpotNotFoundError,
    HubSpotRateLimitError,
    HubSpotValidationError,
)
from app.models.hubspot import (
    Contact,
    ContactCreate,
    ContactResponse,
    ContactSearchRequest,
    ContactSearchResult,
    ContactUpdate,
    Deal,
    DealCreate,
    DealResponse,
    DealStage,
    Note,
    NoteCreate,
    NoteResponse,
    OAuthToken,
    SearchFilter,
    SearchFilterGroup,
    Task,
    TaskCreate,
    TaskPriority,
    TaskResponse,
    TaskStatus,
    TaskType,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hubspot", tags=["HubSpot"])


# Dependency for HubSpot client
async def get_hubspot_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> HubSpotClient:
    """Get HubSpot client instance."""
    return HubSpotClient(settings=settings)


# Response models for API endpoints

class ErrorResponse(BaseModel):
    """Error response model."""
    detail: str
    error_type: str
    correlation_id: str | None = None


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    status: str
    connected: bool
    timestamp: datetime


class ContactListResponse(BaseModel):
    """Response model for contact list operations."""
    total: int
    contacts: list[Contact]
    next_cursor: str | None = None


class OAuthUrlResponse(BaseModel):
    """OAuth URL response model."""
    authorization_url: str


# Exception handlers

def handle_hubspot_exception(e: HubSpotException) -> HTTPException:
    """Convert HubSpot exceptions to HTTP exceptions."""
    status_code = e.status_code or 500
    detail = {
        "message": e.message,
        "error_type": type(e).__name__,
        "correlation_id": e.correlation_id,
        "details": e.details,
    }

    if isinstance(e, HubSpotAuthenticationError):
        status_code = status.HTTP_401_UNAUTHORIZED
    elif isinstance(e, HubSpotAuthorizationError):
        status_code = status.HTTP_403_FORBIDDEN
    elif isinstance(e, HubSpotNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(e, HubSpotValidationError):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(e, HubSpotConflictError):
        status_code = status.HTTP_409_CONFLICT
    elif isinstance(e, HubSpotRateLimitError):
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
    elif isinstance(e, HubSpotConnectionError):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HTTPException(status_code=status_code, detail=detail)


# =========================================================================
# Health & Connection Endpoints
# =========================================================================

@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    client: Annotated[HubSpotClient, Depends(get_hubspot_client)],
) -> HealthCheckResponse:
    """
    Check HubSpot API connection health.

    Returns the connection status and timestamp.
    """
    try:
        async with client:
            connected = await client.test_connection()
            return HealthCheckResponse(
                status="healthy" if connected else "unhealthy",
                connected=connected,
                timestamp=datetime.utcnow(),
            )
    except HubSpotException as e:
        logger.warning(f"HubSpot health check failed: {e}")
        return HealthCheckResponse(
            status="unhealthy",
            connected=False,
            timestamp=datetime.utcnow(),
        )


# =========================================================================
# Contact Endpoints
# =========================================================================

@router.post("/contacts", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact_data: ContactCreate,
    client: Annotated[HubSpotClient, Depends(get_hubspot_client)],
) -> ContactResponse:
    """
    Create a new contact in HubSpot.

    Required fields:
    - email: Valid email address

    Optional fields:
    - firstname, lastname: Contact name
    - phone: Phone number
    - company: Company name
    - jobtitle: Job title
    - lifecyclestage: Lead lifecycle stage
    """
    try:
        async with client:
            contact = await client.create_contact(contact_data)
            return ContactResponse(
                contact=contact,
                success=True,
                message="Contact created successfully",
            )
    except HubSpotConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Contact with this email already exists",
                "existing_id": e.existing_id,
            },
        )
    except HubSpotException as e:
        raise handle_hubspot_exception(e)


@router.get("/contacts/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: str,
    client: Annotated[HubSpotClient, Depends(get_hubspot_client)],
    properties: Annotated[list[str] | None, Query()] = None,
) -> ContactResponse:
    """
    Get a contact by ID.

    Args:
        contact_id: HubSpot contact ID
        properties: Optional list of properties to include
    """
    try:
        async with client:
            contact = await client.get_contact(contact_id, properties=properties)
            return ContactResponse(contact=contact, success=True)
    except HubSpotException as e:
        raise handle_hubspot_exception(e)


@router.patch("/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: str,
    contact_data: ContactUpdate,
    client: Annotated[HubSpotClient, Depends(get_hubspot_client)],
) -> ContactResponse:
    """
    Update an existing contact.

    Only provided fields will be updated. All fields are optional.
    """
    try:
        async with client:
            contact = await client.update_contact(contact_id, contact_data)
            return ContactResponse(
                contact=contact,
                success=True,
                message="Contact updated successfully",
            )
    except HubSpotException as e:
        raise handle_hubspot_exception(e)


@router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: str,
    client: Annotated[HubSpotClient, Depends(get_hubspot_client)],
) -> None:
    """
    Delete (archive) a contact.

    The contact will be archived in HubSpot, not permanently deleted.
    """
    try:
        async with client:
            await client.delete_contact(contact_id)
    except HubSpotException as e:
        raise handle_hubspot_exception(e)


@router.post("/contacts/search", response_model=ContactSearchResult)
async def search_contacts(
    search_request: ContactSearchRequest,
    client: Annotated[HubSpotClient, Depends(get_hubspot_client)],
) -> ContactSearchResult:
    """
    Search for contacts using filters and query.

    Supports:
    - Free text query search
    - Property-based filters with operators (EQ, NEQ, CONTAINS, etc.)
    - Sorting and pagination

    Example request body:
    ```json
    {
        "query": "john",
        "filterGroups": [
            {
                "filters": [
                    {
                        "propertyName": "lifecyclestage",
                        "operator": "EQ",
                        "value": "lead"
                    }
                ]
            }
        ],
        "limit": 10
    }
    ```
    """
    try:
        async with client:
            return await client.search_contacts(search_request)
    except HubSpotException as e:
        raise handle_hubspot_exception(e)


@router.get("/contacts/by-email/{email}", response_model=ContactResponse)
async def get_contact_by_email(
    email: str,
    client: Annotated[HubSpotClient, Depends(get_hubspot_client)],
) -> ContactResponse:
    """
    Find a contact by email address.

    Returns 404 if no contact is found with the given email.
    """
    try:
        async with client:
            contact = await client.get_contact_by_email(email)
            if not contact:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Contact with email '{email}' not found",
                )
            return ContactResponse(contact=contact, success=True)
    except HubSpotException as e:
        raise handle_hubspot_exception(e)


# =========================================================================
# Deal Endpoints
# =========================================================================

@router.post("/deals", response_model=DealResponse, status_code=status.HTTP_201_CREATED)
async def create_deal(
    deal_data: DealCreate,
    client: Annotated[HubSpotClient, Depends(get_hubspot_client)],
) -> DealResponse:
    """
    Create a new deal in HubSpot.

    Required fields:
    - dealname: Name of the deal

    Optional fields:
    - amount: Deal value
    - dealstage: Pipeline stage
    - pipeline: Pipeline name (default: "default")
    - closedate: Expected close date
    - associated_contact_ids: List of contact IDs to associate
    - associated_company_ids: List of company IDs to associate
    """
    try:
        async with client:
            deal = await client.create_deal(deal_data)
            return DealResponse(
                deal=deal,
                success=True,
                message="Deal created successfully",
            )
    except HubSpotException as e:
        raise handle_hubspot_exception(e)


@router.get("/deals/{deal_id}", response_model=DealResponse)
async def get_deal(
    deal_id: str,
    client: Annotated[HubSpotClient, Depends(get_hubspot_client)],
    properties: Annotated[list[str] | None, Query()] = None,
) -> DealResponse:
    """
    Get a deal by ID.

    Args:
        deal_id: HubSpot deal ID
        properties: Optional list of properties to include
    """
    try:
        async with client:
            deal = await client.get_deal(deal_id, properties=properties)
            return DealResponse(deal=deal, success=True)
    except HubSpotException as e:
        raise handle_hubspot_exception(e)


# =========================================================================
# Note Endpoints
# =========================================================================

@router.post("/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    note_data: NoteCreate,
    client: Annotated[HubSpotClient, Depends(get_hubspot_client)],
) -> NoteResponse:
    """
    Create a note and associate it with contacts, companies, or deals.

    Required fields:
    - body: Note content (HTML or plain text)

    Optional fields:
    - contact_id: Contact to associate
    - company_id: Company to associate
    - deal_id: Deal to associate
    - timestamp: Note timestamp (defaults to now)
    - owner_id: HubSpot owner ID
    """
    try:
        async with client:
            note = await client.add_note_to_contact(note_data)
            return NoteResponse(
                note=note,
                success=True,
                message="Note created successfully",
            )
    except HubSpotException as e:
        raise handle_hubspot_exception(e)


@router.post(
    "/contacts/{contact_id}/notes",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_note_to_contact(
    contact_id: str,
    body: str = Query(..., description="Note content"),
    client: Annotated[HubSpotClient, Depends(get_hubspot_client)] = None,
) -> NoteResponse:
    """
    Add a note to a specific contact.

    This is a convenience endpoint that automatically associates
    the note with the specified contact.
    """
    note_data = NoteCreate(body=body, contact_id=contact_id)
    try:
        async with client:
            note = await client.add_note_to_contact(note_data)
            return NoteResponse(
                note=note,
                success=True,
                message="Note added to contact successfully",
            )
    except HubSpotException as e:
        raise handle_hubspot_exception(e)


# =========================================================================
# Task Endpoints
# =========================================================================

@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    client: Annotated[HubSpotClient, Depends(get_hubspot_client)],
) -> TaskResponse:
    """
    Create a task in HubSpot.

    Required fields:
    - subject: Task title

    Optional fields:
    - body: Task description
    - status: NOT_STARTED, IN_PROGRESS, WAITING, COMPLETED, DEFERRED
    - priority: LOW, MEDIUM, HIGH
    - task_type: TODO, CALL, EMAIL
    - due_date: Task due date
    - contact_id, company_id, deal_id: Associations
    - owner_id: Task owner
    """
    try:
        async with client:
            task = await client.create_task(task_data)
            return TaskResponse(
                task=task,
                success=True,
                message="Task created successfully",
            )
    except HubSpotException as e:
        raise handle_hubspot_exception(e)


@router.post(
    "/contacts/{contact_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task_for_contact(
    contact_id: str,
    subject: str = Query(..., description="Task subject"),
    body: str | None = Query(None, description="Task description"),
    due_date: datetime | None = Query(None, description="Due date"),
    priority: TaskPriority = Query(TaskPriority.MEDIUM, description="Task priority"),
    task_type: TaskType = Query(TaskType.TODO, description="Task type"),
    client: Annotated[HubSpotClient, Depends(get_hubspot_client)] = None,
) -> TaskResponse:
    """
    Create a task for a specific contact.

    This is a convenience endpoint that automatically associates
    the task with the specified contact.
    """
    task_data = TaskCreate(
        subject=subject,
        body=body,
        contact_id=contact_id,
        due_date=due_date,
        priority=priority,
        task_type=task_type,
    )
    try:
        async with client:
            task = await client.create_task(task_data)
            return TaskResponse(
                task=task,
                success=True,
                message="Task created for contact successfully",
            )
    except HubSpotException as e:
        raise handle_hubspot_exception(e)


# =========================================================================
# OAuth Endpoints
# =========================================================================

@router.get("/oauth/authorize", response_model=OAuthUrlResponse)
async def get_oauth_url(
    client: Annotated[HubSpotClient, Depends(get_hubspot_client)],
    state: str | None = Query(None, description="State parameter for CSRF protection"),
) -> OAuthUrlResponse:
    """
    Get the OAuth authorization URL for HubSpot.

    Redirect users to this URL to initiate the OAuth flow.
    The state parameter should be used for CSRF protection.
    """
    try:
        async with client:
            url = await client.get_oauth_url(state=state)
            return OAuthUrlResponse(authorization_url=url)
    except HubSpotException as e:
        raise handle_hubspot_exception(e)


@router.get("/oauth/callback")
async def oauth_callback(
    code: str = Query(..., description="Authorization code from HubSpot"),
    state: str | None = Query(None, description="State parameter"),
    client: Annotated[HubSpotClient, Depends(get_hubspot_client)] = None,
) -> OAuthToken:
    """
    Handle OAuth callback from HubSpot.

    Exchange the authorization code for access and refresh tokens.
    Store these tokens securely for future API calls.
    """
    try:
        async with client:
            token = await client.exchange_code_for_token(code)
            # In production, store token in database associated with user
            return token
    except HubSpotException as e:
        raise handle_hubspot_exception(e)


# =========================================================================
# Sync Endpoints (for workflow integrations)
# =========================================================================

class SyncContactRequest(BaseModel):
    """Request model for syncing contact data."""
    email: str
    firstname: str | None = None
    lastname: str | None = None
    company: str | None = None
    jobtitle: str | None = None
    phone: str | None = None
    note: str | None = Field(None, description="Optional note to add after sync")
    create_if_not_exists: bool = Field(True, description="Create contact if not found")


class SyncContactResponse(BaseModel):
    """Response model for contact sync."""
    contact: Contact
    created: bool
    updated: bool
    note_added: bool = False


@router.post("/sync/contact", response_model=SyncContactResponse)
async def sync_contact(
    sync_request: SyncContactRequest,
    client: Annotated[HubSpotClient, Depends(get_hubspot_client)],
) -> SyncContactResponse:
    """
    Sync a contact to HubSpot (create or update).

    This endpoint will:
    1. Search for existing contact by email
    2. Update if found, create if not (and create_if_not_exists is True)
    3. Optionally add a note to the contact

    Useful for integrating with external systems or workflows.
    """
    try:
        async with client:
            # Try to find existing contact
            existing_contact = await client.get_contact_by_email(sync_request.email)

            created = False
            updated = False
            note_added = False

            if existing_contact:
                # Update existing contact
                update_data = ContactUpdate(
                    firstname=sync_request.firstname,
                    lastname=sync_request.lastname,
                    company=sync_request.company,
                    jobtitle=sync_request.jobtitle,
                    phone=sync_request.phone,
                )
                contact = await client.update_contact(existing_contact.id, update_data)
                updated = True
            elif sync_request.create_if_not_exists:
                # Create new contact
                create_data = ContactCreate(
                    email=sync_request.email,
                    firstname=sync_request.firstname,
                    lastname=sync_request.lastname,
                    company=sync_request.company,
                    jobtitle=sync_request.jobtitle,
                    phone=sync_request.phone,
                )
                contact = await client.create_contact(create_data)
                created = True
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Contact with email '{sync_request.email}' not found",
                )

            # Add note if provided
            if sync_request.note:
                note_data = NoteCreate(body=sync_request.note, contact_id=contact.id)
                await client.add_note_to_contact(note_data)
                note_added = True

            return SyncContactResponse(
                contact=contact,
                created=created,
                updated=updated,
                note_added=note_added,
            )

    except HubSpotException as e:
        raise handle_hubspot_exception(e)


class BulkSyncRequest(BaseModel):
    """Request model for bulk contact sync."""
    contacts: list[SyncContactRequest]


class BulkSyncResponse(BaseModel):
    """Response model for bulk contact sync."""
    total: int
    created: int
    updated: int
    failed: int
    errors: list[dict[str, Any]] = Field(default_factory=list)


@router.post("/sync/contacts/bulk", response_model=BulkSyncResponse)
async def bulk_sync_contacts(
    bulk_request: BulkSyncRequest,
    client: Annotated[HubSpotClient, Depends(get_hubspot_client)],
) -> BulkSyncResponse:
    """
    Bulk sync multiple contacts to HubSpot.

    Each contact will be created or updated based on email matching.
    Failed operations are tracked and returned in the response.
    """
    created = 0
    updated = 0
    failed = 0
    errors: list[dict[str, Any]] = []

    try:
        async with client:
            for contact_req in bulk_request.contacts:
                try:
                    existing = await client.get_contact_by_email(contact_req.email)

                    if existing:
                        update_data = ContactUpdate(
                            firstname=contact_req.firstname,
                            lastname=contact_req.lastname,
                            company=contact_req.company,
                            jobtitle=contact_req.jobtitle,
                            phone=contact_req.phone,
                        )
                        await client.update_contact(existing.id, update_data)
                        updated += 1
                    elif contact_req.create_if_not_exists:
                        create_data = ContactCreate(
                            email=contact_req.email,
                            firstname=contact_req.firstname,
                            lastname=contact_req.lastname,
                            company=contact_req.company,
                            jobtitle=contact_req.jobtitle,
                            phone=contact_req.phone,
                        )
                        await client.create_contact(create_data)
                        created += 1

                except HubSpotException as e:
                    failed += 1
                    errors.append({
                        "email": contact_req.email,
                        "error": e.message,
                        "error_type": type(e).__name__,
                    })

    except HubSpotException as e:
        raise handle_hubspot_exception(e)

    return BulkSyncResponse(
        total=len(bulk_request.contacts),
        created=created,
        updated=updated,
        failed=failed,
        errors=errors,
    )
