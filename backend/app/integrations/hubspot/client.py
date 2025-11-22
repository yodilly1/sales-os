<<<<<<< HEAD
"""HubSpot API client for CRM operations.

This is a stub implementation providing the interface that will be
fully implemented by AGENT-004.
"""

import logging
from typing import Any, Optional

import httpx

from app.core.config import settings
=======
"""
HubSpot CRM Client

A comprehensive client for interacting with HubSpot CRM API including
contact management, deals, notes, tasks, and search functionality.
Features OAuth2 token refresh, rate limiting, and error handling.
"""

import asyncio
import logging
import time
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.core.config import Settings, get_settings
from app.models.hubspot import (
    Association,
    Contact,
    ContactCreate,
    ContactProperties,
    ContactSearchRequest,
    ContactSearchResult,
    ContactUpdate,
    Deal,
    DealCreate,
    DealProperties,
    Note,
    NoteCreate,
    OAuthToken,
    Task,
    TaskCreate,
    TaskPriority,
    TaskStatus,
    TaskType,
)

from .exceptions import (
    HubSpotAuthenticationError,
    HubSpotAuthorizationError,
    HubSpotConfigurationError,
    HubSpotConflictError,
    HubSpotConnectionError,
    HubSpotException,
    HubSpotNotFoundError,
    HubSpotRateLimitError,
    HubSpotServerError,
    HubSpotTokenExpiredError,
    HubSpotValidationError,
)
>>>>>>> origin/claude/hubspot-crm-integration-01AaFjvnS1wUkSz4AGkEMsn2

logger = logging.getLogger(__name__)


<<<<<<< HEAD
class HubSpotClient:
    """Client for HubSpot CRM API operations.

    This stub provides the interface for:
    - Contact management (create, update, search)
    - Company management
    - Deal management
    - Note and task creation

    Full implementation will be provided by AGENT-004.
    """

    BASE_URL = "https://api.hubapi.com"

    def __init__(
        self,
        access_token: Optional[str] = None,
        api_key: Optional[str] = None,
=======
class RateLimiter:
    """Token bucket rate limiter for API requests."""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire a rate limit token, waiting if necessary."""
        async with self._lock:
            now = time.time()

            # Remove expired timestamps
            while self.requests and self.requests[0] < now - self.window_seconds:
                self.requests.popleft()

            # If at limit, wait for the oldest request to expire
            if len(self.requests) >= self.max_requests:
                wait_time = self.requests[0] + self.window_seconds - now
                if wait_time > 0:
                    logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
                    # Clean up again after waiting
                    now = time.time()
                    while self.requests and self.requests[0] < now - self.window_seconds:
                        self.requests.popleft()

            self.requests.append(time.time())


class HubSpotClient:
    """
    HubSpot CRM API client with OAuth2 support, rate limiting, and error handling.

    Supports both API key authentication (for private apps) and OAuth2 authentication
    (for public apps with token refresh).
    """

    def __init__(
        self,
        settings: Settings | None = None,
        api_key: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
>>>>>>> origin/claude/hubspot-crm-integration-01AaFjvnS1wUkSz4AGkEMsn2
    ):
        """
        Initialize HubSpot client.

        Args:
<<<<<<< HEAD
            access_token: OAuth2 access token (preferred)
            api_key: HubSpot API key (deprecated but supported)
        """
        self.access_token = access_token or settings.hubspot_access_token
        self.api_key = api_key or settings.hubspot_api_key
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def is_configured(self) -> bool:
        """Check if HubSpot client is properly configured."""
        return bool(self.access_token or self.api_key)

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            headers = {"Content-Type": "application/json"}
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"

            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers=headers,
                timeout=30.0,
=======
            settings: Application settings (auto-loaded if not provided)
            api_key: HubSpot private app API key
            access_token: OAuth2 access token
            refresh_token: OAuth2 refresh token
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
        """
        self._settings = settings or get_settings()
        self._base_url = self._settings.hubspot_base_url

        # Authentication setup
        self._api_key = api_key or self._settings.hubspot_api_key
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._client_id = client_id or self._settings.hubspot_client_id
        self._client_secret = client_secret or self._settings.hubspot_client_secret
        self._token_expires_at: datetime | None = None

        # Rate limiter
        self._rate_limiter = RateLimiter(
            max_requests=self._settings.hubspot_rate_limit_requests,
            window_seconds=self._settings.hubspot_rate_limit_window,
        )

        # HTTP client
        self._client: httpx.AsyncClient | None = None

        # Validate configuration
        if not self._api_key and not self._access_token:
            logger.warning("HubSpot client initialized without authentication credentials")

    async def __aenter__(self) -> "HubSpotClient":
        """Async context manager entry."""
        await self._ensure_client()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure HTTP client is initialized."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=30.0,
                follow_redirects=True,
>>>>>>> origin/claude/hubspot-crm-integration-01AaFjvnS1wUkSz4AGkEMsn2
            )
        return self._client

    async def close(self) -> None:
