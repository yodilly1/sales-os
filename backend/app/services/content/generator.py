"""Content generator service for creating sales content using Claude."""

import logging
import time
from pathlib import Path
from typing import Any, Optional, Union

from app.core.config import get_settings
from app.core.constants import CONTENT_CATEGORIES, DECK_SLIDE_COUNTS, ContentStatus, ContentType
from app.models.content import (
    AudienceInfo,
    BattlecardContent,
    ContentGenerationRequest,
    ContentGenerationResponse,
    ContentMetadata,
    DeckContent,
    DeckSlide,
    OnePagerContent,
    ProductInfo,
    ProposalContent,
    ProposalSection,
)
from app.services.claude_client import ClaudeClient
from app.services.content.prompts import ContentPromptBuilder

logger = logging.getLogger(__name__)


class ContentGenerator:
    """Service for generating sales content using Claude AI."""

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        """Initialize the content generator.

        Args:
            claude_client: Optional Claude client instance.
        """
        self.claude_client = claude_client or ClaudeClient()
        self.prompt_builder = ContentPromptBuilder()
        self.settings = get_settings()

    async def generate(
        self, request: ContentGenerationRequest
    ) -> ContentGenerationResponse:
        """Generate content based on the request.

        Args:
            request: Content generation request with all parameters.

        Returns:
            ContentGenerationResponse with generated content.
        """
        start_time = time.time()

        # Route to appropriate generator based on content type
        if request.content_type in CONTENT_CATEGORIES["decks"]:
            content = await self._generate_deck(request)
        elif request.content_type in CONTENT_CATEGORIES["proposals"]:
            content = await self._generate_proposal(request)
        elif request.content_type in CONTENT_CATEGORIES["one_pagers"]:
            content = await self._generate_one_pager(request)
        elif request.content_type in CONTENT_CATEGORIES["battlecards"]:
            content = await self._generate_battlecard(request)
        else:
            raise ValueError(f"Unsupported content type: {request.content_type}")

        generation_time_ms = int((time.time() - start_time) * 1000)

        # Create metadata
        metadata = ContentMetadata(
            content_type=request.content_type,
            status=ContentStatus.COMPLETED,
            generation_time_ms=generation_time_ms,
            model_used=self.settings.claude_model,
        )

        # Calculate WbD alignment score
        wbd_score = self._calculate_wbd_alignment(content, request)

        return ContentGenerationResponse(
            metadata=metadata,
            content=content,
            wbd_alignment_score=wbd_score,
            suggestions=self._generate_suggestions(content, request),
        )

    async def _generate_deck(
        self, request: ContentGenerationRequest
    ) -> DeckContent:
        """Generate a sales deck.

        Args:
            request: Content generation request.

        Returns:
            DeckContent with slides and metadata.
        """
        # Determine deck type
        deck_type_map = {
            ContentType.DECK_PITCH: "pitch",
            ContentType.DECK_RENEWAL: "renewal",
            ContentType.DECK_QBR: "qbr",
        }
        deck_type = deck_type_map[request.content_type]

        # Get target slide count
        target_slides = request.max_slides or DECK_SLIDE_COUNTS.get(
            request.content_type, 10
        )

        # Build prompt
        system_prompt = self.prompt_builder.build_system_prompt(
            content_type="deck",
            brand_voice=request.brand_voice,
        )

        user_prompt = self.prompt_builder.build_deck_prompt(
            deck_type=deck_type,
            goal=request.goal,
            product_info=request.product_info,
            audience=request.audience,
            target_slides=target_slides,
            include_speaker_notes=request.include_speaker_notes,
            include_visual_suggestions=request.include_visual_suggestions,
            spiced_context=request.spiced_context,
            custom_instructions=request.custom_instructions,
        )

        # Generate content
        json_content, response = await self.claude_client.generate_json(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=8192,
        )

        # Parse into DeckContent
        slides = [
            DeckSlide(
                slide_number=s.get("slide_number", i + 1),
                title=s.get("title", ""),
                subtitle=s.get("subtitle"),
                content_type=s.get("content_type", "text"),
                main_content=s.get("main_content", ""),
                speaker_notes=s.get("speaker_notes") if request.include_speaker_notes else None,
                visual_suggestions=s.get("visual_suggestions") if request.include_visual_suggestions else None,
                transition_note=s.get("transition_note"),
            )
            for i, s in enumerate(json_content.get("slides", []))
        ]

        return DeckContent(
            title=json_content.get("title", f"{request.product_info.name} - {deck_type.title()} Deck"),
            subtitle=json_content.get("subtitle"),
            deck_type=deck_type,
            slides=slides,
            total_slides=len(slides),
            estimated_duration_minutes=json_content.get("estimated_duration_minutes", len(slides) * 3),
            key_messages=json_content.get("key_messages", []),
            call_to_action=json_content.get("call_to_action", "Schedule a follow-up discussion"),
        )

    async def _generate_proposal(
        self, request: ContentGenerationRequest
    ) -> ProposalContent:
        """Generate a proposal.

        Args:
            request: Content generation request.

        Returns:
            ProposalContent with sections.
        """
        proposal_type_map = {
            ContentType.PROPOSAL_CUSTOM: "custom",
            ContentType.PROPOSAL_TEMPLATED: "templated",
        }
        proposal_type = proposal_type_map[request.content_type]

        # Build prompt
        system_prompt = self.prompt_builder.build_system_prompt(
            content_type="proposal",
            brand_voice=request.brand_voice,
        )

        user_prompt = self.prompt_builder.build_proposal_prompt(
            proposal_type=proposal_type,
            goal=request.goal,
            product_info=request.product_info,
            audience=request.audience,
            spiced_context=request.spiced_context,
            custom_instructions=request.custom_instructions,
        )

        # Generate content
        json_content, response = await self.claude_client.generate_json(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=8192,
        )

        # Parse into ProposalContent
        sections = [
            ProposalSection(
                section_number=s.get("section_number", i + 1),
                title=s.get("title", ""),
                content=s.get("content", ""),
                subsections=s.get("subsections"),
            )
            for i, s in enumerate(json_content.get("sections", []))
        ]

        return ProposalContent(
            title=json_content.get("title", f"Proposal for {request.audience.company_name or 'Your Organization'}"),
            proposal_type=proposal_type,
            executive_summary=json_content.get("executive_summary", ""),
            sections=sections,
            pricing_table=json_content.get("pricing_table"),
            terms_and_conditions=json_content.get("terms_and_conditions"),
            next_steps=json_content.get("next_steps", []),
            validity_period=json_content.get("validity_period", "30 days"),
            signature_block=json_content.get("signature_block"),
        )

    async def _generate_one_pager(
        self, request: ContentGenerationRequest
    ) -> OnePagerContent:
        """Generate a one-pager.

        Args:
            request: Content generation request.

        Returns:
            OnePagerContent with all fields.
        """
        one_pager_type_map = {
            ContentType.ONE_PAGER_PRODUCT: "product",
            ContentType.ONE_PAGER_SOLUTION: "solution",
            ContentType.ONE_PAGER_CASE_STUDY: "case_study",
        }
        one_pager_type = one_pager_type_map[request.content_type]

        # Build prompt
        system_prompt = self.prompt_builder.build_system_prompt(
            content_type="one_pager",
            brand_voice=request.brand_voice,
        )

        user_prompt = self.prompt_builder.build_one_pager_prompt(
            one_pager_type=one_pager_type,
            goal=request.goal,
            product_info=request.product_info,
            audience=request.audience,
            case_study_data=request.case_study_data,
            spiced_context=request.spiced_context,
            custom_instructions=request.custom_instructions,
        )

        # Generate content
        json_content, response = await self.claude_client.generate_json(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=4096,
        )

        return OnePagerContent(
            title=json_content.get("title", f"{request.product_info.name} Overview"),
            one_pager_type=one_pager_type,
            headline=json_content.get("headline", ""),
            subheadline=json_content.get("subheadline"),
            overview=json_content.get("overview", ""),
            key_points=json_content.get("key_points", []),
            benefits=json_content.get("benefits", []),
            proof_points=json_content.get("proof_points"),
            call_to_action=json_content.get("call_to_action", "Learn more"),
            contact_info=json_content.get("contact_info"),
            # Case study specific
            customer_name=json_content.get("customer_name"),
            challenge=json_content.get("challenge"),
            solution=json_content.get("solution"),
            results=json_content.get("results"),
            customer_quote=json_content.get("customer_quote"),
        )

    async def _generate_battlecard(
        self, request: ContentGenerationRequest
    ) -> BattlecardContent:
        """Generate a battlecard.

        Args:
            request: Content generation request.

        Returns:
            BattlecardContent with competitive or objection handling info.
        """
        battlecard_type_map = {
            ContentType.BATTLECARD_COMPETITIVE: "competitive",
            ContentType.BATTLECARD_OBJECTION: "objection",
        }
        battlecard_type = battlecard_type_map[request.content_type]

        # Build prompt
        system_prompt = self.prompt_builder.build_system_prompt(
            content_type="battlecard",
            brand_voice=request.brand_voice,
        )

        user_prompt = self.prompt_builder.build_battlecard_prompt(
            battlecard_type=battlecard_type,
            goal=request.goal,
            product_info=request.product_info,
            audience=request.audience,
            competitors=request.competitors,
            objections=request.objections,
            spiced_context=request.spiced_context,
            custom_instructions=request.custom_instructions,
        )

        # Generate content
        json_content, response = await self.claude_client.generate_json(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=6144,
        )

        return BattlecardContent(
            title=json_content.get("title", f"{request.product_info.name} Battlecard"),
            battlecard_type=battlecard_type,
            # Competitive fields
            competitor_name=json_content.get("competitor_name"),
            competitor_overview=json_content.get("competitor_overview"),
            their_strengths=json_content.get("their_strengths"),
            their_weaknesses=json_content.get("their_weaknesses"),
            our_advantages=json_content.get("our_advantages"),
            head_to_head=json_content.get("head_to_head"),
            competitive_positioning=json_content.get("competitive_positioning"),
            trap_questions=json_content.get("trap_questions"),
            landmines=json_content.get("landmines"),
            win_themes=json_content.get("win_themes"),
            # Objection handling fields
            objections=json_content.get("objections"),
            category=json_content.get("category"),
            quick_responses=json_content.get("quick_responses"),
            detailed_responses=json_content.get("detailed_responses"),
            prevention_tips=json_content.get("prevention_tips"),
            related_proof_points=json_content.get("related_proof_points"),
        )

    def _calculate_wbd_alignment(
        self,
        content: Union[DeckContent, ProposalContent, OnePagerContent, BattlecardContent],
        request: ContentGenerationRequest,
    ) -> float:
        """Calculate WbD (Winning by Design) methodology alignment score.

        Args:
            content: Generated content.
            request: Original request with SPICED context.

        Returns:
            Alignment score from 0 to 1.
        """
        score = 0.5  # Base score

        # Bonus for having SPICED context
        if request.spiced_context:
            spiced = request.spiced_context
            if spiced.situation:
                score += 0.1
            if spiced.pain:
                score += 0.1
            if spiced.impact:
                score += 0.1
            if spiced.critical_event:
                score += 0.05
            if spiced.expected_decision:
                score += 0.05
            if spiced.decision_criteria:
                score += 0.1

        return min(score, 1.0)

    def _generate_suggestions(
        self,
        content: Union[DeckContent, ProposalContent, OnePagerContent, BattlecardContent],
        request: ContentGenerationRequest,
    ) -> list[str]:
        """Generate improvement suggestions based on content and request.

        Args:
            content: Generated content.
            request: Original request.

        Returns:
            List of improvement suggestions.
        """
        suggestions = []

        # Check for missing SPICED context
        if not request.spiced_context:
            suggestions.append(
                "Consider adding SPICED context (Situation, Pain, Impact, Critical Event, "
                "Expected Decision, Decision Criteria) for more targeted content."
            )
        elif request.spiced_context:
            spiced = request.spiced_context
            if not spiced.pain:
                suggestions.append("Adding specific pain points will make the content more compelling.")
            if not spiced.impact:
                suggestions.append("Including business impact metrics will strengthen your value proposition.")

        # Check audience specificity
        if not request.audience.company_name:
            suggestions.append(
                "Personalizing with the prospect's company name will increase engagement."
            )

        if not request.audience.pain_points:
            suggestions.append(
                "Adding known audience pain points will make the content more relevant."
            )

        # Content-specific suggestions
        if isinstance(content, DeckContent):
            if content.total_slides > 15:
                suggestions.append(
                    "Consider condensing the deck - shorter presentations often have higher engagement."
                )
            if not content.call_to_action:
                suggestions.append("Ensure you have a clear call to action on the final slide.")

        return suggestions


