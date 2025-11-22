"""
Salesforce Pydantic models for API requests and responses.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field


class SalesforceEnvironment(str, Enum):
    """Salesforce environment types."""
    PRODUCTION = "production"
    SANDBOX = "sandbox"


class SalesforceAuthConfig(BaseModel):
    """OAuth2 configuration for Salesforce."""
    client_id: str
    client_secret: str
    redirect_uri: str
    environment: SalesforceEnvironment = SalesforceEnvironment.PRODUCTION

    @property
    def auth_url(self) -> str:
        """Get the authorization URL based on environment."""
        if self.environment == SalesforceEnvironment.SANDBOX:
            return "https://test.salesforce.com/services/oauth2/authorize"
        return "https://login.salesforce.com/services/oauth2/authorize"

    @property
    def token_url(self) -> str:
        """Get the token URL based on environment."""
        if self.environment == SalesforceEnvironment.SANDBOX:
            return "https://test.salesforce.com/services/oauth2/token"
        return "https://login.salesforce.com/services/oauth2/token"


class SalesforceTokenResponse(BaseModel):
    """OAuth2 token response from Salesforce."""
    access_token: str
    refresh_token: Optional[str] = None
    instance_url: str
    token_type: str = "Bearer"
    issued_at: Optional[str] = None
    signature: Optional[str] = None
    id: Optional[str] = None
    expires_in: Optional[int] = None


class SalesforceCredentials(BaseModel):
    """Stored Salesforce credentials."""
    access_token: str
    refresh_token: str
    instance_url: str
    environment: SalesforceEnvironment
    expires_at: Optional[datetime] = None
    org_id: Optional[str] = None


# Lead Models
class LeadStatus(str, Enum):
    """Standard Salesforce lead statuses."""
    OPEN = "Open - Not Contacted"
    WORKING = "Working - Contacted"
    CLOSED_CONVERTED = "Closed - Converted"
    CLOSED_NOT_CONVERTED = "Closed - Not Converted"


class CreateLeadRequest(BaseModel):
    """Request model for creating a Salesforce lead."""
    first_name: Optional[str] = None
    last_name: str
    company: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    website: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    lead_source: Optional[str] = None
    status: LeadStatus = LeadStatus.OPEN
    description: Optional[str] = None
    industry: Optional[str] = None
    annual_revenue: Optional[float] = None
    number_of_employees: Optional[int] = None
    custom_fields: dict[str, Any] = Field(default_factory=dict)


class LeadResponse(BaseModel):
    """Response model for Salesforce lead."""
    id: str
    first_name: Optional[str] = None
    last_name: str
    company: str
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    status: str
    owner_id: Optional[str] = None
    created_date: Optional[datetime] = None
    last_modified_date: Optional[datetime] = None
    is_converted: bool = False
    converted_contact_id: Optional[str] = None
    converted_account_id: Optional[str] = None
    converted_opportunity_id: Optional[str] = None


# Contact Models
class CreateContactRequest(BaseModel):
    """Request model for creating a Salesforce contact."""
    first_name: Optional[str] = None
    last_name: str
    account_id: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile_phone: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    mailing_street: Optional[str] = None
    mailing_city: Optional[str] = None
    mailing_state: Optional[str] = None
    mailing_postal_code: Optional[str] = None
    mailing_country: Optional[str] = None
    description: Optional[str] = None
    lead_source: Optional[str] = None
    custom_fields: dict[str, Any] = Field(default_factory=dict)


class ContactResponse(BaseModel):
    """Response model for Salesforce contact."""
    id: str
    first_name: Optional[str] = None
    last_name: str
    name: Optional[str] = None
    account_id: Optional[str] = None
    account_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    owner_id: Optional[str] = None
    created_date: Optional[datetime] = None
    last_modified_date: Optional[datetime] = None


# Opportunity Models
class OpportunityStage(str, Enum):
    """Standard Salesforce opportunity stages."""
    PROSPECTING = "Prospecting"
    QUALIFICATION = "Qualification"
    NEEDS_ANALYSIS = "Needs Analysis"
    VALUE_PROPOSITION = "Value Proposition"
    ID_DECISION_MAKERS = "Id. Decision Makers"
    PERCEPTION_ANALYSIS = "Perception Analysis"
    PROPOSAL_QUOTE = "Proposal/Price Quote"
    NEGOTIATION_REVIEW = "Negotiation/Review"
    CLOSED_WON = "Closed Won"
    CLOSED_LOST = "Closed Lost"


class UpdateOpportunityRequest(BaseModel):
    """Request model for updating a Salesforce opportunity."""
    name: Optional[str] = None
    stage_name: Optional[str] = None
    amount: Optional[float] = None
    close_date: Optional[datetime] = None
    probability: Optional[int] = Field(None, ge=0, le=100)
    description: Optional[str] = None
    next_step: Optional[str] = None
    lead_source: Optional[str] = None
    type: Optional[str] = None
    custom_fields: dict[str, Any] = Field(default_factory=dict)


class OpportunityResponse(BaseModel):
    """Response model for Salesforce opportunity."""
    id: str
    name: str
    account_id: Optional[str] = None
    account_name: Optional[str] = None
    stage_name: str
    amount: Optional[float] = None
    close_date: Optional[datetime] = None
    probability: Optional[int] = None
    is_closed: bool = False
    is_won: bool = False
    owner_id: Optional[str] = None
    created_date: Optional[datetime] = None
    last_modified_date: Optional[datetime] = None


# Task Models
class TaskPriority(str, Enum):
    """Salesforce task priority levels."""
    HIGH = "High"
    NORMAL = "Normal"
    LOW = "Low"


class TaskStatus(str, Enum):
    """Salesforce task statuses."""
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    WAITING = "Waiting on someone else"
    DEFERRED = "Deferred"


class AddTaskRequest(BaseModel):
    """Request model for adding a Salesforce task."""
    subject: str
    what_id: Optional[str] = None  # Related record (Account, Opportunity, etc.)
    who_id: Optional[str] = None  # Related person (Contact or Lead)
    owner_id: Optional[str] = None
    activity_date: Optional[datetime] = None
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.NOT_STARTED
    description: Optional[str] = None
    is_reminder_set: bool = False
    reminder_datetime: Optional[datetime] = None
    custom_fields: dict[str, Any] = Field(default_factory=dict)


class TaskResponse(BaseModel):
    """Response model for Salesforce task."""
    id: str
    subject: str
    what_id: Optional[str] = None
    who_id: Optional[str] = None
    owner_id: Optional[str] = None
    activity_date: Optional[datetime] = None
    priority: str
    status: str
    is_closed: bool = False
    created_date: Optional[datetime] = None


# Activity Models
class ActivityType(str, Enum):
    """Types of activities to log."""
    CALL = "Call"
    EMAIL = "Email"
    MEETING = "Meeting"
    OTHER = "Other"


class LogActivityRequest(BaseModel):
    """Request model for logging an activity in Salesforce."""
    subject: str
    what_id: Optional[str] = None  # Related record (Account, Opportunity, etc.)
    who_id: Optional[str] = None  # Related person (Contact or Lead)
    activity_type: ActivityType = ActivityType.CALL
    activity_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    description: Optional[str] = None
    status: str = "Completed"
    call_disposition: Optional[str] = None  # For call logging
    call_result: Optional[str] = None
    custom_fields: dict[str, Any] = Field(default_factory=dict)


class ActivityResponse(BaseModel):
    """Response model for Salesforce activity."""
    id: str
    subject: str
    what_id: Optional[str] = None
    who_id: Optional[str] = None
    activity_type: Optional[str] = None
    activity_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    status: str
    created_date: Optional[datetime] = None


# Search Models
class SearchRecordsRequest(BaseModel):
    """Request model for searching Salesforce records."""
    query: str
    sobject_types: list[str] = Field(
        default_factory=lambda: ["Lead", "Contact", "Account", "Opportunity"]
    )
    fields: Optional[list[str]] = None
    limit: int = Field(default=25, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class SearchResult(BaseModel):
    """Individual search result."""
    id: str
    sobject_type: str
    name: Optional[str] = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class SearchRecordsResponse(BaseModel):
    """Response model for Salesforce record search."""
    results: list[SearchResult]
    total_size: int
    done: bool = True


# Bulk API Models
class BulkOperation(str, Enum):
    """Bulk operation types."""
    INSERT = "insert"
    UPDATE = "update"
    UPSERT = "upsert"
    DELETE = "delete"


class BulkJobRequest(BaseModel):
    """Request model for creating a bulk job."""
    sobject_type: str
    operation: BulkOperation
    external_id_field: Optional[str] = None  # Required for upsert
    records: list[dict[str, Any]]


class BulkJobStatus(str, Enum):
    """Bulk job status values."""
    OPEN = "Open"
    UPLOAD_COMPLETE = "UploadComplete"
    IN_PROGRESS = "InProgress"
    JOB_COMPLETE = "JobComplete"
    ABORTED = "Aborted"
    FAILED = "Failed"


class BulkJobResponse(BaseModel):
    """Response model for bulk job."""
    job_id: str
    state: BulkJobStatus
    sobject_type: str
    operation: str
    created_by_id: Optional[str] = None
    created_date: Optional[datetime] = None
    system_modstamp: Optional[datetime] = None
    number_records_processed: int = 0
    number_records_failed: int = 0


class BulkJobResult(BaseModel):
    """Result of a bulk job operation."""
    job_id: str
    state: BulkJobStatus
    number_records_processed: int
    number_records_failed: int
    successful_records: list[dict[str, Any]] = Field(default_factory=list)
    failed_records: list[dict[str, Any]] = Field(default_factory=list)


# Field Mapping Models
class FieldMappingDirection(str, Enum):
    """Direction of field mapping."""
    INBOUND = "inbound"  # Salesforce -> Sales OS
    OUTBOUND = "outbound"  # Sales OS -> Salesforce
    BIDIRECTIONAL = "bidirectional"


class FieldMapping(BaseModel):
    """Mapping between Sales OS field and Salesforce field."""
    sales_os_field: str
    salesforce_field: str
    sobject_type: str
    direction: FieldMappingDirection = FieldMappingDirection.BIDIRECTIONAL
    transform: Optional[str] = None  # Optional transformation function name
    default_value: Optional[Any] = None
    is_required: bool = False


class FieldMappingConfig(BaseModel):
    """Configuration for field mappings per organization."""
    org_id: str
    mappings: list[FieldMapping] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# API Error Models
class SalesforceError(BaseModel):
    """Salesforce API error."""
    error_code: str
    message: str
    fields: Optional[list[str]] = None


class SalesforceAPIError(Exception):
    """Exception for Salesforce API errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        errors: Optional[list[SalesforceError]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.errors = errors or []
        super().__init__(self.message)
