"""
External Service Integrations for Sales OS

Provides connectors for:
- Email (SendGrid, SES)
- HubSpot CRM
- Avoma
"""

from . import email

__all__ = ["email"]
