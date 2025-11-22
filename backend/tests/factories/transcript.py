"""
Transcript and SPICED Analysis Factories

Provides factory classes for creating transcript and SPICED test data.
"""

from datetime import datetime, timezone
from typing import Any

import factory
from faker import Faker

fake = Faker()


class TranscriptFactory(factory.Factory):
    """Factory for creating Transcript test data."""

    class Meta:
        model = dict

    id = factory.LazyFunction(lambda: f"transcript-{fake.uuid4()[:8]}")
    title = factory.LazyFunction(lambda: f"Sales Call - {fake.company()}")
    content = factory.LazyFunction(lambda: _generate_transcript_content())
    duration = factory.LazyFunction(lambda: fake.random_int(min=300, max=3600))
    participants = factory.LazyFunction(lambda: ["Sales Rep", "Prospect"])
    status = "processed"
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc).isoformat())
    user_id = factory.LazyFunction(lambda: f"user-{fake.uuid4()[:8]}")

    @classmethod
    def create_with_spiced(cls, **kwargs) -> dict[str, Any]:
        """Create a transcript with associated SPICED analysis."""
        transcript = cls.create(**kwargs)
        spiced = SpicedAnalysisFactory.create(transcript_id=transcript["id"])
        return {"transcript": transcript, "spiced": spiced}


class SpicedAnalysisFactory(factory.Factory):
    """Factory for creating SPICED Analysis test data."""

    class Meta:
        model = dict

    id = factory.LazyFunction(lambda: f"spiced-{fake.uuid4()[:8]}")
    transcript_id = factory.LazyFunction(lambda: f"transcript-{fake.uuid4()[:8]}")
    situation = factory.LazyFunction(lambda: _generate_situation())
    problem = factory.LazyFunction(lambda: _generate_problem())
    implication = factory.LazyFunction(lambda: _generate_implication())
    critical_event = factory.LazyFunction(lambda: _generate_critical_event())
    decision = factory.LazyFunction(lambda: _generate_decision())
    confidence = factory.LazyFunction(lambda: round(fake.random.uniform(0.7, 0.99), 2))
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc).isoformat())


def _generate_transcript_content() -> str:
    """Generate realistic sales call transcript content."""
    prospect_name = fake.name()
    company = fake.company()
    problem = fake.bs()

    return f"""
Sales Rep: Hi {prospect_name}, thanks for taking the time to chat today. How are you doing?

{prospect_name}: I'm doing well, thanks for asking. I've been looking forward to this call.

Sales Rep: Great to hear! So I understand you're with {company}. Can you tell me a bit about your current situation?

{prospect_name}: Sure. We're a growing team of about {fake.random_int(min=10, max=500)} people, and we're really struggling with {problem}. It's become a major pain point for us.

Sales Rep: I can definitely understand that frustration. What specific problems is this causing for your team?

{prospect_name}: Well, our sales team is spending way too much time on manual data entry. I'd estimate it's taking up about {fake.random_int(min=10, max=30)} hours per week across the team.

Sales Rep: That's significant. What are the implications if this continues?

{prospect_name}: We're missing opportunities, our forecasting is unreliable, and honestly, team morale is starting to suffer. People didn't sign up to do data entry all day.

Sales Rep: That makes total sense. Is there any specific event or deadline that's driving the urgency here?

{prospect_name}: Yes, actually. We have our {fake.random_element(['Q4 planning', 'annual review', 'board meeting', 'funding round'])} coming up in {fake.random_int(min=30, max=90)} days, and we need to have this sorted by then.

Sales Rep: Got it. And who else is involved in making this decision?

{prospect_name}: It would be myself and our {fake.random_element(['CRO', 'CEO', 'VP of Operations', 'Head of Sales'])}. We both need to sign off on any new tools.

Sales Rep: Perfect. Let me show you how Sales OS can help address these challenges...
"""


def _generate_situation() -> str:
    """Generate a realistic situation description."""
    situations = [
        "Growing sales team struggling with manual processes and data management",
        "Company expanding rapidly but sales operations not scaling efficiently",
        "Team experiencing friction between sales and operations departments",
        "Organization looking to modernize their sales tech stack",
        "Sales team spending excessive time on administrative tasks instead of selling",
    ]
    return fake.random_element(situations)


def _generate_problem() -> str:
    """Generate a realistic problem description."""
    problems = [
        "Spending 20+ hours per week on manual data entry across the sales team",
        "Inconsistent data in CRM leading to unreliable forecasting",
        "Sales reps lack visibility into prospect engagement and history",
        "No standardized process for qualifying and scoring leads",
        "Manual content creation taking time away from customer-facing activities",
    ]
    return fake.random_element(problems)


def _generate_implication() -> str:
    """Generate a realistic implication description."""
    implications = [
        "Missing revenue targets, low team morale, high rep turnover",
        "Lost deals due to slow follow-up and lack of prospect intelligence",
        "Inability to scale sales operations without adding headcount",
        "Executive team lacks confidence in sales forecasts and pipeline data",
        "Competitive disadvantage as prospects expect personalized, timely engagement",
    ]
    return fake.random_element(implications)


def _generate_critical_event() -> str:
    """Generate a realistic critical event description."""
    events = [
        "End of quarter review with board in 30 days",
        "Annual planning cycle starting in 6 weeks",
        "New fiscal year budget decisions due in 45 days",
        "Major product launch requiring sales enablement",
        "Series B funding round closing requiring improved metrics",
    ]
    return fake.random_element(events)


def _generate_decision() -> str:
    """Generate a realistic decision description."""
    decisions = [
        "Need solution implemented before end of quarter to impact Q4 results",
        "Decision committee includes VP Sales and CRO, both need to approve",
        "Budget approved, need to select vendor within 2 weeks",
        "Proof of concept required before full deployment decision",
        "Looking to make final decision after reviewing 3 vendor demos",
    ]
    return fake.random_element(decisions)