<<<<<<< HEAD
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # Contact operations

    async def create_contact(self, properties: dict[str, Any]) -> Optional[dict]:
=======
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def _get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers."""
        headers = {"Content-Type": "application/json"}

        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        elif self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        return headers

    async def _refresh_oauth_token(self) -> None:
        """Refresh OAuth2 access token using refresh token."""
        if not self._refresh_token:
            raise HubSpotTokenExpiredError("No refresh token available")

        if not self._client_id or not self._client_secret:
            raise HubSpotConfigurationError(
                "OAuth2 credentials not configured",
                missing_fields=["client_id", "client_secret"],
            )

        client = await self._ensure_client()

        try:
            response = await client.post(
                "/oauth/v1/token",
                data={
                    "grant_type": "refresh_token",
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "refresh_token": self._refresh_token,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                logger.error(f"Token refresh failed: {response.text}")
                raise HubSpotTokenExpiredError("Failed to refresh OAuth token")

            token_data = response.json()
            self._access_token = token_data["access_token"]
            self._refresh_token = token_data.get("refresh_token", self._refresh_token)
            self._token_expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=token_data.get("expires_in", 3600)
            )

            logger.info("HubSpot OAuth token refreshed successfully")

        except httpx.RequestError as e:
            raise HubSpotConnectionError(f"Token refresh connection error: {e}")

    async def _should_refresh_token(self) -> bool:
        """Check if OAuth token needs refresh."""
        if not self._access_token or not self._token_expires_at:
            return False

        # Refresh if token expires in less than 5 minutes
        return datetime.now(timezone.utc) >= self._token_expires_at - timedelta(minutes=5)

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        retry_count: int = 3,
    ) -> dict[str, Any]:
        """
        Make an authenticated request to HubSpot API.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters
            retry_count: Number of retries for transient errors

        Returns:
            API response data

        Raises:
            HubSpotException: On API errors
        """
        # Check if token needs refresh
        if await self._should_refresh_token():
            await self._refresh_oauth_token()

        # Apply rate limiting
        await self._rate_limiter.acquire()

        client = await self._ensure_client()
        headers = self._get_auth_headers()

        for attempt in range(retry_count):
            try:
                response = await client.request(
                    method=method,
                    url=endpoint,
                    json=data,
                    params=params,
                    headers=headers,
                )

                # Handle response
                return await self._handle_response(response)

            except httpx.RequestError as e:
                if attempt < retry_count - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{retry_count}), "
                        f"retrying in {wait_time}s: {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    raise HubSpotConnectionError(f"Connection error after {retry_count} attempts: {e}")

        raise HubSpotConnectionError("Unexpected error in request loop")

    async def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle API response and raise appropriate exceptions."""
        correlation_id = response.headers.get("x-hubspot-correlation-id")

        if response.status_code == 204:
            return {}

        try:
            data = response.json() if response.content else {}
        except ValueError:
            data = {"raw_response": response.text}

        if 200 <= response.status_code < 300:
            return data

        # Extract error details
        message = data.get("message", "Unknown error")
        category = data.get("category", "")
        errors = data.get("errors", [])

        error_kwargs = {
            "correlation_id": correlation_id,
            "details": {"category": category, "errors": errors},
        }

        # Map status codes to exceptions
        if response.status_code == 401:
            raise HubSpotAuthenticationError(message, **error_kwargs)
        elif response.status_code == 403:
            raise HubSpotAuthorizationError(message, **error_kwargs)
        elif response.status_code == 404:
            raise HubSpotNotFoundError(message, **error_kwargs)
        elif response.status_code == 400:
            raise HubSpotValidationError(message, validation_errors=errors, **error_kwargs)
        elif response.status_code == 409:
            existing_id = None
            if errors:
                existing_id = errors[0].get("context", {}).get("id")
            raise HubSpotConflictError(message, existing_id=existing_id, **error_kwargs)
        elif response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 10))
            raise HubSpotRateLimitError(message, retry_after=retry_after, **error_kwargs)
        elif response.status_code >= 500:
            raise HubSpotServerError(message, **error_kwargs)
        else:
            raise HubSpotException(
                message,
                status_code=response.status_code,
                **error_kwargs,
            )

    # =========================================================================
    # Contact Operations
    # =========================================================================

    async def create_contact(self, contact: ContactCreate) -> Contact:
>>>>>>> origin/claude/hubspot-crm-integration-01AaFjvnS1wUkSz4AGkEMsn2
        """
        Create a new contact in HubSpot.

        Args:
<<<<<<< HEAD
            properties: Contact properties (email, firstname, lastname, etc.)

        Returns:
            Created contact data or None on failure
        """
        if not self.is_configured:
            logger.warning("HubSpot not configured, skipping contact creation")
            return None

        # Stub implementation
        logger.info(f"[STUB] Would create contact with properties: {properties}")
        return {"id": "stub-contact-id", "properties": properties}

    async def update_contact(
        self,
        contact_id: str,
        properties: dict[str, Any],
    ) -> Optional[dict]:
        """
        Update an existing contact.

        Args:
            contact_id: HubSpot contact ID
            properties: Properties to update

        Returns:
            Updated contact data or None on failure
        """
        if not self.is_configured:
            return None

        logger.info(f"[STUB] Would update contact {contact_id} with: {properties}")
        return {"id": contact_id, "properties": properties}

    async def search_contacts(
        self,
        email: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict]:
        """
        Search for contacts.

        Args:
            email: Search by email address
            query: Free-text search query
            limit: Maximum results to return

        Returns:
            List of matching contacts
        """
        if not self.is_configured:
            return []

        logger.info(f"[STUB] Would search contacts with email={email}, query={query}")
        return []

    async def get_contact(self, contact_id: str) -> Optional[dict]:
        """Get contact by ID."""
        if not self.is_configured:
            return None

        logger.info(f"[STUB] Would get contact {contact_id}")
        return None

    # Company operations

    async def create_company(self, properties: dict[str, Any]) -> Optional[dict]:
        """Create a new company."""
        if not self.is_configured:
            return None

        logger.info(f"[STUB] Would create company with properties: {properties}")
        return {"id": "stub-company-id", "properties": properties}

    async def update_company(
        self,
        company_id: str,
        properties: dict[str, Any],
    ) -> Optional[dict]:
        """Update an existing company."""
        if not self.is_configured:
            return None

        logger.info(f"[STUB] Would update company {company_id}")
        return {"id": company_id, "properties": properties}

    async def search_companies(
        self,
        domain: Optional[str] = None,
        name: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict]:
        """Search for companies."""
        if not self.is_configured:
            return []

        logger.info(f"[STUB] Would search companies with domain={domain}, name={name}")
        return []

    # Deal operations

    async def create_deal(
        self,
        properties: dict[str, Any],
        associations: Optional[dict] = None,
    ) -> Optional[dict]:
        """Create a new deal."""
        if not self.is_configured:
            return None

        logger.info(f"[STUB] Would create deal with properties: {properties}")
        return {"id": "stub-deal-id", "properties": properties}

    # Note and task operations

    async def add_note_to_contact(
        self,
        contact_id: str,
        note_body: str,
    ) -> Optional[dict]:
        """Add a note to a contact."""
        if not self.is_configured:
            return None

        logger.info(f"[STUB] Would add note to contact {contact_id}")
        return {"id": "stub-note-id"}

    async def create_task(
        self,
        contact_id: str,
        subject: str,
        due_date: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Optional[dict]:
        """Create a task associated with a contact."""
        if not self.is_configured:
            return None

        logger.info(f"[STUB] Would create task for contact {contact_id}")
        return {"id": "stub-task-id"}

    # Association operations

    async def associate_contact_to_company(
        self,
        contact_id: str,
        company_id: str,
    ) -> bool:
        """Associate a contact with a company."""
        if not self.is_configured:
            return False

        logger.info(f"[STUB] Would associate contact {contact_id} to company {company_id}")
        return True
=======
            contact: Contact data to create

        Returns:
            Created contact object

        Raises:
            HubSpotValidationError: If contact data is invalid
            HubSpotConflictError: If contact with email already exists
        """
        properties = contact.model_dump(exclude_none=True, by_alias=True)

        data = await self._request(
            "POST",
            "/crm/v3/objects/contacts",
            data={"properties": properties},
        )

        return Contact(
            id=data["id"],
            properties=ContactProperties(**data.get("properties", {})),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
            archived=data.get("archived", False),
        )

    async def update_contact(self, contact_id: str, contact: ContactUpdate) -> Contact:
        """
        Update an existing contact in HubSpot.

        Args:
            contact_id: HubSpot contact ID
            contact: Contact data to update

        Returns:
            Updated contact object

        Raises:
            HubSpotNotFoundError: If contact doesn't exist
            HubSpotValidationError: If update data is invalid
        """
        properties = contact.model_dump(exclude_none=True, by_alias=True)

        data = await self._request(
            "PATCH",
            f"/crm/v3/objects/contacts/{contact_id}",
            data={"properties": properties},
        )

        return Contact(
            id=data["id"],
            properties=ContactProperties(**data.get("properties", {})),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
            archived=data.get("archived", False),
        )

    async def get_contact(self, contact_id: str, properties: list[str] | None = None) -> Contact:
        """
        Get a contact by ID.

        Args:
            contact_id: HubSpot contact ID
            properties: List of properties to include

        Returns:
            Contact object

        Raises:
            HubSpotNotFoundError: If contact doesn't exist
        """
        params = {}
        if properties:
            params["properties"] = ",".join(properties)

        data = await self._request(
            "GET",
            f"/crm/v3/objects/contacts/{contact_id}",
            params=params,
        )

        return Contact(
            id=data["id"],
            properties=ContactProperties(**data.get("properties", {})),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
            archived=data.get("archived", False),
        )

    async def delete_contact(self, contact_id: str) -> bool:
        """
        Delete (archive) a contact.

        Args:
            contact_id: HubSpot contact ID

        Returns:
            True if successful

        Raises:
            HubSpotNotFoundError: If contact doesn't exist
        """
        await self._request("DELETE", f"/crm/v3/objects/contacts/{contact_id}")
        return True

    async def search_contacts(
        self,
        search_request: ContactSearchRequest,
    ) -> ContactSearchResult:
        """
        Search for contacts using HubSpot's search API.

        Args:
            search_request: Search parameters including filters, query, and pagination

        Returns:
            Search results with total count and contacts

        Example:
            # Search by email
            request = ContactSearchRequest(
                filter_groups=[
                    SearchFilterGroup(filters=[
                        SearchFilter(
                            property_name="email",
                            operator="EQ",
                            value="john@example.com"
                        )
                    ])
                ]
            )
            results = await client.search_contacts(request)
        """
        request_data: dict[str, Any] = {
            "limit": search_request.limit,
        }

        if search_request.query:
            request_data["query"] = search_request.query

        if search_request.filter_groups:
            request_data["filterGroups"] = [
                {"filters": [f.model_dump(by_alias=True) for f in group.filters]}
                for group in search_request.filter_groups
            ]

        if search_request.sorts:
            request_data["sorts"] = search_request.sorts

        if search_request.properties:
            request_data["properties"] = search_request.properties

        if search_request.after:
            request_data["after"] = search_request.after

        data = await self._request(
            "POST",
            "/crm/v3/objects/contacts/search",
            data=request_data,
        )

        contacts = [
            Contact(
                id=item["id"],
                properties=ContactProperties(**item.get("properties", {})),
                created_at=item.get("createdAt"),
                updated_at=item.get("updatedAt"),
                archived=item.get("archived", False),
            )
            for item in data.get("results", [])
        ]

        return ContactSearchResult(
            total=data.get("total", len(contacts)),
            contacts=contacts,
        )

    async def get_contact_by_email(self, email: str) -> Contact | None:
        """
        Find a contact by email address.

        Args:
            email: Email address to search for

        Returns:
            Contact if found, None otherwise
        """
        search_request = ContactSearchRequest(
            filter_groups=[
                {
                    "filters": [
                        {
                            "propertyName": "email",
                            "operator": "EQ",
                            "value": email,
                        }
                    ]
                }
            ],
            limit=1,
        )

        # Build the request manually for this simpler case
        data = await self._request(
            "POST",
            "/crm/v3/objects/contacts/search",
            data={
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": "email",
                                "operator": "EQ",
                                "value": email,
                            }
                        ]
                    }
                ],
                "limit": 1,
            },
        )

        results = data.get("results", [])
        if not results:
            return None

        item = results[0]
        return Contact(
            id=item["id"],
            properties=ContactProperties(**item.get("properties", {})),
            created_at=item.get("createdAt"),
            updated_at=item.get("updatedAt"),
            archived=item.get("archived", False),
        )

    # =========================================================================
    # Deal Operations
    # =========================================================================

    async def create_deal(self, deal: DealCreate) -> Deal:
        """
        Create a new deal in HubSpot.

        Args:
            deal: Deal data to create

        Returns:
            Created deal object

        Raises:
            HubSpotValidationError: If deal data is invalid
        """
        properties = deal.model_dump(
            exclude={"associated_contact_ids", "associated_company_ids"},
            exclude_none=True,
            by_alias=True,
        )

        # Build associations
        associations = []

        for contact_id in deal.associated_contact_ids:
            associations.append({
                "to": {"id": contact_id},
                "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 3}],
            })

        for company_id in deal.associated_company_ids:
            associations.append({
                "to": {"id": company_id},
                "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 5}],
            })

        request_data: dict[str, Any] = {"properties": properties}
        if associations:
            request_data["associations"] = associations

        data = await self._request(
            "POST",
            "/crm/v3/objects/deals",
            data=request_data,
        )

        return Deal(
            id=data["id"],
            properties=DealProperties(**data.get("properties", {})),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
            archived=data.get("archived", False),
        )

    async def get_deal(self, deal_id: str, properties: list[str] | None = None) -> Deal:
        """
        Get a deal by ID.

        Args:
            deal_id: HubSpot deal ID
            properties: List of properties to include

        Returns:
            Deal object

        Raises:
            HubSpotNotFoundError: If deal doesn't exist
        """
        params = {}
        if properties:
            params["properties"] = ",".join(properties)

        data = await self._request(
            "GET",
            f"/crm/v3/objects/deals/{deal_id}",
            params=params,
        )

        return Deal(
            id=data["id"],
            properties=DealProperties(**data.get("properties", {})),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
            archived=data.get("archived", False),
        )

    # =========================================================================
    # Note/Engagement Operations
    # =========================================================================

    async def add_note_to_contact(self, note: NoteCreate) -> Note:
        """
        Add a note (engagement) to a contact.

        Args:
            note: Note data including content and associations

        Returns:
            Created note object

        Raises:
            HubSpotValidationError: If note data is invalid
        """
        timestamp = note.timestamp or datetime.now(timezone.utc)
        timestamp_ms = int(timestamp.timestamp() * 1000)

        # Build associations
        associations = []

        if note.contact_id:
            associations.append({
                "to": {"id": note.contact_id},
                "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 202}],
            })

        if note.company_id:
            associations.append({
                "to": {"id": note.company_id},
                "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 190}],
            })

        if note.deal_id:
            associations.append({
                "to": {"id": note.deal_id},
                "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 214}],
            })

        request_data: dict[str, Any] = {
            "properties": {
                "hs_timestamp": str(timestamp_ms),
                "hs_note_body": note.body,
            },
        }

        if note.owner_id:
            request_data["properties"]["hubspot_owner_id"] = note.owner_id

        if associations:
            request_data["associations"] = associations

        data = await self._request(
            "POST",
            "/crm/v3/objects/notes",
            data=request_data,
        )

        return Note(
            id=data["id"],
            body=data.get("properties", {}).get("hs_note_body", note.body),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
            associations={
                "contacts": [note.contact_id] if note.contact_id else [],
                "companies": [note.company_id] if note.company_id else [],
                "deals": [note.deal_id] if note.deal_id else [],
            },
        )

    # =========================================================================
    # Task Operations
    # =========================================================================

    async def create_task(self, task: TaskCreate) -> Task:
        """
        Create a task in HubSpot.

        Args:
            task: Task data including subject, due date, and associations

        Returns:
            Created task object

        Raises:
            HubSpotValidationError: If task data is invalid
        """
        properties: dict[str, Any] = {
            "hs_task_subject": task.subject,
            "hs_task_status": task.status.value,
            "hs_task_priority": task.priority.value,
            "hs_task_type": task.task_type.value,
        }

        if task.body:
            properties["hs_task_body"] = task.body

        if task.due_date:
            properties["hs_timestamp"] = str(int(task.due_date.timestamp() * 1000))

        if task.owner_id:
            properties["hubspot_owner_id"] = task.owner_id

        # Build associations
        associations = []

        if task.contact_id:
            associations.append({
                "to": {"id": task.contact_id},
                "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 204}],
            })

        if task.company_id:
            associations.append({
                "to": {"id": task.company_id},
                "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 192}],
            })

        if task.deal_id:
            associations.append({
                "to": {"id": task.deal_id},
                "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 216}],
            })

        request_data: dict[str, Any] = {"properties": properties}
        if associations:
            request_data["associations"] = associations

        data = await self._request(
            "POST",
            "/crm/v3/objects/tasks",
            data=request_data,
        )

        props = data.get("properties", {})

        return Task(
            id=data["id"],
            subject=props.get("hs_task_subject", task.subject),
            body=props.get("hs_task_body"),
            status=TaskStatus(props.get("hs_task_status", task.status.value)),
            priority=TaskPriority(props.get("hs_task_priority", task.priority.value)),
            task_type=TaskType(props.get("hs_task_type", task.task_type.value)),
            due_date=task.due_date,
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
            associations={
                "contacts": [task.contact_id] if task.contact_id else [],
                "companies": [task.company_id] if task.company_id else [],
                "deals": [task.deal_id] if task.deal_id else [],
            },
        )

    # =========================================================================
    # Association Operations
    # =========================================================================

    async def create_association(self, association: Association) -> bool:
        """
        Create an association between two HubSpot objects.

        Args:
            association: Association details

        Returns:
            True if successful
        """
        await self._request(
            "PUT",
            f"/crm/v4/objects/{association.from_object_type}/{association.from_object_id}"
            f"/associations/{association.to_object_type}/{association.to_object_id}",
            data=[
                {
                    "associationCategory": "HUBSPOT_DEFINED",
                    "associationTypeId": self._get_association_type_id(
                        association.from_object_type,
                        association.to_object_type,
                    ),
                }
            ],
        )
        return True

    def _get_association_type_id(self, from_type: str, to_type: str) -> int:
        """Get the HubSpot association type ID for object types."""
        association_map = {
            ("contact", "company"): 1,
            ("contact", "deal"): 3,
            ("deal", "contact"): 3,
            ("deal", "company"): 5,
            ("company", "contact"): 2,
            ("company", "deal"): 6,
            ("note", "contact"): 202,
            ("task", "contact"): 204,
        }
        return association_map.get((from_type, to_type), 0)

    # =========================================================================
    # OAuth Operations
    # =========================================================================

    async def get_oauth_url(self, scopes: list[str] | None = None, state: str | None = None) -> str:
        """
        Generate OAuth authorization URL.

        Args:
            scopes: List of OAuth scopes to request
            state: State parameter for CSRF protection

        Returns:
            OAuth authorization URL
        """
        if not self._client_id:
            raise HubSpotConfigurationError(
                "OAuth not configured",
                missing_fields=["client_id"],
            )

        default_scopes = [
            "crm.objects.contacts.read",
            "crm.objects.contacts.write",
            "crm.objects.deals.read",
            "crm.objects.deals.write",
        ]
        scopes = scopes or default_scopes

        params = {
            "client_id": self._client_id,
            "redirect_uri": self._settings.hubspot_redirect_uri,
            "scope": " ".join(scopes),
        }

        if state:
            params["state"] = state

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"https://app.hubspot.com/oauth/authorize?{query_string}"

    async def exchange_code_for_token(self, code: str) -> OAuthToken:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from OAuth callback

        Returns:
            OAuth token response
        """
        if not self._client_id or not self._client_secret:
            raise HubSpotConfigurationError(
                "OAuth not configured",
                missing_fields=["client_id", "client_secret"],
            )

        client = await self._ensure_client()

        response = await client.post(
            "/oauth/v1/token",
            data={
                "grant_type": "authorization_code",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "redirect_uri": self._settings.hubspot_redirect_uri,
                "code": code,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code != 200:
            raise HubSpotAuthenticationError(f"Token exchange failed: {response.text}")

        token_data = response.json()

        # Update client tokens
        self._access_token = token_data["access_token"]
        self._refresh_token = token_data["refresh_token"]
        self._token_expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=token_data.get("expires_in", 3600)
        )

        return OAuthToken(
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            expires_in=token_data.get("expires_in", 3600),
            token_type=token_data.get("token_type", "bearer"),
            expires_at=self._token_expires_at,
        )

    # =========================================================================
    # Utility Methods
    # =========================================================================

    async def test_connection(self) -> bool:
        """
        Test the HubSpot API connection.

        Returns:
            True if connection is successful

        Raises:
            HubSpotException: If connection fails
        """
        try:
            await self._request("GET", "/crm/v3/objects/contacts", params={"limit": 1})
            return True
        except HubSpotException:
            raise
        except Exception as e:
            raise HubSpotConnectionError(f"Connection test failed: {e}")

    def set_tokens(
        self,
        access_token: str,
        refresh_token: str | None = None,
        expires_at: datetime | None = None,
    ) -> None:
        """
        Set OAuth tokens for the client.

        Args:
            access_token: OAuth access token
            refresh_token: OAuth refresh token
            expires_at: Token expiration datetime
        """
        self._access_token = access_token
        if refresh_token:
            self._refresh_token = refresh_token
        if expires_at:
            self._token_expires_at = expires_at
>>>>>>> origin/claude/hubspot-crm-integration-01AaFjvnS1wUkSz4AGkEMsn2