# Convenience functions for direct use
async def generate_pitch_deck(
    product_info: ProductInfo,
    goal: str,
    audience: Optional[AudienceInfo] = None,
    **kwargs,
) -> ContentGenerationResponse:
    """Generate a pitch deck.

    Args:
        product_info: Product information.
        goal: Goal of the deck.
        audience: Optional audience info.
        **kwargs: Additional request parameters.

    Returns:
        ContentGenerationResponse with deck content.
    """
    generator = ContentGenerator()
    request = ContentGenerationRequest(
        content_type=ContentType.DECK_PITCH,
        goal=goal,
        product_info=product_info,
        audience=audience or AudienceInfo(),
        **kwargs,
    )
    return await generator.generate(request)


async def generate_proposal(
    product_info: ProductInfo,
    goal: str,
    audience: Optional[AudienceInfo] = None,
    custom: bool = True,
    **kwargs,
) -> ContentGenerationResponse:
    """Generate a proposal.

    Args:
        product_info: Product information.
        goal: Goal of the proposal.
        audience: Optional audience info.
        custom: Whether to generate custom or templated proposal.
        **kwargs: Additional request parameters.

    Returns:
        ContentGenerationResponse with proposal content.
    """
    generator = ContentGenerator()
    content_type = ContentType.PROPOSAL_CUSTOM if custom else ContentType.PROPOSAL_TEMPLATED
    request = ContentGenerationRequest(
        content_type=content_type,
        goal=goal,
        product_info=product_info,
        audience=audience or AudienceInfo(),
        **kwargs,
    )
    return await generator.generate(request)


