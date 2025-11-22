"""
Prospect and Company Factories

Provides factory classes for creating prospect and company test data.
"""

from datetime import datetime, timezone
from typing import Any

import factory
from faker import Faker

fake = Faker()


class ProspectFactory(factory.Factory):
    """Factory for creating Prospect test data."""

    class Meta:
        model = dict

    id = factory.LazyFunction(lambda: f"prospect-{fake.uuid4()[:8]}")
    first_name = factory.LazyFunction(lambda: fake.first_name())
    last_name = factory.LazyFunction(lambda: fake.last_name())
    email = factory.LazyFunction(lambda: fake.email())
    company = factory.LazyFunction(lambda: fake.company())
    title = factory.LazyFunction(lambda: fake.random_element([
        "VP of Sales",
        "Chief Revenue Officer",
        "Sales Director",
        "Head of Business Development",
        "Account Executive",
        "Sales Manager",
    ]))
    phone = factory.LazyFunction(lambda: fake.phone_number())
    linkedin = factory.LazyFunction(lambda: f"https://linkedin.com/in/{fake.user_name()}")
    verified = False
    enrichment_data = None
    crm_synced = False
    crm_id = None
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc).isoformat())
    user_id = factory.LazyFunction(lambda: f"user-{fake.uuid4()[:8]}")

    @classmethod
    def create_verified(cls, **kwargs) -> dict[str, Any]:
        """Create a verified prospect with enrichment data."""
        enrichment = _generate_enrichment_data()
        return cls.create(
            verified=True,
            enrichment_data=enrichment,
            **kwargs
        )

    @classmethod
    def create_synced(cls, **kwargs) -> dict[str, Any]:
        """Create a prospect that's synced to CRM."""
        return cls.create(
            verified=True,
            crm_synced=True,
            crm_id=f"hubspot-{fake.uuid4()[:8]}",
            **kwargs
        )

    @classmethod
    def create_batch(cls, count: int = 5, **kwargs) -> list[dict[str, Any]]:
        """Create a batch of prospects."""
        return [cls.create(**kwargs) for _ in range(count)]


class CompanyFactory(factory.Factory):
    """Factory for creating Company test data."""

    class Meta:
        model = dict

    id = factory.LazyFunction(lambda: f"company-{fake.uuid4()[:8]}")
    name = factory.LazyFunction(lambda: fake.company())
    domain = factory.LazyFunction(lambda: fake.domain_name())
    industry = factory.LazyFunction(lambda: fake.random_element([
        "Technology",
        "Healthcare",
        "Finance",
        "Retail",
        "Manufacturing",
        "Professional Services",
        "Education",
        "Real Estate",
    ]))
    size = factory.LazyFunction(lambda: fake.random_element([
        "1-10",
        "11-50",
        "51-200",
        "201-500",
        "501-1000",
        "1001-5000",
        "5000+",
    ]))
    revenue = factory.LazyFunction(lambda: fake.random_element([
        "<$1M",
        "$1M-$5M",
        "$5M-$10M",
        "$10M-$50M",
        "$50M-$100M",
        "$100M-$500M",
        "$500M+",
    ]))
    location = factory.LazyFunction(lambda: f"{fake.city()}, {fake.state_abbr()}")
    description = factory.LazyFunction(lambda: fake.paragraph(nb_sentences=2))
    founded_year = factory.LazyFunction(lambda: fake.random_int(min=1990, max=2023))
    linkedin_url = factory.LazyFunction(lambda: f"https://linkedin.com/company/{fake.slug()}")
    website = factory.LazyFunction(lambda: f"https://{fake.domain_name()}")
    technologies = factory.LazyFunction(lambda: fake.random_elements(
        elements=["Salesforce", "HubSpot", "Slack", "AWS", "Azure", "Google Cloud"],
        length=fake.random_int(min=2, max=5),
        unique=True,
    ))
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def create_enterprise(cls, **kwargs) -> dict[str, Any]:
        """Create an enterprise-sized company."""
        return cls.create(
            size="1001-5000",
            revenue="$100M-$500M",
            **kwargs
        )

    @classmethod
    def create_smb(cls, **kwargs) -> dict[str, Any]:
        """Create a small/medium business company."""
        return cls.create(
            size="51-200",
            revenue="$5M-$10M",
            **kwargs
        )


def _generate_enrichment_data() -> dict[str, Any]:
    """Generate realistic enrichment data."""
    return {
        "email_verified": True,
        "email_deliverable": True,
        "phone_verified": fake.boolean(chance_of_getting_true=70),
        "linkedin_profile": f"https://linkedin.com/in/{fake.user_name()}",
        "twitter_profile": f"https://twitter.com/{fake.user_name()}" if fake.boolean() else None,
        "company_info": {
            "name": fake.company(),
            "domain": fake.domain_name(),
            "industry": fake.random_element(["Technology", "Healthcare", "Finance"]),
            "size": fake.random_element(["51-200", "201-500", "501-1000"]),
            "revenue": fake.random_element(["$10M-$50M", "$50M-$100M"]),
            "location": f"{fake.city()}, {fake.state_abbr()}",
            "founded_year": fake.random_int(min=2000, max=2020),
        },
        "social_profiles": {
            "linkedin": f"https://linkedin.com/in/{fake.user_name()}",
            "twitter": f"https://twitter.com/{fake.user_name()}" if fake.boolean() else None,
        },
        "work_history": [
            {
                "company": fake.company(),
                "title": fake.job(),
                "start_date": "2020-01",
                "end_date": None,
                "is_current": True,
            },
            {
                "company": fake.company(),
                "title": fake.job(),
                "start_date": "2017-06",
                "end_date": "2019-12",
                "is_current": False,
            },
        ],
        "education": [
            {
                "school": f"{fake.city()} University",
                "degree": fake.random_element(["MBA", "BS Computer Science", "BA Business"]),
                "year": fake.random_int(min=2005, max=2018),
            }
        ],
        "skills": fake.random_elements(
            elements=["Sales", "Leadership", "Strategy", "Negotiation", "CRM", "Analytics"],
            length=fake.random_int(min=3, max=6),
            unique=True,
        ),
        "enriched_at": datetime.now(timezone.utc).isoformat(),
        "data_source": "clearbit",
    }
