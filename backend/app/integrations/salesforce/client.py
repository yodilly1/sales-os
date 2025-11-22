"""
Salesforce CRM client for Sales OS.

Provides a complete interface for interacting with Salesforce,
including CRUD operations for Leads, Contacts, Opportunities, Tasks, and Activities.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Optional

import httpx

from backend.app.integrations.salesforce.bulk import SalesforceBulkAPI
from backend.app.integrations.salesforce.field_mapping import SalesforceFieldMapper
from backend.app.integrations.salesforce.oauth2 import SalesforceTokenManager
from backend.app.models.salesforce import (
    ActivityResponse,
    AddTaskRequest,
    BulkJobRequest,
    BulkJobResult,
    ContactResponse,
    CreateContactRequest,
    CreateLeadRequest,
    LeadResponse,
    LogActivityRequest,
    OpportunityResponse,
    SalesforceAPIError,
    SalesforceCredentials,
    SalesforceError,
    SearchRecordsRequest,
    SearchRecordsResponse,
    SearchResult,
    TaskResponse,
    UpdateOpportunityRequest,
)

logger = logging.getLogger(__name__)


class SalesforceClient:
    """
    Main Salesforce CRM client.

    Provides methods for:
    - Lead management (create, update, convert)
    - Contact management (create, update)
    - Opportunity management (update stages, amounts)
    - Task management (create, update)
    - Activity logging (calls, emails, meetings)
    - Record search (SOSL and SOQL)
    - Bulk operations for large datasets
    """

    # Salesforce API version
    API_VERSION = "v59.0"

    # Rate limiting settings
    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 1.0
    RATE_LIMIT_DELAY_SECONDS = 60.0

    def __init__(
        self,
        token_manager: SalesforceTokenManager,
        field_mapper: Optional[SalesforceFieldMapper] = None,
    ):
        """
        Initialize the Salesforce client.

        Args:
            token_manager: Token manager for authentication
            field_mapper: Optional custom field mapper
        """
        self.token_manager = token_manager
        self.field_mapper = field_mapper or SalesforceFieldMapper()
        self._http_client: Optional[httpx.AsyncClient] = None
        self._bulk_api: Optional[SalesforceBulkAPI] = None

    @property
    def instance_url(self) -> str:
        """Get the Salesforce instance URL."""
        return self.token_manager.instance_url

    @property
    def base_url(self) -> str:
        """Get the base REST API URL."""
        return f"{self.instance_url}/services/data/{self.API_VERSION}"

    @property
    def http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                follow_redirects=True,
            )
        return self._http_client

    async def _get_headers(self) -> dict[str, str]:
        """Get request headers with valid access token."""
        access_token = await self.token_manager.get_valid_access_token()
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Make an authenticated request to Salesforce.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint (relative to base URL)
            data: Request body data
            params: Query parameters

        Returns:
            Response data

        Raises:
            SalesforceAPIError: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        headers = await self._get_headers()

        for attempt in range(self.MAX_RETRIES):
            try:
                response = await self.http_client.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=headers,
                )

                # Handle rate limiting
                if response.status_code == 429:
                    if attempt < self.MAX_RETRIES - 1:
                        await asyncio.sleep(self.RATE_LIMIT_DELAY_SECONDS)
                        continue
                    raise SalesforceAPIError(
                        message="Rate limit exceeded",
                        status_code=429,
                    )

                # Handle success
                if response.status_code in (200, 201, 204):
                    if response.status_code == 204 or not response.content:
                        return {}
                    return response.json()

                # Handle errors
                error_data = response.json() if response.content else []
                errors = []

                if isinstance(error_data, list):
                    for err in error_data:
                        errors.append(
                            SalesforceError(
                                error_code=err.get("errorCode", "UNKNOWN"),
                                message=err.get("message", "Unknown error"),
                                fields=err.get("fields"),
                            )
                        )
                else:
                    errors.append(
                        SalesforceError(
                            error_code=error_data.get("errorCode", "UNKNOWN"),
                            message=error_data.get("message", str(error_data)),
                        )
                    )

                raise SalesforceAPIError(
                    message=errors[0].message if errors else "Unknown error",
                    status_code=response.status_code,
                    errors=errors,
                )

            except httpx.TimeoutException:
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY_SECONDS * (attempt + 1))
                    continue
                raise SalesforceAPIError(
                    message="Request timed out",
                    status_code=408,
                )

            except httpx.HTTPError as e:
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY_SECONDS * (attempt + 1))
                    continue
                raise SalesforceAPIError(
                    message=f"HTTP error: {str(e)}",
                    status_code=500,
                )

        raise SalesforceAPIError(
            message="Max retries exceeded",
            status_code=500,
        )

    async def close(self) -> None:
        """Close the client and release resources."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
        if self._bulk_api:
            await self._bulk_api.close()
        await self.token_manager.close()

    # ==================== Lead Operations ====================

    async def create_lead(self, request: CreateLeadRequest) -> LeadResponse:
        """
        Create a new lead in Salesforce.

        Args:
            request: Lead creation request

        Returns:
            Created lead response

        Raises:
            SalesforceAPIError: If creation fails
        """
        # Map fields to Salesforce format
        data = self.field_mapper.map_to_salesforce(
            "Lead",
            request.model_dump(exclude_none=True),
        )

        result = await self._request("POST", "/sobjects/Lead", data=data)

        # Fetch the created lead to return full details
        return await self.get_lead(result["id"])

    async def get_lead(self, lead_id: str) -> LeadResponse:
        """
        Get a lead by ID.

        Args:
            lead_id: Salesforce lead ID

        Returns:
            Lead response

        Raises:
            SalesforceAPIError: If lead not found
        """
        result = await self._request("GET", f"/sobjects/Lead/{lead_id}")

        return LeadResponse(
            id=result["Id"],
            first_name=result.get("FirstName"),
            last_name=result["LastName"],
            company=result["Company"],
            email=result.get("Email"),
            phone=result.get("Phone"),
            title=result.get("Title"),
            status=result.get("Status", ""),
            owner_id=result.get("OwnerId"),
            created_date=result.get("CreatedDate"),
            last_modified_date=result.get("LastModifiedDate"),
            is_converted=result.get("IsConverted", False),
            converted_contact_id=result.get("ConvertedContactId"),
            converted_account_id=result.get("ConvertedAccountId"),
            converted_opportunity_id=result.get("ConvertedOpportunityId"),
        )

    async def update_lead(
        self,
        lead_id: str,
        updates: dict[str, Any],
    ) -> LeadResponse:
        """
        Update a lead.

        Args:
            lead_id: Salesforce lead ID
            updates: Fields to update

        Returns:
            Updated lead response

        Raises:
            SalesforceAPIError: If update fails
        """
        data = self.field_mapper.map_to_salesforce("Lead", updates)
        await self._request("PATCH", f"/sobjects/Lead/{lead_id}", data=data)
        return await self.get_lead(lead_id)

    async def delete_lead(self, lead_id: str) -> bool:
        """
        Delete a lead.

        Args:
            lead_id: Salesforce lead ID

        Returns:
            True if deletion was successful

        Raises:
            SalesforceAPIError: If deletion fails
        """
        await self._request("DELETE", f"/sobjects/Lead/{lead_id}")
        return True

    # ==================== Contact Operations ====================

    async def create_contact(self, request: CreateContactRequest) -> ContactResponse:
        """
        Create a new contact in Salesforce.

        Args:
            request: Contact creation request

        Returns:
            Created contact response

        Raises:
            SalesforceAPIError: If creation fails
        """
        data = self.field_mapper.map_to_salesforce(
            "Contact",
            request.model_dump(exclude_none=True),
        )

        result = await self._request("POST", "/sobjects/Contact", data=data)
        return await self.get_contact(result["id"])

    async def get_contact(self, contact_id: str) -> ContactResponse:
        """
        Get a contact by ID.

        Args:
            contact_id: Salesforce contact ID

        Returns:
            Contact response

        Raises:
            SalesforceAPIError: If contact not found
        """
        result = await self._request("GET", f"/sobjects/Contact/{contact_id}")

        return ContactResponse(
            id=result["Id"],
            first_name=result.get("FirstName"),
            last_name=result["LastName"],
            name=result.get("Name"),
            account_id=result.get("AccountId"),
            email=result.get("Email"),
            phone=result.get("Phone"),
            title=result.get("Title"),
            owner_id=result.get("OwnerId"),
            created_date=result.get("CreatedDate"),
            last_modified_date=result.get("LastModifiedDate"),
        )

    async def update_contact(
        self,
        contact_id: str,
        updates: dict[str, Any],
    ) -> ContactResponse:
        """
        Update a contact.

        Args:
            contact_id: Salesforce contact ID
            updates: Fields to update

        Returns:
            Updated contact response

        Raises:
            SalesforceAPIError: If update fails
        """
        data = self.field_mapper.map_to_salesforce("Contact", updates)
        await self._request("PATCH", f"/sobjects/Contact/{contact_id}", data=data)
        return await self.get_contact(contact_id)

    async def delete_contact(self, contact_id: str) -> bool:
        """
        Delete a contact.

        Args:
            contact_id: Salesforce contact ID

        Returns:
            True if deletion was successful

        Raises:
            SalesforceAPIError: If deletion fails
        """
        await self._request("DELETE", f"/sobjects/Contact/{contact_id}")
        return True

    # ==================== Opportunity Operations ====================

    async def get_opportunity(self, opportunity_id: str) -> OpportunityResponse:
        """
        Get an opportunity by ID.

        Args:
            opportunity_id: Salesforce opportunity ID

        Returns:
            Opportunity response

        Raises:
            SalesforceAPIError: If opportunity not found
        """
        result = await self._request("GET", f"/sobjects/Opportunity/{opportunity_id}")

        return OpportunityResponse(
            id=result["Id"],
            name=result["Name"],
            account_id=result.get("AccountId"),
            stage_name=result["StageName"],
            amount=result.get("Amount"),
            close_date=result.get("CloseDate"),
            probability=result.get("Probability"),
            is_closed=result.get("IsClosed", False),
            is_won=result.get("IsWon", False),
            owner_id=result.get("OwnerId"),
            created_date=result.get("CreatedDate"),
            last_modified_date=result.get("LastModifiedDate"),
        )

    async def update_opportunity(
        self,
        opportunity_id: str,
        request: UpdateOpportunityRequest,
    ) -> OpportunityResponse:
        """
        Update an opportunity.

        Args:
            opportunity_id: Salesforce opportunity ID
            request: Update request

        Returns:
            Updated opportunity response

        Raises:
            SalesforceAPIError: If update fails
        """
        data = self.field_mapper.map_to_salesforce(
            "Opportunity",
            request.model_dump(exclude_none=True),
        )

        await self._request("PATCH", f"/sobjects/Opportunity/{opportunity_id}", data=data)
        return await self.get_opportunity(opportunity_id)

    async def create_opportunity(
        self,
        name: str,
        stage_name: str,
        close_date: datetime,
        account_id: Optional[str] = None,
        amount: Optional[float] = None,
        **kwargs: Any,
    ) -> OpportunityResponse:
        """
        Create a new opportunity.

        Args:
            name: Opportunity name
            stage_name: Sales stage
            close_date: Expected close date
            account_id: Related account ID
            amount: Deal amount
            **kwargs: Additional fields

        Returns:
            Created opportunity response

        Raises:
            SalesforceAPIError: If creation fails
        """
        data = {
            "Name": name,
            "StageName": stage_name,
            "CloseDate": close_date.strftime("%Y-%m-%d"),
        }

        if account_id:
            data["AccountId"] = account_id
        if amount is not None:
            data["Amount"] = amount

        # Add any additional fields
        for key, value in kwargs.items():
            if value is not None:
                data[key] = value

        result = await self._request("POST", "/sobjects/Opportunity", data=data)
        return await self.get_opportunity(result["id"])

    # ==================== Task Operations ====================

    async def add_task(self, request: AddTaskRequest) -> TaskResponse:
        """
        Add a new task in Salesforce.

        Args:
            request: Task creation request

        Returns:
            Created task response

        Raises:
            SalesforceAPIError: If creation fails
        """
        data = self.field_mapper.map_to_salesforce(
            "Task",
            request.model_dump(exclude_none=True),
        )

        result = await self._request("POST", "/sobjects/Task", data=data)
        return await self.get_task(result["id"])

    async def get_task(self, task_id: str) -> TaskResponse:
        """
        Get a task by ID.

        Args:
            task_id: Salesforce task ID

        Returns:
            Task response

        Raises:
            SalesforceAPIError: If task not found
        """
        result = await self._request("GET", f"/sobjects/Task/{task_id}")

        return TaskResponse(
            id=result["Id"],
            subject=result["Subject"],
            what_id=result.get("WhatId"),
            who_id=result.get("WhoId"),
            owner_id=result.get("OwnerId"),
            activity_date=result.get("ActivityDate"),
            priority=result.get("Priority", "Normal"),
            status=result.get("Status", "Not Started"),
            is_closed=result.get("IsClosed", False),
            created_date=result.get("CreatedDate"),
        )

    async def update_task(
        self,
        task_id: str,
        updates: dict[str, Any],
    ) -> TaskResponse:
        """
        Update a task.

        Args:
            task_id: Salesforce task ID
            updates: Fields to update

        Returns:
            Updated task response

        Raises:
            SalesforceAPIError: If update fails
        """
        data = self.field_mapper.map_to_salesforce("Task", updates)
        await self._request("PATCH", f"/sobjects/Task/{task_id}", data=data)
        return await self.get_task(task_id)

    async def complete_task(self, task_id: str) -> TaskResponse:
        """
        Mark a task as completed.

        Args:
            task_id: Salesforce task ID

        Returns:
            Updated task response

        Raises:
            SalesforceAPIError: If update fails
        """
        return await self.update_task(task_id, {"status": "Completed"})

    # ==================== Activity Logging ====================

    async def log_activity(self, request: LogActivityRequest) -> ActivityResponse:
        """
        Log an activity (call, email, meeting) in Salesforce.

        Activities are logged as completed Tasks in Salesforce.

        Args:
            request: Activity logging request

        Returns:
            Created activity response

        Raises:
            SalesforceAPIError: If logging fails
        """
        # Map activity type to Salesforce task type
        task_type_map = {
            "Call": "Call",
            "Email": "Email",
            "Meeting": "Meeting",
            "Other": "Other",
        }

        data = {
            "Subject": request.subject,
            "Status": request.status,
            "TaskSubtype": task_type_map.get(request.activity_type.value, "Other"),
        }

        if request.what_id:
            data["WhatId"] = request.what_id
        if request.who_id:
            data["WhoId"] = request.who_id
        if request.activity_date:
            data["ActivityDate"] = request.activity_date.strftime("%Y-%m-%d")
        if request.description:
            data["Description"] = request.description
        if request.call_disposition:
            data["CallDisposition"] = request.call_disposition
        if request.duration_minutes:
            data["CallDurationInSeconds"] = request.duration_minutes * 60

        # Add custom fields
        if request.custom_fields:
            data.update(request.custom_fields)

        result = await self._request("POST", "/sobjects/Task", data=data)

        return ActivityResponse(
            id=result["id"],
            subject=request.subject,
            what_id=request.what_id,
            who_id=request.who_id,
            activity_type=request.activity_type.value,
            activity_date=request.activity_date,
            duration_minutes=request.duration_minutes,
            status=request.status,
            created_date=datetime.now(),
        )

    # ==================== Search Operations ====================

    async def search_records(
        self,
        request: SearchRecordsRequest,
    ) -> SearchRecordsResponse:
        """
        Search for records using SOSL (Salesforce Object Search Language).

        Args:
            request: Search request

        Returns:
            Search results

        Raises:
            SalesforceAPIError: If search fails
        """
        # Build SOSL query
        search_term = request.query.replace("'", "\\'")
        sobject_clause = ", ".join(request.sobject_types)

        sosl_query = f"FIND {{{search_term}}} IN ALL FIELDS RETURNING {sobject_clause}"

        # Add limit
        params = {"q": sosl_query}

        result = await self._request("GET", "/search/", params=params)

        search_results = []
        for record in result.get("searchRecords", []):
            attributes = record.get("attributes", {})
            search_results.append(
                SearchResult(
                    id=record.get("Id", ""),
                    sobject_type=attributes.get("type", "Unknown"),
                    name=record.get("Name"),
                    attributes={
                        k: v
                        for k, v in record.items()
                        if k not in ("Id", "Name", "attributes")
                    },
                )
            )

        return SearchRecordsResponse(
            results=search_results[: request.limit],
            total_size=len(search_results),
            done=True,
        )

    async def query(self, soql: str) -> list[dict[str, Any]]:
        """
        Execute a SOQL query.

        Args:
            soql: SOQL query string

        Returns:
            List of records

        Raises:
            SalesforceAPIError: If query fails
        """
        params = {"q": soql}
        result = await self._request("GET", "/query/", params=params)

        records = result.get("records", [])

        # Handle pagination
        while not result.get("done", True) and result.get("nextRecordsUrl"):
            next_url = result["nextRecordsUrl"]
            # Extract just the path part
            if next_url.startswith("/services/data"):
                next_url = next_url.replace(f"/services/data/{self.API_VERSION}", "")
            result = await self._request("GET", next_url)
            records.extend(result.get("records", []))

        return records

    async def query_more(self, next_records_url: str) -> dict[str, Any]:
        """
        Get next batch of query results.

        Args:
            next_records_url: URL for next batch

        Returns:
            Next batch of results

        Raises:
            SalesforceAPIError: If request fails
        """
        if next_records_url.startswith("/services/data"):
            next_records_url = next_records_url.replace(
                f"/services/data/{self.API_VERSION}", ""
            )
        return await self._request("GET", next_records_url)

    # ==================== Bulk Operations ====================

    async def get_bulk_api(self) -> SalesforceBulkAPI:
        """
        Get the Bulk API handler.

        Returns:
            SalesforceBulkAPI instance
        """
        if self._bulk_api is None:
            access_token = await self.token_manager.get_valid_access_token()
            self._bulk_api = SalesforceBulkAPI(
                instance_url=self.instance_url,
                access_token=access_token,
                api_version=self.API_VERSION,
            )
        return self._bulk_api

    async def bulk_create_leads(
        self,
        leads: list[CreateLeadRequest],
        wait_for_completion: bool = True,
    ) -> BulkJobResult:
        """
        Bulk create leads.

        Args:
            leads: List of lead creation requests
            wait_for_completion: Whether to wait for job completion

        Returns:
            Bulk job result

        Raises:
            SalesforceAPIError: If operation fails
        """
        records = [
            self.field_mapper.map_to_salesforce("Lead", lead.model_dump(exclude_none=True))
            for lead in leads
        ]

        bulk_api = await self.get_bulk_api()
        return await bulk_api.execute_bulk_operation(
            BulkJobRequest(
                sobject_type="Lead",
                operation="insert",
                records=records,
            ),
            wait_for_completion=wait_for_completion,
        )

    async def bulk_create_contacts(
        self,
        contacts: list[CreateContactRequest],
        wait_for_completion: bool = True,
    ) -> BulkJobResult:
        """
        Bulk create contacts.

        Args:
            contacts: List of contact creation requests
            wait_for_completion: Whether to wait for job completion

        Returns:
            Bulk job result

        Raises:
            SalesforceAPIError: If operation fails
        """
        records = [
            self.field_mapper.map_to_salesforce(
                "Contact", contact.model_dump(exclude_none=True)
            )
            for contact in contacts
        ]

        bulk_api = await self.get_bulk_api()
        return await bulk_api.execute_bulk_operation(
            BulkJobRequest(
                sobject_type="Contact",
                operation="insert",
                records=records,
            ),
            wait_for_completion=wait_for_completion,
        )

    async def bulk_update_records(
        self,
        sobject_type: str,
        records: list[dict[str, Any]],
        wait_for_completion: bool = True,
    ) -> BulkJobResult:
        """
        Bulk update records.

        Args:
            sobject_type: Salesforce object type
            records: List of records with Id field
            wait_for_completion: Whether to wait for job completion

        Returns:
            Bulk job result

        Raises:
            SalesforceAPIError: If operation fails
        """
        bulk_api = await self.get_bulk_api()
        return await bulk_api.execute_bulk_operation(
            BulkJobRequest(
                sobject_type=sobject_type,
                operation="update",
                records=records,
            ),
            wait_for_completion=wait_for_completion,
        )

    async def bulk_upsert_records(
        self,
        sobject_type: str,
        records: list[dict[str, Any]],
        external_id_field: str,
        wait_for_completion: bool = True,
    ) -> BulkJobResult:
        """
        Bulk upsert records using an external ID field.

        Args:
            sobject_type: Salesforce object type
            records: List of records
            external_id_field: Name of external ID field for matching
            wait_for_completion: Whether to wait for job completion

        Returns:
            Bulk job result

        Raises:
            SalesforceAPIError: If operation fails
        """
        bulk_api = await self.get_bulk_api()
        return await bulk_api.execute_bulk_operation(
            BulkJobRequest(
                sobject_type=sobject_type,
                operation="upsert",
                external_id_field=external_id_field,
                records=records,
            ),
            wait_for_completion=wait_for_completion,
        )

    # ==================== Metadata Operations ====================

    async def describe_sobject(self, sobject_type: str) -> dict[str, Any]:
        """
        Get metadata about a Salesforce object.

        Args:
            sobject_type: Salesforce object type

        Returns:
            Object metadata including fields

        Raises:
            SalesforceAPIError: If request fails
        """
        return await self._request("GET", f"/sobjects/{sobject_type}/describe")

    async def get_custom_fields(self, sobject_type: str) -> list[dict[str, Any]]:
        """
        Get custom fields for a Salesforce object.

        Args:
            sobject_type: Salesforce object type

        Returns:
            List of custom field metadata

        Raises:
            SalesforceAPIError: If request fails
        """
        metadata = await self.describe_sobject(sobject_type)
        fields = metadata.get("fields", [])

        # Custom fields end with __c
        return [f for f in fields if f.get("name", "").endswith("__c")]

    async def get_picklist_values(
        self,
        sobject_type: str,
        field_name: str,
    ) -> list[dict[str, Any]]:
        """
        Get picklist values for a field.

        Args:
            sobject_type: Salesforce object type
            field_name: Field name

        Returns:
            List of picklist value options

        Raises:
            SalesforceAPIError: If request fails
        """
        metadata = await self.describe_sobject(sobject_type)
        fields = metadata.get("fields", [])

        for field in fields:
            if field.get("name") == field_name:
                return field.get("picklistValues", [])

        return []

    # ==================== User Operations ====================

    async def get_current_user(self) -> dict[str, Any]:
        """
        Get the current authenticated user.

        Returns:
            User information

        Raises:
            SalesforceAPIError: If request fails
        """
        # Use the identity URL to get user info
        access_token = await self.token_manager.get_valid_access_token()
        response = await self.http_client.get(
            f"{self.instance_url}/services/oauth2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if response.status_code != 200:
            raise SalesforceAPIError(
                message="Failed to get current user",
                status_code=response.status_code,
            )

        return response.json()

    async def get_user(self, user_id: str) -> dict[str, Any]:
        """
        Get a user by ID.

        Args:
            user_id: Salesforce user ID

        Returns:
            User information

        Raises:
            SalesforceAPIError: If user not found
        """
        return await self._request("GET", f"/sobjects/User/{user_id}")