async def generate_one_pager(
    product_info: ProductInfo,
    goal: str,
    one_pager_type: str = "product",
    audience: Optional[AudienceInfo] = None,
    **kwargs,
) -> ContentGenerationResponse:
    """Generate a one-pager.

    Args:
        product_info: Product information.
        goal: Goal of the one-pager.
        one_pager_type: Type: 'product', 'solution', or 'case_study'.
        audience: Optional audience info.
        **kwargs: Additional request parameters.

    Returns:
        ContentGenerationResponse with one-pager content.
    """
    generator = ContentGenerator()
    type_map = {
        "product": ContentType.ONE_PAGER_PRODUCT,
        "solution": ContentType.ONE_PAGER_SOLUTION,
        "case_study": ContentType.ONE_PAGER_CASE_STUDY,
    }
    request = ContentGenerationRequest(
        content_type=type_map.get(one_pager_type, ContentType.ONE_PAGER_PRODUCT),
        goal=goal,
        product_info=product_info,
        audience=audience or AudienceInfo(),
        **kwargs,
    )
    return await generator.generate(request)


async def generate_battlecard(
    product_info: ProductInfo,
    goal: str,
    battlecard_type: str = "competitive",
    audience: Optional[AudienceInfo] = None,
    **kwargs,
) -> ContentGenerationResponse:
    """Generate a battlecard.

    Args:
        product_info: Product information.
        goal: Goal of the battlecard.
        battlecard_type: Type: 'competitive' or 'objection'.
        audience: Optional audience info.
        **kwargs: Additional request parameters.

    Returns:
        ContentGenerationResponse with battlecard content.
    """
    generator = ContentGenerator()
    type_map = {
        "competitive": ContentType.BATTLECARD_COMPETITIVE,
        "objection": ContentType.BATTLECARD_OBJECTION,
    }
    request = ContentGenerationRequest(
        content_type=type_map.get(battlecard_type, ContentType.BATTLECARD_COMPETITIVE),
        goal=goal,
        product_info=product_info,
        audience=audience or AudienceInfo(),
        **kwargs,
    )
    return await generator.generate(request)
