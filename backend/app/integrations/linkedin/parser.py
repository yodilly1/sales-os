"""
LinkedIn URL Parser

Utilities for parsing and validating LinkedIn URLs.
Handles various URL formats for profiles, companies, posts, and other resources.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple
from urllib.parse import urlparse, parse_qs


class LinkedInResourceType(str, Enum):
    """Types of LinkedIn resources that can be identified from URLs"""
    PROFILE = "profile"
    COMPANY = "company"
    SCHOOL = "school"
    SHOWCASE = "showcase"
    POST = "post"
    ARTICLE = "article"
    JOB = "job"
    GROUP = "group"
    EVENT = "event"
    SALES_NAVIGATOR_PROFILE = "sales_navigator_profile"
    SALES_NAVIGATOR_COMPANY = "sales_navigator_company"
    SALES_NAVIGATOR_LEAD = "sales_navigator_lead"
    UNKNOWN = "unknown"


@dataclass
class ParsedLinkedInURL:
    """Result of parsing a LinkedIn URL"""
    original_url: str
    resource_type: LinkedInResourceType
    identifier: Optional[str] = None  # Username, company slug, etc.
    normalized_url: Optional[str] = None
    is_valid: bool = True
    error_message: Optional[str] = None
    metadata: Optional[dict] = None


class LinkedInURLParser:
    """
    Parser for LinkedIn URLs.

    Handles various URL formats:
    - Profile URLs: linkedin.com/in/username
    - Company URLs: linkedin.com/company/company-name
    - Sales Navigator URLs: linkedin.com/sales/lead/*, linkedin.com/sales/company/*
    - Post URLs: linkedin.com/posts/*, linkedin.com/feed/update/*
    - And more...
    """

    # Base LinkedIn domains
    LINKEDIN_DOMAINS = [
        "linkedin.com",
        "www.linkedin.com",
        "uk.linkedin.com",
        "de.linkedin.com",
        "fr.linkedin.com",
        # Add other country-specific domains as needed
    ]

    # URL patterns for different resource types
    PATTERNS = {
        LinkedInResourceType.PROFILE: [
            r"/in/([a-zA-Z0-9\-_%]+)/?",
            r"/pub/([a-zA-Z0-9\-_%]+)/?",
        ],
        LinkedInResourceType.COMPANY: [
            r"/company/([a-zA-Z0-9\-_%]+)/?",
            r"/school/([a-zA-Z0-9\-_%]+)/?",  # Schools are similar to companies
        ],
        LinkedInResourceType.SCHOOL: [
            r"/school/([a-zA-Z0-9\-_%]+)/?",
        ],
        LinkedInResourceType.SHOWCASE: [
            r"/showcase/([a-zA-Z0-9\-_%]+)/?",
        ],
        LinkedInResourceType.POST: [
            r"/posts/([a-zA-Z0-9\-_%]+)-activity-(\d+)",
            r"/feed/update/urn:li:activity:(\d+)",
            r"/feed/update/urn:li:share:(\d+)",
        ],
        LinkedInResourceType.ARTICLE: [
            r"/pulse/([a-zA-Z0-9\-_%]+)",
        ],
        LinkedInResourceType.JOB: [
            r"/jobs/view/(\d+)",
            r"/jobs/collections/recommended/\?currentJobId=(\d+)",
        ],
        LinkedInResourceType.GROUP: [
            r"/groups/(\d+)",
        ],
        LinkedInResourceType.EVENT: [
            r"/events/([a-zA-Z0-9\-_%]+)",
        ],
        LinkedInResourceType.SALES_NAVIGATOR_PROFILE: [
            r"/sales/lead/([a-zA-Z0-9\-_%,]+)",
            r"/sales/people/([a-zA-Z0-9\-_%,]+)",
        ],
        LinkedInResourceType.SALES_NAVIGATOR_COMPANY: [
            r"/sales/company/(\d+)",
        ],
        LinkedInResourceType.SALES_NAVIGATOR_LEAD: [
            r"/sales/lead/([a-zA-Z0-9\-_%,]+)",
        ],
    }

    @classmethod
    def parse(cls, url: str) -> ParsedLinkedInURL:
        """
        Parse a LinkedIn URL and extract information.

        Args:
            url: The URL to parse

        Returns:
            ParsedLinkedInURL with extracted information
        """
        if not url:
            return ParsedLinkedInURL(
                original_url=url,
                resource_type=LinkedInResourceType.UNKNOWN,
                is_valid=False,
                error_message="Empty URL provided",
            )

        # Clean and normalize the URL
        url = url.strip()

        # Handle URLs without scheme
        if not url.startswith(("http://", "https://")):
            if url.startswith("linkedin.com") or url.startswith("www.linkedin.com"):
                url = f"https://{url}"
            elif url.startswith("/"):
                url = f"https://www.linkedin.com{url}"

        # Parse the URL
        try:
            parsed = urlparse(url)
        except Exception as e:
            return ParsedLinkedInURL(
                original_url=url,
                resource_type=LinkedInResourceType.UNKNOWN,
                is_valid=False,
                error_message=f"Invalid URL format: {str(e)}",
            )

        # Check if it's a LinkedIn domain
        domain = parsed.netloc.lower()
        if not any(domain == d or domain.endswith(f".{d}") for d in cls.LINKEDIN_DOMAINS):
            return ParsedLinkedInURL(
                original_url=url,
                resource_type=LinkedInResourceType.UNKNOWN,
                is_valid=False,
                error_message=f"Not a LinkedIn URL: {domain}",
            )

        # Try to match against known patterns
        path = parsed.path
        for resource_type, patterns in cls.PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, path, re.IGNORECASE)
                if match:
                    identifier = match.group(1)
                    normalized = cls._normalize_url(resource_type, identifier)

                    # Extract additional metadata from query params
                    metadata = {}
                    if parsed.query:
                        query_params = parse_qs(parsed.query)
                        metadata["query_params"] = {
                            k: v[0] if len(v) == 1 else v
                            for k, v in query_params.items()
                        }

                    return ParsedLinkedInURL(
                        original_url=url,
                        resource_type=resource_type,
                        identifier=identifier,
                        normalized_url=normalized,
                        is_valid=True,
                        metadata=metadata if metadata else None,
                    )

        # No pattern matched
        return ParsedLinkedInURL(
            original_url=url,
            resource_type=LinkedInResourceType.UNKNOWN,
            is_valid=False,
            error_message="Could not identify LinkedIn resource type",
        )

    @classmethod
    def _normalize_url(cls, resource_type: LinkedInResourceType, identifier: str) -> str:
        """Generate a normalized URL for a resource"""
        base = "https://www.linkedin.com"

        url_templates = {
            LinkedInResourceType.PROFILE: f"{base}/in/{identifier}",
            LinkedInResourceType.COMPANY: f"{base}/company/{identifier}",
            LinkedInResourceType.SCHOOL: f"{base}/school/{identifier}",
            LinkedInResourceType.SHOWCASE: f"{base}/showcase/{identifier}",
            LinkedInResourceType.GROUP: f"{base}/groups/{identifier}",
            LinkedInResourceType.EVENT: f"{base}/events/{identifier}",
            LinkedInResourceType.JOB: f"{base}/jobs/view/{identifier}",
            LinkedInResourceType.ARTICLE: f"{base}/pulse/{identifier}",
            LinkedInResourceType.SALES_NAVIGATOR_PROFILE: f"{base}/sales/lead/{identifier}",
            LinkedInResourceType.SALES_NAVIGATOR_COMPANY: f"{base}/sales/company/{identifier}",
            LinkedInResourceType.SALES_NAVIGATOR_LEAD: f"{base}/sales/lead/{identifier}",
        }

        return url_templates.get(resource_type, f"{base}/{identifier}")

    @classmethod
    def is_profile_url(cls, url: str) -> bool:
        """Check if URL is a LinkedIn profile URL"""
        result = cls.parse(url)
        return result.resource_type == LinkedInResourceType.PROFILE

    @classmethod
    def is_company_url(cls, url: str) -> bool:
        """Check if URL is a LinkedIn company URL"""
        result = cls.parse(url)
        return result.resource_type in (
            LinkedInResourceType.COMPANY,
            LinkedInResourceType.SCHOOL,
        )

    @classmethod
    def is_sales_navigator_url(cls, url: str) -> bool:
        """Check if URL is a Sales Navigator URL"""
        result = cls.parse(url)
        return result.resource_type in (
            LinkedInResourceType.SALES_NAVIGATOR_PROFILE,
            LinkedInResourceType.SALES_NAVIGATOR_COMPANY,
            LinkedInResourceType.SALES_NAVIGATOR_LEAD,
        )

    @classmethod
    def extract_username(cls, url: str) -> Optional[str]:
        """Extract username from a profile URL"""
        result = cls.parse(url)
        if result.resource_type == LinkedInResourceType.PROFILE:
            return result.identifier
        return None

    @classmethod
    def extract_company_slug(cls, url: str) -> Optional[str]:
        """Extract company slug from a company URL"""
        result = cls.parse(url)
        if result.resource_type in (LinkedInResourceType.COMPANY, LinkedInResourceType.SCHOOL):
            return result.identifier
        return None

    @classmethod
    def normalize_profile_url(cls, url: str) -> Optional[str]:
        """Normalize a profile URL to standard format"""
        result = cls.parse(url)
        if result.resource_type == LinkedInResourceType.PROFILE:
            return result.normalized_url
        return None

    @classmethod
    def normalize_company_url(cls, url: str) -> Optional[str]:
        """Normalize a company URL to standard format"""
        result = cls.parse(url)
        if result.resource_type in (LinkedInResourceType.COMPANY, LinkedInResourceType.SCHOOL):
            return result.normalized_url
        return None

    @classmethod
    def convert_sales_nav_to_regular(cls, url: str) -> Optional[str]:
        """
        Convert a Sales Navigator URL to a regular LinkedIn URL if possible.

        Note: This may not always work as Sales Navigator uses different identifiers.
        """
        result = cls.parse(url)
        if result.resource_type == LinkedInResourceType.SALES_NAVIGATOR_PROFILE:
            # Sales Navigator URLs often contain the regular profile ID
            # Format: /sales/lead/ACwAAAxxxxxx,NAME
            identifier = result.identifier
            if identifier and "," in identifier:
                parts = identifier.split(",")
                # The first part might be the member ID
                # We can't directly convert, but we can extract what we have
                return None  # Would need API lookup to convert
        return None

    @classmethod
    def batch_parse(cls, urls: list[str]) -> list[ParsedLinkedInURL]:
        """Parse multiple URLs at once"""
        return [cls.parse(url) for url in urls]

    @classmethod
    def validate_and_normalize(cls, url: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate and normalize a LinkedIn URL.

        Returns:
            Tuple of (is_valid, normalized_url, error_message)
        """
        result = cls.parse(url)
        return (result.is_valid, result.normalized_url, result.error_message)


# Convenience functions
def parse_linkedin_url(url: str) -> ParsedLinkedInURL:
    """Parse a LinkedIn URL"""
    return LinkedInURLParser.parse(url)


def is_valid_linkedin_url(url: str) -> bool:
    """Check if a URL is a valid LinkedIn URL"""
    return LinkedInURLParser.parse(url).is_valid


def get_profile_username(url: str) -> Optional[str]:
    """Extract username from a LinkedIn profile URL"""
    return LinkedInURLParser.extract_username(url)


def get_company_slug(url: str) -> Optional[str]:
    """Extract company slug from a LinkedIn company URL"""
    return LinkedInURLParser.extract_company_slug(url)
