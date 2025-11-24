"""Export service for generating CSV files for Instantly and HeyReach."""

import csv
import io
import logging
from typing import Optional

from app.services.outreach.campaign_generator import OutreachCampaign, get_campaign

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting outreach campaigns to various formats."""

    # Instantly CSV columns
    INSTANTLY_COLUMNS = [
        "email",
        "first_name",
        "last_name",
        "company",
        "email_1_subject",
        "email_1_body",
        "email_2_subject",
        "email_2_body",
        "email_3_subject",
        "email_3_body",
    ]

    # HeyReach CSV columns
    HEYREACH_COLUMNS = [
        "linkedin_url",
        "first_name",
        "last_name",
        "company",
        "connection_message",
        "followup_1",
        "followup_2",
    ]

    def export_to_instantly(self, campaign: OutreachCampaign) -> str:
        """Export campaign to Instantly CSV format.

        Args:
            campaign: The outreach campaign to export.

        Returns:
            CSV string ready for download.
        """
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=self.INSTANTLY_COLUMNS)
        writer.writeheader()

        # Parse name
        name_parts = campaign.prospect_name.split()
        first_name = name_parts[0] if name_parts else ""
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        row = {
            "email": campaign.prospect_email or "",
            "first_name": first_name,
            "last_name": last_name,
            "company": campaign.company_name or "",
        }

        # Add emails
        emails = campaign.email_sequence.emails
        for i in range(3):
            if i < len(emails):
                row[f"email_{i+1}_subject"] = emails[i].subject
                row[f"email_{i+1}_body"] = emails[i].body
            else:
                row[f"email_{i+1}_subject"] = ""
                row[f"email_{i+1}_body"] = ""

        writer.writerow(row)

        return output.getvalue()

    def export_to_heyreach(self, campaign: OutreachCampaign) -> str:
        """Export campaign to HeyReach CSV format.

        Args:
            campaign: The outreach campaign to export.

        Returns:
            CSV string ready for download.
        """
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=self.HEYREACH_COLUMNS)
        writer.writeheader()

        # Parse name
        name_parts = campaign.prospect_name.split()
        first_name = name_parts[0] if name_parts else ""
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        linkedin_seq = campaign.linkedin_sequence

        row = {
            "linkedin_url": campaign.linkedin_url or "",
            "first_name": first_name,
            "last_name": last_name,
            "company": campaign.company_name or "",
            "connection_message": linkedin_seq.connection_request,
            "followup_1": linkedin_seq.followup_1,
            "followup_2": linkedin_seq.followup_2,
        }

        writer.writerow(row)

        return output.getvalue()

    def export_multiple_to_instantly(self, campaigns: list[OutreachCampaign]) -> str:
        """Export multiple campaigns to a single Instantly CSV.

        Args:
            campaigns: List of outreach campaigns to export.

        Returns:
            CSV string with all campaigns.
        """
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=self.INSTANTLY_COLUMNS)
        writer.writeheader()

        for campaign in campaigns:
            name_parts = campaign.prospect_name.split()
            first_name = name_parts[0] if name_parts else ""
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

            row = {
                "email": campaign.prospect_email or "",
                "first_name": first_name,
                "last_name": last_name,
                "company": campaign.company_name or "",
            }

            emails = campaign.email_sequence.emails
            for i in range(3):
                if i < len(emails):
                    row[f"email_{i+1}_subject"] = emails[i].subject
                    row[f"email_{i+1}_body"] = emails[i].body
                else:
                    row[f"email_{i+1}_subject"] = ""
                    row[f"email_{i+1}_body"] = ""

            writer.writerow(row)

        return output.getvalue()

    def export_multiple_to_heyreach(self, campaigns: list[OutreachCampaign]) -> str:
        """Export multiple campaigns to a single HeyReach CSV.

        Args:
            campaigns: List of outreach campaigns to export.

        Returns:
            CSV string with all campaigns.
        """
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=self.HEYREACH_COLUMNS)
        writer.writeheader()

        for campaign in campaigns:
            name_parts = campaign.prospect_name.split()
            first_name = name_parts[0] if name_parts else ""
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

            linkedin_seq = campaign.linkedin_sequence

            row = {
                "linkedin_url": campaign.linkedin_url or "",
                "first_name": first_name,
                "last_name": last_name,
                "company": campaign.company_name or "",
                "connection_message": linkedin_seq.connection_request,
                "followup_1": linkedin_seq.followup_1,
                "followup_2": linkedin_seq.followup_2,
            }

            writer.writerow(row)

        return output.getvalue()


def get_export_service() -> ExportService:
    """Get export service instance."""
    return ExportService()


def export_to_instantly(campaign_id: str) -> Optional[str]:
    """Export a campaign to Instantly CSV format.

    Args:
        campaign_id: The campaign ID to export.

    Returns:
        CSV string or None if campaign not found.
    """
    campaign = get_campaign(campaign_id)
    if not campaign:
        return None

    service = ExportService()
    return service.export_to_instantly(campaign)


def export_to_heyreach(campaign_id: str) -> Optional[str]:
    """Export a campaign to HeyReach CSV format.

    Args:
        campaign_id: The campaign ID to export.

    Returns:
        CSV string or None if campaign not found.
    """
    campaign = get_campaign(campaign_id)
    if not campaign:
        return None

    service = ExportService()
    return service.export_to_heyreach(campaign)
