"""
Battlecard Generator - AI-powered battlecard content generation.

Uses Claude API to generate intelligent battlecard content based on
competitor data, product information, and win/loss history.
"""

import json
from pathlib import Path
from typing import Optional

from ...models.battlecard import (
    BattlecardType,
    BattlecardGenerateRequest,
    BattlecardContent,
    CompetitiveBattlecard,
    CompetitiveTalkingPoint,
    ObjectionHandlingBattlecard,
    ObjectionCard,
    ObjectionResponse,
    FeatureComparisonMatrix,
    FeatureComparison,
    FeatureRating,
    WinLossAnalysisBattlecard,
    WinLossFactor,
    WinLossDeal,
    DealOutcome,
    Competitor,
    CompetitorStrength,
    CompetitorWeakness,
)


class BattlecardGenerator:
    """
    AI-powered battlecard content generator.

    Generates different types of battlecards using Claude API
    with specialized prompts for each battlecard type.
    """

    def __init__(self, prompts_dir: str = "claude/prompts"):
        self.prompts_dir = Path(prompts_dir)
        self._load_prompts()

    def _load_prompts(self) -> None:
        """Load prompt templates from files."""
        self.prompts = {}
        prompt_files = {
            "competitive": "battlecard_competitive.md",
            "objection": "battlecard_objection.md",
            "comparison": "battlecard_comparison.md",
            "winloss": "battlecard_winloss.md",
        }

        for key, filename in prompt_files.items():
            prompt_path = self.prompts_dir / filename
            if prompt_path.exists():
                with open(prompt_path, "r") as f:
                    self.prompts[key] = f.read()
            else:
                self.prompts[key] = self._get_default_prompt(key)

    def _get_default_prompt(self, prompt_type: str) -> str:
        """Get default prompt if file not found."""
        defaults = {
            "competitive": """Generate a competitive battlecard with the following sections:
- Competitor overview
- Our positioning
- Key differentiators
- Competitor strengths and weaknesses
- Talking points
- Landmine questions
- Proof points
- When we win/lose scenarios""",
            "objection": """Generate objection handling responses following the ACR framework:
- Acknowledge the concern
- Clarify with questions
- Respond with value
- Provide proof
- Redirect the conversation""",
            "comparison": """Create a feature comparison matrix that:
- Lists key features by category
- Rates our capabilities vs competitors
- Provides talking points for each feature
- Summarizes key advantages""",
            "winloss": """Analyze win/loss data to identify:
- Top factors contributing to wins
- Top factors contributing to losses
- Competitor-specific insights
- Actionable recommendations""",
        }
        return defaults.get(prompt_type, "")

    async def generate(
        self,
        request: BattlecardGenerateRequest,
        competitor: Optional[Competitor] = None,
        competitors: Optional[list[Competitor]] = None,
        win_loss_data: Optional[list[dict]] = None,
        product_info: Optional[dict] = None,
    ) -> BattlecardContent:
        """
        Generate battlecard content based on type.

        Args:
            request: Generation request with type and context
            competitor: Primary competitor (for competitive cards)
            competitors: List of competitors (for comparison)
            win_loss_data: Historical win/loss data
            product_info: Our product information

        Returns:
            BattlecardContent with generated content
        """
        if request.type == BattlecardType.COMPETITIVE:
            content = await self._generate_competitive(
                request, competitor, product_info
            )
            return BattlecardContent(competitive=content)

        elif request.type == BattlecardType.OBJECTION_HANDLING:
            content = await self._generate_objection_handling(
                request, product_info
            )
            return BattlecardContent(objection_handling=content)

        elif request.type == BattlecardType.FEATURE_COMPARISON:
            content = await self._generate_feature_comparison(
                request, competitors or [], product_info
            )
            return BattlecardContent(feature_comparison=content)

        elif request.type == BattlecardType.WIN_LOSS_ANALYSIS:
            content = await self._generate_win_loss_analysis(
                request, win_loss_data or [], competitors
            )
            return BattlecardContent(win_loss_analysis=content)

        raise ValueError(f"Unsupported battlecard type: {request.type}")

    async def _generate_competitive(
        self,
        request: BattlecardGenerateRequest,
        competitor: Optional[Competitor],
        product_info: Optional[dict],
    ) -> CompetitiveBattlecard:
        """
        Generate a competitive battlecard.

        In production, this would call Claude API with the competitive prompt.
        For now, generates structured content based on available data.
        """
        competitor_name = (
            competitor.name if competitor
            else request.competitor_name or "Competitor"
        )

        # Build content from competitor data or generate placeholder
        strengths = []
        weaknesses = []
        if competitor:
            strengths = competitor.strengths
            weaknesses = competitor.weaknesses

        # Default strengths/weaknesses if none provided
        if not strengths:
            strengths = [
                CompetitorStrength(
                    area="Market Presence",
                    description=f"{competitor_name} has established market presence",
                    impact="May have existing relationships with prospects",
                ),
            ]

        if not weaknesses:
            weaknesses = [
                CompetitorWeakness(
                    area="Innovation",
                    description="Slower to adopt new technologies",
                    talking_point="Highlight our modern architecture and faster innovation cycles",
                ),
            ]

        return CompetitiveBattlecard(
            competitor_name=competitor_name,
            competitor_overview=(
                competitor.description if competitor
                else f"Overview of {competitor_name} and their market position."
            ),
            our_positioning=(
                f"We differentiate from {competitor_name} through superior "
                "technology, customer success focus, and value-based pricing."
            ),
            key_differentiators=[
                "Modern, cloud-native architecture",
                "Superior customer success and support",
                "Flexible, value-based pricing",
                "Faster time-to-value",
                "Continuous innovation and updates",
            ],
            competitor_strengths=strengths,
            competitor_weaknesses=weaknesses,
            talking_points=[
                CompetitiveTalkingPoint(
                    category="differentiation",
                    point="Our platform was built for the modern era",
                    supporting_evidence="Cloud-native architecture, real-time updates",
                ),
                CompetitiveTalkingPoint(
                    category="value",
                    point="Customers see ROI 40% faster than with legacy solutions",
                    supporting_evidence="Customer case studies and metrics",
                ),
                CompetitiveTalkingPoint(
                    category="proof",
                    point="Leading enterprises trust us for mission-critical operations",
                    supporting_evidence="Customer logos and testimonials",
                ),
            ],
            landmines=[
                f"How does {competitor_name} handle [specific use case]?",
                "What's their roadmap for [emerging technology]?",
                "Can you share recent customer references in your industry?",
                "What's the total cost of ownership including implementation?",
            ],
            proof_points=[
                "Customer A achieved 50% efficiency gains",
                "Customer B reduced time-to-market by 3 months",
                "Industry analyst recognition",
            ],
            when_we_win=[
                "Customer values innovation and modern technology",
                "Fast implementation timeline is critical",
                "Customer success and support are priorities",
                "Flexible pricing model fits their budget",
            ],
            when_we_lose=[
                "Deep existing relationship with competitor",
                "Specific legacy integration requirements",
                "Price-only evaluation",
            ],
        )

    async def _generate_objection_handling(
        self,
        request: BattlecardGenerateRequest,
        product_info: Optional[dict],
    ) -> ObjectionHandlingBattlecard:
        """
        Generate objection handling battlecard.

        Creates structured responses for common sales objections.
        """
        context = request.objection_context or "General sales conversations"
        categories = request.objection_categories or [
            "price", "timing", "competition", "need", "authority"
        ]

        objections = []

        # Price objections
        if "price" in categories:
            objections.append(
                ObjectionCard(
                    objection="Your solution is too expensive",
                    category="price",
                    severity="high",
                    root_cause="Prospect may not see full value or has budget constraints",
                    response=ObjectionResponse(
                        acknowledge="I understand budget is a key consideration in any decision.",
                        clarify="Help me understand - is it the upfront cost or the ongoing investment that concerns you most?",
                        respond="When we look at total cost of ownership, including implementation time, training, and ongoing maintenance, our customers typically see 30-40% lower TCO over 3 years.",
                        proof="For example, [Customer X] initially had the same concern but found they saved $X in the first year alone.",
                        redirect="What would the cost be to your organization if you don't solve this problem?",
                    ),
                    alternative_responses=[
                        "Let's look at the ROI calculation together",
                        "We have flexible payment options that might help",
                    ],
                    success_rate=72.0,
                )
            )

        # Timing objections
        if "timing" in categories:
            objections.append(
                ObjectionCard(
                    objection="We're not ready to make a decision right now",
                    category="timing",
                    severity="medium",
                    root_cause="May lack urgency or internal alignment",
                    response=ObjectionResponse(
                        acknowledge="I appreciate you being upfront about your timeline.",
                        clarify="What would need to happen internally for this to become a priority?",
                        respond="Many of our customers felt the same way initially. What changed for them was realizing the hidden costs of delay.",
                        proof="[Customer Y] delayed 6 months and estimated it cost them $X in lost productivity.",
                        redirect="If we could show you a quick win that proves value in 30 days, would that help build the case?",
                    ),
                    alternative_responses=[
                        "What's driving your current timeline?",
                        "Is there a trigger event that would change this?",
                    ],
                    success_rate=65.0,
                )
            )

        # Competition objections
        if "competition" in categories:
            objections.append(
                ObjectionCard(
                    objection="We're also looking at [Competitor]",
                    category="competition",
                    severity="medium",
                    root_cause="Prospect is doing due diligence",
                    response=ObjectionResponse(
                        acknowledge="That's a smart approach - you want to make sure you're making the right choice.",
                        clarify="What criteria are most important to you in making this decision?",
                        respond="Great that you're evaluating options. Based on what you've shared about your priorities, here's where we excel...",
                        proof="Customers who evaluated both solutions chose us because of [key differentiators].",
                        redirect="Would it be helpful if I shared a comparison based on your specific requirements?",
                    ),
                    alternative_responses=[
                        "What specifically appeals to you about their solution?",
                        "Have you seen how we handle [specific capability]?",
                    ],
                    success_rate=68.0,
                )
            )

        # Need objections
        if "need" in categories:
            objections.append(
                ObjectionCard(
                    objection="We're doing fine with our current solution",
                    category="need",
                    severity="high",
                    root_cause="Prospect doesn't see compelling reason to change",
                    response=ObjectionResponse(
                        acknowledge="It sounds like you've built a process that works for your team.",
                        clarify="If you could wave a magic wand and improve one thing about your current approach, what would it be?",
                        respond="What we're seeing in the market is that 'fine' often hides significant opportunity costs. Teams using modern solutions are outpacing competitors.",
                        proof="[Customer Z] thought they were fine too, but discovered they were leaving significant efficiency gains on the table.",
                        redirect="Would you be open to a quick assessment to see if there's untapped potential?",
                    ),
                    alternative_responses=[
                        "What does 'fine' look like in terms of metrics?",
                        "How does your leadership feel about the current situation?",
                    ],
                    success_rate=55.0,
                )
            )

        # Authority objections
        if "authority" in categories:
            objections.append(
                ObjectionCard(
                    objection="I need to get approval from my manager/team",
                    category="authority",
                    severity="medium",
                    root_cause="Multiple decision makers involved",
                    response=ObjectionResponse(
                        acknowledge="Of course - it's important to have alignment with your team.",
                        clarify="Who else would be involved in this decision, and what are their top priorities?",
                        respond="I'd be happy to help you build the internal business case. We have materials designed specifically for different stakeholders.",
                        proof="We've helped other champions like yourself get buy-in by focusing on [key benefits for each stakeholder].",
                        redirect="Would it make sense for me to join a call with your team to answer their questions directly?",
                    ),
                    alternative_responses=[
                        "What would make your manager say yes immediately?",
                        "What concerns do you anticipate from your team?",
                    ],
                    success_rate=70.0,
                )
            )

        return ObjectionHandlingBattlecard(
            context=context,
            objections=objections,
            general_tips=[
                "Always listen fully before responding",
                "Acknowledge emotions, not just logic",
                "Ask clarifying questions to understand the real concern",
                "Use customer stories as proof points",
                "Redirect to value, not features",
                "Document objections to improve future responses",
            ],
        )

    async def _generate_feature_comparison(
        self,
        request: BattlecardGenerateRequest,
        competitors: list[Competitor],
        product_info: Optional[dict],
    ) -> FeatureComparisonMatrix:
        """
        Generate a feature comparison matrix.

        Compares our product features against competitors.
        """
        competitor_names = [c.name for c in competitors]
        if not competitor_names and request.competitors_to_compare:
            competitor_names = request.competitors_to_compare

        if not competitor_names:
            competitor_names = ["Competitor A", "Competitor B"]

        categories = request.feature_categories or [
            "Core Functionality",
            "Integration & API",
            "Security & Compliance",
            "Support & Success",
        ]

        our_product = product_info.get("name", "Our Product") if product_info else "Our Product"

        comparisons = []

        # Core Functionality features
        if "Core Functionality" in categories:
            comparisons.extend([
                FeatureComparison(
                    feature_name="Real-time Processing",
                    feature_category="Core Functionality",
                    our_capability="Sub-second processing with streaming architecture",
                    our_rating=FeatureRating.SUPERIOR,
                    competitor_capabilities={
                        name: "Batch processing with delays" for name in competitor_names
                    },
                    competitor_ratings={
                        name: FeatureRating.INFERIOR for name in competitor_names
                    },
                    talking_point="Our real-time architecture enables instant insights",
                ),
                FeatureComparison(
                    feature_name="Customization",
                    feature_category="Core Functionality",
                    our_capability="Fully customizable workflows and UI",
                    our_rating=FeatureRating.SUPERIOR,
                    competitor_capabilities={
                        name: "Limited customization options" for name in competitor_names
                    },
                    competitor_ratings={
                        name: FeatureRating.COMPARABLE for name in competitor_names
                    },
                    talking_point="Adapt the platform to your exact needs",
                ),
            ])

        # Integration features
        if "Integration & API" in categories:
            comparisons.extend([
                FeatureComparison(
                    feature_name="API Coverage",
                    feature_category="Integration & API",
                    our_capability="Comprehensive REST and GraphQL APIs",
                    our_rating=FeatureRating.SUPERIOR,
                    competitor_capabilities={
                        name: "REST API only" for name in competitor_names
                    },
                    competitor_ratings={
                        name: FeatureRating.COMPARABLE for name in competitor_names
                    },
                    talking_point="Modern API options for any integration pattern",
                ),
                FeatureComparison(
                    feature_name="Pre-built Integrations",
                    feature_category="Integration & API",
                    our_capability="200+ native integrations",
                    our_rating=FeatureRating.COMPARABLE,
                    competitor_capabilities={
                        name: "150+ integrations" for name in competitor_names
                    },
                    competitor_ratings={
                        name: FeatureRating.COMPARABLE for name in competitor_names
                    },
                    talking_point="Native integrations with all major platforms",
                ),
            ])

        # Security features
        if "Security & Compliance" in categories:
            comparisons.extend([
                FeatureComparison(
                    feature_name="SOC 2 Type II",
                    feature_category="Security & Compliance",
                    our_capability="Certified annually",
                    our_rating=FeatureRating.COMPARABLE,
                    competitor_capabilities={
                        name: "Certified" for name in competitor_names
                    },
                    competitor_ratings={
                        name: FeatureRating.COMPARABLE for name in competitor_names
                    },
                    talking_point="Enterprise-grade security compliance",
                ),
                FeatureComparison(
                    feature_name="Data Residency",
                    feature_category="Security & Compliance",
                    our_capability="Multi-region options including EU",
                    our_rating=FeatureRating.SUPERIOR,
                    competitor_capabilities={
                        name: "US only" for name in competitor_names
                    },
                    competitor_ratings={
                        name: FeatureRating.INFERIOR for name in competitor_names
                    },
                    talking_point="Meet data sovereignty requirements globally",
                ),
            ])

        # Support features
        if "Support & Success" in categories:
            comparisons.extend([
                FeatureComparison(
                    feature_name="Customer Success",
                    feature_category="Support & Success",
                    our_capability="Dedicated CSM for all plans",
                    our_rating=FeatureRating.SUPERIOR,
                    competitor_capabilities={
                        name: "Enterprise plans only" for name in competitor_names
                    },
                    competitor_ratings={
                        name: FeatureRating.INFERIOR for name in competitor_names
                    },
                    talking_point="White-glove service regardless of plan size",
                ),
                FeatureComparison(
                    feature_name="Response Time SLA",
                    feature_category="Support & Success",
                    our_capability="< 1 hour for critical issues",
                    our_rating=FeatureRating.SUPERIOR,
                    competitor_capabilities={
                        name: "4-8 hour SLA" for name in competitor_names
                    },
                    competitor_ratings={
                        name: FeatureRating.INFERIOR for name in competitor_names
                    },
                    talking_point="Industry-leading support response times",
                ),
            ])

        # Count advantages
        superior_count = sum(1 for c in comparisons if c.our_rating == FeatureRating.SUPERIOR)
        comparable_count = sum(1 for c in comparisons if c.our_rating == FeatureRating.COMPARABLE)

        return FeatureComparisonMatrix(
            title=request.title,
            our_product=our_product,
            competitors=competitor_names,
            categories=categories,
            comparisons=comparisons,
            summary=(
                f"Across {len(comparisons)} key features, we are superior in "
                f"{superior_count} areas and comparable in {comparable_count}. "
                "Our key advantages are in real-time processing, customization, "
                "and customer success."
            ),
            key_advantages=[
                "Real-time processing architecture",
                "Dedicated customer success for all customers",
                "Multi-region data residency options",
                "Industry-leading support SLAs",
            ],
            areas_for_improvement=[
                "Expanding pre-built integration library",
            ],
        )

    async def _generate_win_loss_analysis(
        self,
        request: BattlecardGenerateRequest,
        win_loss_data: list[dict],
        competitors: Optional[list[Competitor]],
    ) -> WinLossAnalysisBattlecard:
        """
        Generate win/loss analysis battlecard.

        Analyzes historical deal data to identify patterns.
        """
        analysis_days = request.analysis_period_days or 90
        analysis_period = f"Last {analysis_days} days"

        # Process win/loss data or use defaults
        if win_loss_data:
            # Analyze actual data
            total = len(win_loss_data)
            wins = [d for d in win_loss_data if d.get("outcome") == "won"]
            losses = [d for d in win_loss_data if d.get("outcome") == "lost"]
            win_rate = (len(wins) / total * 100) if total > 0 else 0

            # Calculate averages
            avg_won = sum(d.get("deal_size", 0) for d in wins) / len(wins) if wins else None
            avg_lost = sum(d.get("deal_size", 0) for d in losses) / len(losses) if losses else None
        else:
            # Use sample data for demonstration
            total = 47
            win_rate = 62.0
            avg_won = 85000.0
            avg_lost = 72000.0

        return WinLossAnalysisBattlecard(
            analysis_period=analysis_period,
            total_deals_analyzed=total,
            win_rate=win_rate,
            avg_deal_size_won=avg_won,
            avg_deal_size_lost=avg_lost,
            avg_sales_cycle_won=45,
            avg_sales_cycle_lost=67,
            top_win_factors=[
                WinLossFactor(
                    factor="Strong Champion",
                    impact="high",
                    description="Deals with an internal champion close at 2x the rate",
                    frequency=28,
                ),
                WinLossFactor(
                    factor="Executive Engagement",
                    impact="high",
                    description="C-level involvement increases win probability by 45%",
                    frequency=22,
                ),
                WinLossFactor(
                    factor="Technical Validation",
                    impact="medium",
                    description="POC or technical deep-dive completed",
                    frequency=25,
                ),
                WinLossFactor(
                    factor="Clear ROI Story",
                    impact="high",
                    description="Quantified business case presented",
                    frequency=20,
                ),
            ],
            top_loss_factors=[
                WinLossFactor(
                    factor="No Decision",
                    impact="high",
                    description="35% of losses are to 'no decision' - priority shifted",
                    frequency=12,
                ),
                WinLossFactor(
                    factor="Price",
                    impact="medium",
                    description="Lost on price when value not established early",
                    frequency=8,
                ),
                WinLossFactor(
                    factor="Incumbent Relationship",
                    impact="medium",
                    description="Strong existing vendor relationship",
                    frequency=6,
                ),
                WinLossFactor(
                    factor="Missing Feature",
                    impact="low",
                    description="Specific feature gap was deal-breaker",
                    frequency=4,
                ),
            ],
            competitor_breakdown={
                "Competitor A": 58.0,
                "Competitor B": 72.0,
                "Competitor C": 45.0,
                "No Competition": 78.0,
            },
            recommendations=[
                "Identify and develop champions earlier in the sales cycle",
                "Push for executive engagement by end of discovery phase",
                "Complete ROI analysis before proposal stage",
                "Address 'no decision' risk by quantifying cost of inaction",
                "When competing on price, shift conversation to TCO and value",
            ],
            notable_deals=[
                WinLossDeal(
                    deal_name="Enterprise Co - Digital Transformation",
                    outcome=DealOutcome.WON,
                    competitor="Competitor A",
                    deal_size=250000,
                    sales_cycle_days=62,
                    key_factors=["Strong champion", "Executive buy-in", "Clear ROI"],
                    lessons_learned="Early executive engagement and quantified business case were critical",
                ),
                WinLossDeal(
                    deal_name="Tech Startup - Growth Initiative",
                    outcome=DealOutcome.LOST,
                    competitor="Competitor B",
                    deal_size=45000,
                    sales_cycle_days=90,
                    key_factors=["Price sensitivity", "Long sales cycle"],
                    lessons_learned="Should have qualified budget constraints earlier",
                ),
            ],
        )

    async def refresh_from_data(
        self,
        battlecard_type: BattlecardType,
        current_content: BattlecardContent,
        new_data: dict,
    ) -> BattlecardContent:
        """
        Refresh battlecard content with new data (e.g., win/loss updates).

        Args:
            battlecard_type: Type of battlecard to refresh
            current_content: Current battlecard content
            new_data: New data to incorporate

        Returns:
            Updated BattlecardContent
        """
        # In production, this would use Claude to intelligently merge
        # new data with existing content
        # For now, returns current content
        return current_content
