"""Prompt builder for content generation."""

from typing import Any, Optional

from app.core.constants import BrandVoice
from app.models.content import (
    AudienceInfo,
    CompetitorInfo,
    ObjectionInfo,
    ProductInfo,
    SPICEDContext,
)


class ContentPromptBuilder:
    """Builder for creating prompts for content generation."""

    # Brand voice guidelines
    BRAND_VOICE_GUIDELINES = {
        BrandVoice.PROFESSIONAL: """
            - Use clear, confident language
            - Avoid jargon unless industry-standard
            - Focus on value and outcomes
            - Maintain a polished, business-appropriate tone
            - Use data and evidence to support claims
        """,
        BrandVoice.CONVERSATIONAL: """
            - Use friendly, approachable language
            - Write as if having a dialogue
            - Use contractions naturally
            - Keep sentences shorter and more dynamic
            - Include occasional questions to engage
        """,
        BrandVoice.TECHNICAL: """
            - Use precise technical terminology
            - Include specific details and specifications
            - Focus on functionality and capabilities
            - Reference technical standards when relevant
            - Be thorough but avoid unnecessary complexity
        """,
        BrandVoice.EXECUTIVE: """
            - Lead with business impact and ROI
            - Be concise and direct
            - Focus on strategic outcomes
            - Use metrics and KPIs
            - Emphasize competitive advantage
        """,
    }

    # WbD (Winning by Design) alignment guidelines
    WBD_GUIDELINES = """
    Follow the Winning by Design (WbD) SPICED methodology:
    - SITUATION: Understand and reflect the customer's current state
    - PAIN: Clearly articulate the problems and challenges they face
    - IMPACT: Quantify the business impact of these problems
    - CRITICAL EVENT: Identify timeline drivers and urgency factors
    - EXPECTED DECISION: Understand their decision process
    - DECISION CRITERIA: Address how they will evaluate solutions

    Align all content with customer-centric value selling principles.
    Focus on outcomes and business impact, not just features.
    """

    def build_system_prompt(
        self,
        content_type: str,
        brand_voice: BrandVoice = BrandVoice.PROFESSIONAL,
    ) -> str:
        """Build system prompt for content generation.

        Args:
            content_type: Type of content being generated.
            brand_voice: Brand voice to use.

        Returns:
            System prompt string.
        """
        voice_guidelines = self.BRAND_VOICE_GUIDELINES.get(
            brand_voice, self.BRAND_VOICE_GUIDELINES[BrandVoice.PROFESSIONAL]
        )

        return f"""You are an expert B2B sales content creator specializing in {content_type}s.
Your content follows the Winning by Design (WbD) methodology and SPICED framework.

{self.WBD_GUIDELINES}

Brand Voice Guidelines:
{voice_guidelines}

Content Quality Standards:
- Create compelling, professional content that drives action
- Use specific, concrete language rather than vague statements
- Include quantifiable benefits and outcomes where possible
- Structure content for easy scanning and consumption
- Ensure logical flow and clear transitions
- Tailor messaging to the specific audience
- Include clear calls to action

Output Format:
- Always return valid JSON matching the requested structure
- Do not include markdown code blocks in your response
- Ensure all required fields are populated
"""

    def build_deck_prompt(
        self,
        deck_type: str,
        goal: str,
        product_info: ProductInfo,
        audience: AudienceInfo,
        target_slides: int = 10,
        include_speaker_notes: bool = True,
        include_visual_suggestions: bool = True,
        spiced_context: Optional[SPICEDContext] = None,
        custom_instructions: Optional[str] = None,
    ) -> str:
        """Build prompt for deck generation.

        Args:
            deck_type: Type of deck (pitch, renewal, qbr).
            goal: Goal of the deck.
            product_info: Product information.
            audience: Target audience.
            target_slides: Target number of slides.
            include_speaker_notes: Whether to include speaker notes.
            include_visual_suggestions: Whether to include visual suggestions.
            spiced_context: Optional SPICED context.
            custom_instructions: Optional custom instructions.

        Returns:
            User prompt string.
        """
        deck_structure = self._get_deck_structure(deck_type)
        spiced_section = self._format_spiced_context(spiced_context)
        audience_section = self._format_audience(audience)
        product_section = self._format_product_info(product_info)

        return f"""Create a {deck_type} sales deck with the following specifications:

## Goal
{goal}

## Product Information
{product_section}

## Target Audience
{audience_section}

{spiced_section}

## Deck Requirements
- Total slides: {target_slides}
- Deck type: {deck_type}
- Include speaker notes: {include_speaker_notes}
- Include visual suggestions: {include_visual_suggestions}

## Suggested Structure
{deck_structure}

{f'## Additional Instructions{chr(10)}{custom_instructions}' if custom_instructions else ''}

## Output JSON Structure
Return a JSON object with this structure:
{{
    "title": "Deck title",
    "subtitle": "Optional subtitle",
    "estimated_duration_minutes": 30,
    "key_messages": ["message1", "message2", "message3"],
    "call_to_action": "Clear CTA",
    "slides": [
        {{
            "slide_number": 1,
            "title": "Slide title",
            "subtitle": "Optional subtitle",
            "content_type": "text|bullets|chart|image|quote",
            "main_content": "Content text or [array of bullets]",
            "speaker_notes": "Notes for presenter",
            "visual_suggestions": "Suggested visuals",
            "transition_note": "How to transition to next slide"
        }}
    ]
}}

Generate the complete deck now."""

    def build_proposal_prompt(
        self,
        proposal_type: str,
        goal: str,
        product_info: ProductInfo,
        audience: AudienceInfo,
        spiced_context: Optional[SPICEDContext] = None,
        custom_instructions: Optional[str] = None,
    ) -> str:
        """Build prompt for proposal generation.

        Args:
            proposal_type: Type of proposal (custom, templated).
            goal: Goal of the proposal.
            product_info: Product information.
            audience: Target audience.
            spiced_context: Optional SPICED context.
            custom_instructions: Optional custom instructions.

        Returns:
            User prompt string.
        """
        spiced_section = self._format_spiced_context(spiced_context)
        audience_section = self._format_audience(audience)
        product_section = self._format_product_info(product_info)

        return f"""Create a {proposal_type} sales proposal with the following specifications:

## Goal
{goal}

## Product Information
{product_section}

## Target Audience
{audience_section}

{spiced_section}

## Proposal Requirements
- Type: {proposal_type}
- Style: Professional, compelling, action-oriented
- Focus: Customer outcomes and value

{f'## Additional Instructions{chr(10)}{custom_instructions}' if custom_instructions else ''}

## Output JSON Structure
Return a JSON object with this structure:
{{
    "title": "Proposal title",
    "executive_summary": "Compelling executive summary paragraph",
    "sections": [
        {{
            "section_number": 1,
            "title": "Section title",
            "content": "Section content (markdown supported)",
            "subsections": [
                {{"title": "Subsection", "content": "Content"}}
            ]
        }}
    ],
    "pricing_table": {{
        "items": [
            {{"name": "Item", "description": "Desc", "price": "$X,XXX"}}
        ],
        "total": "$XX,XXX",
        "notes": "Pricing notes"
    }},
    "terms_and_conditions": "Standard terms",
    "next_steps": ["Step 1", "Step 2", "Step 3"],
    "validity_period": "30 days",
    "signature_block": {{
        "company": "Company name",
        "prepared_by": "Name",
        "date": "Date"
    }}
}}

Include these sections:
1. Executive Summary
2. Understanding Your Challenges (SPICED-aligned)
3. Proposed Solution
4. Implementation Approach
5. Investment & ROI
6. Why Choose Us
7. Next Steps

Generate the complete proposal now."""

    def build_one_pager_prompt(
        self,
        one_pager_type: str,
        goal: str,
        product_info: ProductInfo,
        audience: AudienceInfo,
        case_study_data: Optional[dict[str, Any]] = None,
        spiced_context: Optional[SPICEDContext] = None,
        custom_instructions: Optional[str] = None,
    ) -> str:
        """Build prompt for one-pager generation.

        Args:
            one_pager_type: Type of one-pager (product, solution, case_study).
            goal: Goal of the one-pager.
            product_info: Product information.
            audience: Target audience.
            case_study_data: Optional case study data.
            spiced_context: Optional SPICED context.
            custom_instructions: Optional custom instructions.

        Returns:
            User prompt string.
        """
        spiced_section = self._format_spiced_context(spiced_context)
        audience_section = self._format_audience(audience)
        product_section = self._format_product_info(product_info)

        case_study_section = ""
        if case_study_data and one_pager_type == "case_study":
            case_study_section = f"""
## Case Study Data
- Customer: {case_study_data.get('customer_name', 'Customer')}
- Industry: {case_study_data.get('industry', 'N/A')}
- Challenge: {case_study_data.get('challenge', 'N/A')}
- Solution: {case_study_data.get('solution', 'N/A')}
- Results: {case_study_data.get('results', 'N/A')}
- Quote: {case_study_data.get('quote', 'N/A')}
"""

        output_structure = self._get_one_pager_output_structure(one_pager_type)

        return f"""Create a {one_pager_type} one-pager with the following specifications:

## Goal
{goal}

## Product Information
{product_section}

## Target Audience
{audience_section}

{spiced_section}
{case_study_section}

## One-Pager Requirements
- Type: {one_pager_type}
- Format: Single page, scannable, impactful
- Focus: Key messages that drive action

{f'## Additional Instructions{chr(10)}{custom_instructions}' if custom_instructions else ''}

## Output JSON Structure
{output_structure}

Generate the complete one-pager now."""

    def build_battlecard_prompt(
        self,
        battlecard_type: str,
        goal: str,
        product_info: ProductInfo,
        audience: AudienceInfo,
        competitors: Optional[list[CompetitorInfo]] = None,
        objections: Optional[list[ObjectionInfo]] = None,
        spiced_context: Optional[SPICEDContext] = None,
        custom_instructions: Optional[str] = None,
    ) -> str:
        """Build prompt for battlecard generation.

        Args:
            battlecard_type: Type of battlecard (competitive, objection).
            goal: Goal of the battlecard.
            product_info: Product information.
            audience: Target audience.
            competitors: Optional competitor information.
            objections: Optional objection information.
            spiced_context: Optional SPICED context.
            custom_instructions: Optional custom instructions.

        Returns:
            User prompt string.
        """
        spiced_section = self._format_spiced_context(spiced_context)
        audience_section = self._format_audience(audience)
        product_section = self._format_product_info(product_info)

        competitor_section = ""
        if competitors and battlecard_type == "competitive":
            competitor_section = "## Competitor Information\n"
            for comp in competitors:
                competitor_section += f"""
### {comp.name}
- Description: {comp.description or 'N/A'}
- Strengths: {', '.join(comp.strengths) if comp.strengths else 'N/A'}
- Weaknesses: {', '.join(comp.weaknesses) if comp.weaknesses else 'N/A'}
- Pricing: {comp.pricing or 'N/A'}
- Common Objections: {', '.join(comp.common_objections) if comp.common_objections else 'N/A'}
"""

        objection_section = ""
        if objections and battlecard_type == "objection":
            objection_section = "## Objections to Address\n"
            for obj in objections:
                objection_section += f"""
- Objection: "{obj.objection}"
  - Category: {obj.category or 'General'}
  - Frequency: {obj.frequency or 'N/A'}
  - Context: {obj.context or 'N/A'}
"""

        output_structure = self._get_battlecard_output_structure(battlecard_type)

        return f"""Create a {battlecard_type} battlecard with the following specifications:

## Goal
{goal}

## Product Information
{product_section}

## Target Audience
{audience_section}

{spiced_section}
{competitor_section}
{objection_section}

## Battlecard Requirements
- Type: {battlecard_type}
- Purpose: Equip sales team with competitive intelligence and responses
- Format: Quick-reference, actionable

{f'## Additional Instructions{chr(10)}{custom_instructions}' if custom_instructions else ''}

## Output JSON Structure
{output_structure}

Generate the complete battlecard now."""

    def _get_deck_structure(self, deck_type: str) -> str:
        """Get suggested deck structure based on type."""
        structures = {
            "pitch": """
1. Title Slide
2. The Challenge (Customer Pain Points)
3. Market Landscape / Why Now
4. Our Solution Overview
5. How It Works
6. Key Benefits & Value
7. Customer Success / Social Proof
8. Differentiation
9. Investment & ROI
10. Call to Action & Next Steps
""",
            "renewal": """
1. Title Slide
2. Partnership Overview & Timeline
3. Key Achievements & Wins
4. Usage & Adoption Metrics
5. Value Delivered (ROI)
6. What's New & Roadmap
7. Expansion Opportunities
8. Renewal Terms & Investment
""",
            "qbr": """
1. Title Slide
2. Executive Summary
3. Performance Scorecard
4. Goals vs. Actuals
5. Key Wins & Successes
6. Challenges & Solutions
7. Usage Analytics
8. Product Updates & Roadmap
9. Recommendations
10. Goals for Next Quarter
11. Success Plan
12. Q&A / Next Steps
""",
        }
        return structures.get(deck_type, structures["pitch"])

    def _get_one_pager_output_structure(self, one_pager_type: str) -> str:
        """Get output structure for one-pager based on type."""
        base_structure = """Return a JSON object with this structure:
{
    "title": "One-pager title",
    "headline": "Compelling headline",
    "subheadline": "Supporting subheadline",
    "overview": "Brief overview paragraph",
    "key_points": [
        {"title": "Point 1", "description": "Description"},
        {"title": "Point 2", "description": "Description"},
        {"title": "Point 3", "description": "Description"}
    ],
    "benefits": ["Benefit 1", "Benefit 2", "Benefit 3"],
    "proof_points": [
        {"stat": "50%", "description": "reduction in X"},
        {"quote": "Quote text", "attribution": "Name, Title"}
    ],
    "call_to_action": "Clear CTA",
    "contact_info": {"email": "email", "phone": "phone", "website": "url"}"""

        if one_pager_type == "case_study":
            return base_structure + """,
    "customer_name": "Customer Name",
    "challenge": "Challenge description",
    "solution": "Solution description",
    "results": [
        {"metric": "50%", "description": "improvement in X"}
    ],
    "customer_quote": "Customer testimonial"
}"""
        return base_structure + "\n}"

    def _get_battlecard_output_structure(self, battlecard_type: str) -> str:
        """Get output structure for battlecard based on type."""
        if battlecard_type == "competitive":
            return """Return a JSON object with this structure:
{
    "title": "Battlecard title",
    "competitor_name": "Competitor Name",
    "competitor_overview": "Brief competitor overview",
    "their_strengths": ["Strength 1", "Strength 2"],
    "their_weaknesses": ["Weakness 1", "Weakness 2"],
    "our_advantages": ["Advantage 1", "Advantage 2"],
    "head_to_head": [
        {"feature": "Feature", "us": "Our capability", "them": "Their capability"}
    ],
    "competitive_positioning": "How to position against them",
    "trap_questions": [
        {"question": "Question to ask", "why": "Why this favors us"}
    ],
    "landmines": [
        {"topic": "Topic", "how_to_handle": "How to handle"}
    ],
    "win_themes": ["Theme 1", "Theme 2"]
}"""
        else:  # objection
            return """Return a JSON object with this structure:
{
    "title": "Battlecard title",
    "category": "Objection category",
    "objections": [
        {"objection": "The objection", "response": "The response"}
    ],
    "quick_responses": [
        {"objection": "Short objection", "response": "One-liner response"}
    ],
    "detailed_responses": [
        {"objection": "Objection", "context": "When it arises", "response": "Detailed response", "follow_up": "Follow-up question"}
    ],
    "prevention_tips": ["How to prevent this objection"],
    "related_proof_points": ["Evidence to support responses"]
}"""

    def _format_spiced_context(self, spiced: Optional[SPICEDContext]) -> str:
        """Format SPICED context for prompt."""
        if not spiced:
            return ""

        sections = []
        if spiced.situation:
            sections.append(f"- Situation: {spiced.situation}")
        if spiced.pain:
            sections.append(f"- Pain: {spiced.pain}")
        if spiced.impact:
            sections.append(f"- Impact: {spiced.impact}")
        if spiced.critical_event:
            sections.append(f"- Critical Event: {spiced.critical_event}")
        if spiced.expected_decision:
            sections.append(f"- Expected Decision: {spiced.expected_decision}")
        if spiced.decision_criteria:
            sections.append(f"- Decision Criteria: {spiced.decision_criteria}")

        if sections:
            return "## SPICED Context (WbD Framework)\n" + "\n".join(sections)
        return ""

    def _format_audience(self, audience: AudienceInfo) -> str:
        """Format audience info for prompt."""
        sections = [f"- Audience Type: {audience.audience_type.value}"]

        if audience.company_name:
            sections.append(f"- Company: {audience.company_name}")
        if audience.industry:
            sections.append(f"- Industry: {audience.industry}")
        if audience.company_size:
            sections.append(f"- Company Size: {audience.company_size}")
        if audience.pain_points:
            sections.append(f"- Pain Points: {', '.join(audience.pain_points)}")
        if audience.priorities:
            sections.append(f"- Priorities: {', '.join(audience.priorities)}")
        if audience.decision_criteria:
            sections.append(f"- Decision Criteria: {', '.join(audience.decision_criteria)}")
        if audience.stakeholders:
            sections.append(f"- Key Stakeholders: {', '.join(audience.stakeholders)}")

        return "\n".join(sections)

    def _format_product_info(self, product: ProductInfo) -> str:
        """Format product info for prompt."""
        sections = [
            f"- Name: {product.name}",
            f"- Description: {product.description}",
        ]

        if product.key_features:
            sections.append(f"- Key Features: {', '.join(product.key_features)}")
        if product.value_propositions:
            sections.append(f"- Value Propositions: {', '.join(product.value_propositions)}")
        if product.pricing_info:
            sections.append(f"- Pricing: {product.pricing_info}")
        if product.differentiators:
            sections.append(f"- Differentiators: {', '.join(product.differentiators)}")
        if product.use_cases:
            sections.append(f"- Use Cases: {', '.join(product.use_cases)}")
        if product.customer_segments:
            sections.append(f"- Target Segments: {', '.join(product.customer_segments)}")

        return "\n".join(sections)
