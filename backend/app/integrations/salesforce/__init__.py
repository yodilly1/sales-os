"""
Salesforce CRM integration for Sales OS.

This module provides a complete interface for integrating with Salesforce,
including OAuth2 authentication, CRUD operations, bulk data operations,
and custom field mapping.

Usage:
    from backend.app.integrations.salesforce import (
        SalesforceClient,
        SalesforceOAuth2Handler,
        SalesforceFieldMapper,
        SalesforceBulkAPI,
    )

    # Initialize OAuth2
    oauth_handler = SalesforceOAuth2Handler(config)
    auth_url = oauth_handler.get_authorization_url()

    # After OAuth2 callback
    tokens = await oauth_handler.exchange_code_for_tokens(code)
    credentials = oauth_handler.create_credentials(tokens)

    # Create client
    token_manager = SalesforceTokenManager(oauth_handler, credentials)
    client = SalesforceClient(token_manager)

    # Use client
    lead = await client.create_lead(CreateLeadRequest(...))
"""

from backend.app.integrations.salesforce.bulk import SalesforceBulkAPI
from backend.app.integrations.salesforce.client import SalesforceClient
from backend.app.integrations.salesforce.field_mapping import (
    SalesforceFieldMapper,
    TRANSFORM_REGISTRY,
)
from backend.app.integrations.salesforce.oauth2 import (
    SalesforceOAuth2Handler,
    SalesforceTokenManager,
)

__all__ = [
    "SalesforceClient",
    "SalesforceOAuth2Handler",
    "SalesforceTokenManager",
    "SalesforceFieldMapper",
    "SalesforceBulkAPI",
    "TRANSFORM_REGISTRY",
]
