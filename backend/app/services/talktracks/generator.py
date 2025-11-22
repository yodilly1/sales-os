"""
Talk Track Generator Service

Core service for generating WbD methodology-aligned talk tracks and scripts
using Claude AI for persona-based customization and industry-specific language.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from backend.app.models.talktrack import (
    TalkTrack,
    TalkTrackRequest,
    TalkTrackResponse,
    ScriptType,
    PersonaType,
    Industry,
    DealStage,
    ScriptSection,
    DiscoveryQuestion,
    ObjectionResponse,
    SPICEDElement,
)

logger = logging.getLogger(__name__)


class TalkTrackGenerator:
    """
    Generates talk tracks and scripts aligned with WbD methodology.

    Supports:
    - Discovery call scripts with SPICED questions
    - Demo scripts focused on value delivery
    - Objection response playbooks
    - Closing conversation guides
    - Follow-up call frameworks
    """

    def __init__(self, claude_client=None):
        """
        Initialize the talk track generator.

        Args:
            claude_client: Claude API client for AI-powered generation
        """
        self.claude_client = claude_client
        self._prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        """Load the talk track generation prompt template."""
        prompt_path = Path(__file__).parent.parent.parent.parent.parent / "claude" / "prompts" / "talktrack_generation.md"
        try:
            if prompt_path.exists():
                return prompt_path.read_text()
        except Exception as e:
            logger.warning(f"Could not load prompt template: {e}")
        return self._get_default_prompt_template()

    def _get_default_prompt_template(self) -> str:
        """Return default prompt template if file not found."""
        return """You are an expert sales coach specializing in the Winning by Design (WbD) methodology and SPICED framework.

Generate a {script_type} talk track with the following context:
- Target Persona: {persona}
- Industry: {industry}
- Deal Stage: {deal_stage}
- Tone: {tone}

{context_section}

Create a natural, conversational script that:
1. Follows WbD best practices
2. Incorporates SPICED discovery elements where appropriate
3. Is customized for the specific persona and industry
4. Includes coaching notes for delivery
5. Has clear transitions between sections

Output the script in structured JSON format."""

    async def generate(self, request: TalkTrackRequest) -> TalkTrackResponse:
        """
        Generate a talk track based on the request parameters.

        Args:
            request: Talk track generation request with all context

        Returns:
            TalkTrackResponse with primary talk track and optional variants
        """
        logger.info(f"Generating {request.script_type.value} talk track for {request.persona.value} in {request.industry.value}")

        # Generate primary talk track
        primary = await self._generate_talk_track(request)

        # Generate variants if requested
        variants = []
        if request.generate_variants:
            variants = await self._generate_variants(request, primary)

        return TalkTrackResponse(
            primary=primary,
            variants=variants,
            generation_metadata={
                "script_type": request.script_type.value,
                "persona": request.persona.value,
                "industry": request.industry.value,
                "variants_generated": len(variants),
            }
        )

    async def _generate_talk_track(
        self,
        request: TalkTrackRequest,
        variant_id: Optional[str] = None
    ) -> TalkTrack:
        """Generate a single talk track."""
        if self.claude_client:
            return await self._generate_with_claude(request, variant_id)
        return self._generate_template_based(request, variant_id)

    async def _generate_with_claude(
        self,
        request: TalkTrackRequest,
        variant_id: Optional[str] = None
    ) -> TalkTrack:
        """Generate talk track using Claude AI."""
        prompt = self._build_prompt(request)

        try:
            response = await self.claude_client.generate(
                prompt=prompt,
                system="You are an expert sales coach. Generate structured talk tracks in JSON format.",
                max_tokens=4000,
            )
            return self._parse_claude_response(response, request, variant_id)
        except Exception as e:
            logger.error(f"Claude generation failed: {e}")
            return self._generate_template_based(request, variant_id)

    def _build_prompt(self, request: TalkTrackRequest) -> str:
        """Build the prompt for Claude."""
        context_parts = []

        if request.prospect:
            context_parts.append(f"Prospect: {request.prospect.name or 'Unknown'}, {request.prospect.title or ''} at {request.prospect.company or ''}")
            if request.prospect.known_pain_points:
                context_parts.append(f"Known Pain Points: {', '.join(request.prospect.known_pain_points)}")

        if request.product:
            context_parts.append(f"Product: {request.product.name}")
            if request.product.value_propositions:
                context_parts.append(f"Value Props: {', '.join(request.product.value_propositions)}")

        if request.objection and request.script_type == ScriptType.OBJECTION_RESPONSE:
            context_parts.append(f"Objection to Address: {request.objection.objection}")

        if request.spiced_context:
            context_parts.append(f"Known SPICED Elements: {json.dumps(request.spiced_context)}")

        context_section = "\n".join(context_parts) if context_parts else "No additional context provided."

        return self._prompt_template.format(
            script_type=request.script_type.value.replace("_", " "),
            persona=request.persona.value.replace("_", " "),
            industry=request.industry.value.replace("_", " "),
            deal_stage=request.deal_stage.value.replace("_", " "),
            tone=request.tone,
            context_section=context_section,
        )

    def _parse_claude_response(
        self,
        response: str,
        request: TalkTrackRequest,
        variant_id: Optional[str] = None
    ) -> TalkTrack:
        """Parse Claude's response into a TalkTrack object."""
        try:
            # Extract JSON from response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                data = json.loads(response[json_start:json_end])
                return self._build_talk_track_from_data(data, request, variant_id)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Claude response as JSON: {e}")

        # Fallback to template-based generation
        return self._generate_template_based(request, variant_id)

    def _build_talk_track_from_data(
        self,
        data: Dict,
        request: TalkTrackRequest,
        variant_id: Optional[str] = None
    ) -> TalkTrack:
        """Build TalkTrack from parsed data."""
        return TalkTrack(
            id=uuid4(),
            script_type=request.script_type,
            variant=variant_id,
            title=data.get("title", f"{request.script_type.value} for {request.persona.value}"),
            description=data.get("description"),
            persona=request.persona,
            industry=request.industry,
            deal_stage=request.deal_stage,
            opening=ScriptSection(
                name="Opening",
                content=data.get("opening", {}).get("content", ""),
                coaching_notes=data.get("opening", {}).get("coaching_notes"),
                duration_seconds=data.get("opening", {}).get("duration_seconds", 60),
            ),
            sections=[
                ScriptSection(
                    name=s.get("name", f"Section {i+1}"),
                    content=s.get("content", ""),
                    coaching_notes=s.get("coaching_notes"),
                    duration_seconds=s.get("duration_seconds"),
                    spiced_elements=[
                        SPICEDElement(e) for e in s.get("spiced_elements", [])
                        if e in [el.value for el in SPICEDElement]
                    ],
                    transition_phrase=s.get("transition_phrase"),
                )
                for i, s in enumerate(data.get("sections", []))
            ],
            closing=ScriptSection(
                name="Closing",
                content=data.get("closing", {}).get("content", ""),
                coaching_notes=data.get("closing", {}).get("coaching_notes"),
                duration_seconds=data.get("closing", {}).get("duration_seconds", 60),
            ),
            discovery_questions=[
                DiscoveryQuestion(
                    question=q.get("question", ""),
                    spiced_element=SPICEDElement(q.get("spiced_element", "situation")),
                    follow_up_questions=q.get("follow_up_questions", []),
                    what_to_listen_for=q.get("what_to_listen_for", ""),
                    coaching_tip=q.get("coaching_tip"),
                )
                for q in data.get("discovery_questions", [])
            ] if request.script_type == ScriptType.DISCOVERY_CALL else None,
            objection_responses=[
                ObjectionResponse(
                    objection=o.get("objection", ""),
                    category=o.get("category", "general"),
                    response=o.get("response", ""),
                    acknowledge_phrase=o.get("acknowledge_phrase", ""),
                    reframe_strategy=o.get("reframe_strategy", ""),
                    transition_to_value=o.get("transition_to_value", ""),
                    proof_points=o.get("proof_points", []),
                )
                for o in data.get("objection_responses", [])
            ] if request.script_type == ScriptType.OBJECTION_RESPONSE else None,
            key_tips=data.get("key_tips", []),
            common_mistakes=data.get("common_mistakes", []),
            success_metrics=data.get("success_metrics", []),
            total_duration_minutes=request.call_duration_minutes or data.get("total_duration_minutes"),
        )

    def _generate_template_based(
        self,
        request: TalkTrackRequest,
        variant_id: Optional[str] = None
    ) -> TalkTrack:
        """
        Generate a talk track using templates when Claude is not available.

        This provides baseline scripts based on WbD methodology templates.
        """
        generator_map = {
            ScriptType.DISCOVERY_CALL: self._generate_discovery_script,
            ScriptType.DEMO_SCRIPT: self._generate_demo_script,
            ScriptType.OBJECTION_RESPONSE: self._generate_objection_script,
            ScriptType.CLOSING_CONVERSATION: self._generate_closing_script,
            ScriptType.FOLLOW_UP_GUIDE: self._generate_followup_script,
        }

        generator = generator_map.get(request.script_type, self._generate_discovery_script)
        return generator(request, variant_id)

    def _generate_discovery_script(
        self,
        request: TalkTrackRequest,
        variant_id: Optional[str] = None
    ) -> TalkTrack:
        """Generate a discovery call script with SPICED questions."""
        prospect_name = request.prospect.name if request.prospect else "the prospect"
        company_name = request.prospect.company if request.prospect else "your company"
        product_name = request.product.name if request.product else "our solution"

        persona_opener = self._get_persona_opener(request.persona)
        industry_context = self._get_industry_context(request.industry)

        return TalkTrack(
            id=uuid4(),
            script_type=ScriptType.DISCOVERY_CALL,
            variant=variant_id,
            title=f"Discovery Call Script - {request.persona.value.replace('_', ' ').title()}",
            description=f"SPICED-aligned discovery call script for {request.industry.value.replace('_', ' ')} {request.persona.value.replace('_', ' ')}",
            persona=request.persona,
            industry=request.industry,
            deal_stage=request.deal_stage,
            opening=ScriptSection(
                name="Opening & Rapport Building",
                duration_seconds=120,
                content=f"""Hi {prospect_name}, thank you for taking the time to connect today. {persona_opener}

Before we dive in, I'd love to learn a bit more about your role and what prompted you to take this call. But first, let me give you a quick agenda:

1. I'll share a brief overview of what we do
2. Then I'd love to understand your current situation and challenges
3. We can discuss if there's a fit and what next steps might look like

Does that work for you, or is there anything specific you'd like to make sure we cover?""",
                coaching_notes="Build rapport quickly. Match their energy. Listen for cues about their communication style.",
                spiced_elements=[],
                transition_phrase="Great, let me start by understanding your current situation...",
            ),
            sections=[
                ScriptSection(
                    name="Situation Discovery",
                    duration_seconds=180,
                    content=f"""I'd love to understand your current setup. Can you walk me through how your team currently handles [relevant process]?

Follow-up probes:
- How long has that been in place?
- What does the team look like that manages this?
- What tools or systems are you using today?

{industry_context}""",
                    coaching_notes="Let them talk. Take notes. Use active listening phrases like 'I see' and 'Tell me more about that.'",
                    spiced_elements=[SPICEDElement.SITUATION],
                    transition_phrase="That's really helpful context. Now I'm curious...",
                ),
                ScriptSection(
                    name="Pain Discovery",
                    duration_seconds=240,
                    content="""What's working well with your current approach? And what's not working as well as you'd like?

Deeper pain probes:
- How often does [problem] occur?
- What happens when [problem] occurs?
- How does this impact you personally? Your team?
- If you could wave a magic wand, what would be different?""",
                    coaching_notes="Push past surface-level answers. When they mention a pain, ask 'Tell me more about that.' Get specific examples.",
                    spiced_elements=[SPICEDElement.PAIN],
                    transition_phrase="I can see why that would be frustrating. Let's talk about the impact...",
                ),
                ScriptSection(
                    name="Impact Quantification",
                    duration_seconds=180,
                    content="""When [pain] happens, what's the impact on the business?

Impact probes:
- How much time does your team spend on [problem] each week?
- What's the cost of [problem] in terms of revenue/efficiency/morale?
- How does this affect your ability to hit your goals?
- What metrics are being impacted?""",
                    coaching_notes="Get them to quantify the impact. Numbers make the case compelling. Help them calculate if needed.",
                    spiced_elements=[SPICEDElement.IMPACT],
                    transition_phrase="Those are significant numbers. Let me ask about timing...",
                ),
                ScriptSection(
                    name="Critical Event Discovery",
                    duration_seconds=120,
                    content="""Is there anything driving the timeline for solving this?

Critical event probes:
- Do you have any initiatives or deadlines that this ties into?
- What happens if this isn't solved by [timeframe]?
- Is there a budget cycle we should be aware of?
- What would need to happen for this to become a priority?""",
                    coaching_notes="No critical event = no urgency = deal stalls. If there isn't one, help them identify or create one.",
                    spiced_elements=[SPICEDElement.CRITICAL_EVENT],
                    transition_phrase="Got it. Let's talk about the decision process...",
                ),
                ScriptSection(
                    name="Decision Process Discovery",
                    duration_seconds=180,
                    content="""Help me understand how decisions like this typically get made at {company_name}.

Decision probes:
- Who else would need to be involved in evaluating a solution?
- What criteria would you use to compare options?
- Have you looked at other solutions? What did you think?
- What would make this a 'yes' vs a 'no' for you?""",
                    coaching_notes="Map the decision process. Identify all stakeholders. Understand their buying criteria.",
                    spiced_elements=[SPICEDElement.EXPECTED_DECISION, SPICEDElement.DECISION_CRITERIA],
                    transition_phrase="This is really helpful. Based on what you've shared...",
                ),
            ],
            closing=ScriptSection(
                name="Value Summary & Next Steps",
                duration_seconds=120,
                content=f"""Based on what you've shared, it sounds like [summarize pain and impact]. And you're looking to have this solved by [critical event].

Here's how {product_name} could help: [brief value proposition]

For next steps, I'd recommend [specific next step]. Does [day/time] work for you?

Is there anyone else who should join that conversation?""",
                coaching_notes="Summarize what you heard (not what you want to sell). Propose a specific next step. Don't leave with 'I'll send some info.'",
            ),
            discovery_questions=[
                DiscoveryQuestion(
                    question="Can you walk me through how your team currently handles [process]?",
                    spiced_element=SPICEDElement.SITUATION,
                    follow_up_questions=["How long has that been in place?", "What tools are you using?"],
                    what_to_listen_for="Current state, team structure, existing solutions",
                    coaching_tip="Let them describe the full picture before asking follow-ups",
                ),
                DiscoveryQuestion(
                    question="What's not working as well as you'd like with your current approach?",
                    spiced_element=SPICEDElement.PAIN,
                    follow_up_questions=["How often does that happen?", "What impact does that have?"],
                    what_to_listen_for="Specific pain points, frequency, frustration level",
                    coaching_tip="Push for specifics - 'Can you give me an example?'",
                ),
                DiscoveryQuestion(
                    question="What's the business impact when [pain] occurs?",
                    spiced_element=SPICEDElement.IMPACT,
                    follow_up_questions=["How does that translate to time/money?", "What goals does this affect?"],
                    what_to_listen_for="Quantifiable metrics, revenue impact, efficiency loss",
                    coaching_tip="Help them do the math - 'So if that happens X times per month...'",
                ),
                DiscoveryQuestion(
                    question="Is there anything driving the timeline for solving this?",
                    spiced_element=SPICEDElement.CRITICAL_EVENT,
                    follow_up_questions=["What happens if it's not solved by then?", "Is there budget allocated?"],
                    what_to_listen_for="Deadlines, initiatives, budget cycles, consequences of inaction",
                    coaching_tip="No urgency = low priority. Help them identify a compelling event.",
                ),
                DiscoveryQuestion(
                    question="Who else would need to be involved in evaluating this?",
                    spiced_element=SPICEDElement.EXPECTED_DECISION,
                    follow_up_questions=["What's their main concern?", "How have similar decisions been made?"],
                    what_to_listen_for="Decision makers, influencers, procurement process",
                    coaching_tip="Map the full buying committee. Ask about each person's role.",
                ),
                DiscoveryQuestion(
                    question="What criteria would you use to compare options?",
                    spiced_element=SPICEDElement.DECISION_CRITERIA,
                    follow_up_questions=["What's most important?", "What would be a dealbreaker?"],
                    what_to_listen_for="Must-haves, nice-to-haves, non-negotiables",
                    coaching_tip="Understand what 'good' looks like to them specifically.",
                ),
            ],
            key_tips=[
                "Listen more than you talk - aim for 70/30 prospect/rep ratio",
                "Take detailed notes - you'll need this info for proposals",
                "Summarize back what you heard to confirm understanding",
                "Always end with a clear, specific next step",
                "If you don't uncover strong SPICED, the deal will stall",
            ],
            common_mistakes=[
                "Jumping to product demo before understanding pain",
                "Accepting surface-level answers without probing deeper",
                "Talking about features instead of outcomes",
                "Leaving without a scheduled next step",
                "Not identifying all decision makers",
            ],
            success_metrics=[
                "All 6 SPICED elements identified",
                "Pain quantified with specific numbers",
                "Decision process and timeline mapped",
                "Next meeting scheduled with additional stakeholders",
                "Prospect articulated their own business case",
            ],
            total_duration_minutes=request.call_duration_minutes or 30,
        )

    def _generate_demo_script(
        self,
        request: TalkTrackRequest,
        variant_id: Optional[str] = None
    ) -> TalkTrack:
        """Generate a value-focused demo script."""
        product_name = request.product.name if request.product else "our solution"
        prospect_company = request.prospect.company if request.prospect else "your organization"

        return TalkTrack(
            id=uuid4(),
            script_type=ScriptType.DEMO_SCRIPT,
            variant=variant_id,
            title=f"Demo Script - {request.persona.value.replace('_', ' ').title()}",
            description=f"Value-focused demo script for {request.industry.value.replace('_', ' ')}",
            persona=request.persona,
            industry=request.industry,
            deal_stage=request.deal_stage,
            opening=ScriptSection(
                name="Demo Opening",
                duration_seconds=120,
                content=f"""Thank you for joining today. Before I show you {product_name}, I want to make sure this demo is valuable for you.

From our last conversation, I understood that:
- [Pain 1 from discovery]
- [Pain 2 from discovery]
- And you're looking to have this solved by [critical event]

Is that still accurate? Anything else you'd like me to address today?

Great. I've tailored this demo to focus specifically on how we can help with those challenges. I'll show you 3 key capabilities, and then we can discuss next steps.""",
                coaching_notes="Always reference previous discovery. Confirm priorities haven't changed. Set expectations for the demo.",
            ),
            sections=[
                ScriptSection(
                    name="Pain-Capability Bridge",
                    duration_seconds=300,
                    content=f"""You mentioned [specific pain]. Let me show you exactly how {product_name} addresses that.

[Demo specific feature]

What this means for {prospect_company} is [specific outcome/value].

Companies similar to you are seeing [relevant metric improvement].

How would that impact your team?""",
                    coaching_notes="Connect every feature to a pain they mentioned. Always ask how it would impact them - get them talking.",
                    spiced_elements=[SPICEDElement.PAIN, SPICEDElement.IMPACT],
                ),
                ScriptSection(
                    name="Value Demonstration",
                    duration_seconds=300,
                    content="""Now let me show you how this works in practice...

[Live demonstration]

Notice how [key differentiator]. This is different from [alternative approach] because [specific benefit].

Let's walk through a scenario that matches what you described...""",
                    coaching_notes="Use their data/examples if possible. Show, don't tell. Pause for questions and reactions.",
                ),
                ScriptSection(
                    name="Social Proof & Results",
                    duration_seconds=180,
                    content=f"""I want to share how [similar customer] in the [industry] industry achieved results with this.

They were facing [similar pain] and within [timeframe]:
- [Result 1]
- [Result 2]
- [Result 3]

Given what you've shared about {prospect_company}'s situation, I'd expect similar or better results because [reason].""",
                    coaching_notes="Use case studies relevant to their industry/size. Make the connection to their specific situation.",
                ),
            ],
            closing=ScriptSection(
                name="Demo Close & Next Steps",
                duration_seconds=180,
                content="""Based on what you've seen today, how well do you think this addresses the challenges we discussed?

[Listen and address any concerns]

Given your timeline of [critical event], here's what I'd recommend as next steps:
1. [Specific next step]
2. [Who else should be involved]
3. [Timeline]

What questions do you have before we wrap up?""",
                coaching_notes="Get their reaction before proposing next steps. Address objections directly. Always leave with a scheduled next step.",
            ),
            key_tips=[
                "Every feature shown must connect to a pain they mentioned",
                "Use their words and examples, not generic ones",
                "Pause frequently to check for understanding and reactions",
                "Tell don't sell - let the value speak for itself",
                "Demo what they need, not everything you have",
            ],
            common_mistakes=[
                "Showing too many features without connecting to value",
                "Not referencing the discovery conversation",
                "Talking too much, not getting their reactions",
                "Going over time and rushing the close",
                "Generic case studies instead of industry-relevant ones",
            ],
            success_metrics=[
                "Prospect can articulate how the solution addresses their pain",
                "Positive reactions captured during demo",
                "Objections surfaced and addressed",
                "Clear next steps with specific timeline",
                "Additional stakeholders identified for next meeting",
            ],
            total_duration_minutes=request.call_duration_minutes or 45,
        )

    def _generate_objection_script(
        self,
        request: TalkTrackRequest,
        variant_id: Optional[str] = None
    ) -> TalkTrack:
        """Generate objection response playbook."""
        objection_text = request.objection.objection if request.objection else "general objections"
        product_name = request.product.name if request.product else "our solution"

        return TalkTrack(
            id=uuid4(),
            script_type=ScriptType.OBJECTION_RESPONSE,
            variant=variant_id,
            title=f"Objection Handling - {request.persona.value.replace('_', ' ').title()}",
            description=f"Objection response playbook for common sales objections",
            persona=request.persona,
            industry=request.industry,
            deal_stage=request.deal_stage,
            opening=ScriptSection(
                name="Objection Handling Framework",
                duration_seconds=60,
                content="""When you encounter an objection, follow the LAER framework:
1. **Listen** - Let them fully express the concern
2. **Acknowledge** - Show you understand and validate
3. **Explore** - Ask questions to understand the root cause
4. **Respond** - Address the actual concern with value""",
                coaching_notes="Most objections are symptoms, not the real issue. Always explore before responding.",
            ),
            sections=[
                ScriptSection(
                    name="Acknowledgment Template",
                    duration_seconds=30,
                    content="""\"I appreciate you sharing that concern. [Specific objection] is something we hear from many companies evaluating solutions like ours. Can you help me understand a bit more about what's driving that concern?\"

Alternative acknowledgments:
- \"That's a fair point. Tell me more about...\"
- \"I understand where you're coming from. What specifically...\"
- \"Thanks for being direct about that. Can you walk me through...\"""",
                    coaching_notes="Never get defensive. Objections mean they're engaged. Treat them as opportunities.",
                ),
            ],
            closing=ScriptSection(
                name="Resolution & Commitment",
                duration_seconds=60,
                content="""After addressing the objection:

\"Does that address your concern about [objection]? Is there anything else that would need to be true for us to move forward?\"

If resolved: \"Great. Given that, shall we [specific next step]?\"

If not resolved: \"I want to make sure we address this fully. What would you need to see to feel confident about [concern]?\"""",
                coaching_notes="Always check if the objection is truly resolved. Don't move on if they're still hesitant.",
            ),
            objection_responses=[
                ObjectionResponse(
                    objection="The price is too high",
                    category="price",
                    response=f"I understand budget is a consideration. Let's look at this in terms of ROI. Based on what you shared about [impact], the cost of not solving this is approximately [calculated cost]. {product_name} would pay for itself within [timeframe] based on those numbers.",
                    acknowledge_phrase="Price is definitely an important factor in any decision.",
                    reframe_strategy="Shift from cost to ROI and cost of inaction",
                    transition_to_value="Let's look at what you're currently spending on this problem...",
                    proof_points=[
                        "Customer X saw ROI within 3 months",
                        "Average customer saves $X per year",
                        "Cost of status quo often exceeds solution cost by 3-5x",
                    ],
                ),
                ObjectionResponse(
                    objection="We're already using a competitor",
                    category="competition",
                    response="I'm glad you have something in place. Many of our best customers switched from [competitor]. What I hear most often is that while [competitor] is good at [strength], they found they needed [our differentiator] for [specific outcome]. Is that something you've experienced?",
                    acknowledge_phrase="It's smart to have a solution in place already.",
                    reframe_strategy="Focus on gaps in current solution vs our differentiators",
                    transition_to_value="What's working well with your current solution? What's not?",
                    proof_points=[
                        "X% of customers switched from [competitor]",
                        "Key differentiators: [list]",
                        "Specific outcomes competitor can't deliver",
                    ],
                ),
                ObjectionResponse(
                    objection="We need to think about it",
                    category="timing",
                    response="Of course, this is an important decision. Help me understand what you're weighing. Is it the solution fit, the timing, the investment, or something else? I want to make sure I've given you everything you need to make a confident decision.",
                    acknowledge_phrase="I appreciate you being thoughtful about this.",
                    reframe_strategy="Identify the real objection behind 'think about it'",
                    transition_to_value="What specific questions would you want answered?",
                    proof_points=[
                        "Reference their critical event timeline",
                        "Cost of delay in their specific context",
                        "Offer specific resources to help decision",
                    ],
                ),
                ObjectionResponse(
                    objection="Now is not the right time",
                    category="timing",
                    response="I understand timing is crucial. Help me understand what's driving that. Is it budget cycles, other priorities, or resources to implement? Based on what you shared about [critical event], what happens if this isn't solved by then?",
                    acknowledge_phrase="Timing is always a factor. I want to understand your situation.",
                    reframe_strategy="Connect to their critical event and cost of delay",
                    transition_to_value="Let's revisit the impact we discussed earlier...",
                    proof_points=[
                        "Cost of delay calculation",
                        "Quick implementation timeline",
                        "Phased approach option",
                    ],
                ),
                ObjectionResponse(
                    objection="I need to get buy-in from others",
                    category="stakeholder",
                    response="Absolutely, decisions like this require alignment. Who else needs to be involved, and what are their main concerns likely to be? I'd be happy to join a call with them or provide specific materials that address their questions.",
                    acknowledge_phrase="That makes sense. Getting alignment is important.",
                    reframe_strategy="Turn it into an opportunity to engage more stakeholders",
                    transition_to_value="Let me help you build the internal case...",
                    proof_points=[
                        "Offer stakeholder-specific materials",
                        "Executive summary for leadership",
                        "ROI calculator for finance",
                    ],
                ),
            ],
            key_tips=[
                "Objections mean they're engaged - welcome them",
                "Most objections are not the real objection - explore deeper",
                "Never argue or get defensive",
                "Use their own words and data when responding",
                "Always confirm the objection is resolved before moving on",
            ],
            common_mistakes=[
                "Responding immediately without exploring the root cause",
                "Getting defensive or argumentative",
                "Providing generic responses instead of personalized ones",
                "Not confirming the objection is resolved",
                "Treating 'I need to think about it' as a real answer",
            ],
            success_metrics=[
                "Root cause of objection identified",
                "Response customized to their specific situation",
                "Prospect confirms concern is addressed",
                "Conversation moves forward after objection",
                "No lingering unaddressed concerns",
            ],
            total_duration_minutes=None,
        )

    def _generate_closing_script(
        self,
        request: TalkTrackRequest,
        variant_id: Optional[str] = None
    ) -> TalkTrack:
        """Generate closing conversation script."""
        product_name = request.product.name if request.product else "our solution"
        prospect_company = request.prospect.company if request.prospect else "your organization"

        return TalkTrack(
            id=uuid4(),
            script_type=ScriptType.CLOSING_CONVERSATION,
            variant=variant_id,
            title=f"Closing Conversation - {request.persona.value.replace('_', ' ').title()}",
            description=f"WbD-aligned closing conversation framework",
            persona=request.persona,
            industry=request.industry,
            deal_stage=request.deal_stage,
            opening=ScriptSection(
                name="Value Recap",
                duration_seconds=120,
                content=f"""Thank you for the time you've invested in evaluating {product_name}. Before we discuss next steps, I want to make sure we're aligned on what we've covered.

Over our conversations, we've discussed:
- The challenges you're facing with [pain points]
- The impact of [quantified impact]
- Your timeline to have this resolved by [critical event]
- How {product_name} specifically addresses [key capabilities]

Does that align with your understanding? Is there anything we've missed?""",
                coaching_notes="Don't assume alignment. Confirm everything before asking for the close.",
            ),
            sections=[
                ScriptSection(
                    name="Stakeholder Alignment Check",
                    duration_seconds=120,
                    content="""I want to make sure everyone who needs to be comfortable with this decision is aligned.

- [Decision maker] - Are they supportive of moving forward?
- [Other stakeholders] - Have their concerns been addressed?
- Is there anyone else who needs to weigh in?

What, if anything, would prevent us from moving forward today?""",
                    coaching_notes="Surface any hidden objections or stakeholders now, not after you ask for the close.",
                    spiced_elements=[SPICEDElement.EXPECTED_DECISION, SPICEDElement.DECISION_CRITERIA],
                ),
                ScriptSection(
                    name="The Ask",
                    duration_seconds=60,
                    content=f"""Based on everything we've discussed, I'm confident {product_name} is the right solution for {prospect_company}.

Are you ready to move forward?

[If yes]: Great! Here's what happens next: [outline process]

[If hesitation]: Help me understand what's holding you back. What would need to be true for you to feel confident moving forward?""",
                    coaching_notes="Be direct. Don't waffle. Silence after 'the ask' is okay - let them respond.",
                ),
                ScriptSection(
                    name="Negotiation Prep",
                    duration_seconds=120,
                    content="""If negotiation points come up:

**On Price:**
\"I understand you want to ensure you're getting the best value. Rather than adjusting price, let's talk about [additional value we can add / payment terms / implementation support]. What would be most valuable to you?\"

**On Terms:**
\"Our standard terms are designed to protect both parties. Can you help me understand specifically which terms are concerning? I'll see what flexibility we have.\"

**On Timeline:**
\"We can typically have you live within [timeframe]. What's driving your timeline needs? Let's see how we can accommodate that.\"""",
                    coaching_notes="Know your boundaries before the call. Focus on value, not discounts. Trading > conceding.",
                ),
            ],
            closing=ScriptSection(
                name="Commitment & Next Steps",
                duration_seconds=60,
                content="""[Once agreement is reached]:

\"Excellent! Here's what happens next:
1. I'll send over the agreement today
2. Once signed, our implementation team will reach out within [timeframe]
3. You can expect to be live by [date]

Do you have any final questions before we wrap up?

Thank you for your partnership. I'm excited to work with {prospect_company}.\"""",
                coaching_notes="Be clear about next steps. Send agreement same day. Follow up promptly.",
            ),
            key_tips=[
                "Earn the right to close by confirming value and alignment first",
                "Surface objections before asking for the close",
                "Be direct and confident in your ask",
                "Silence is okay - don't fill it nervously",
                "If they're not ready, understand why and address it",
            ],
            common_mistakes=[
                "Asking for the close before confirming alignment",
                "Not involving all decision makers",
                "Caving on price without understanding the real concern",
                "Leaving the call without clear commitment or next steps",
                "Being apologetic or tentative when asking",
            ],
            success_metrics=[
                "All stakeholders aligned before ask",
                "Objections surfaced and addressed",
                "Clear commitment or specific obstacle identified",
                "Next steps documented and communicated",
                "Agreement sent same day",
            ],
            total_duration_minutes=request.call_duration_minutes or 30,
        )

    def _generate_followup_script(
        self,
        request: TalkTrackRequest,
        variant_id: Optional[str] = None
    ) -> TalkTrack:
        """Generate follow-up call guide."""
        product_name = request.product.name if request.product else "our solution"
        prospect_name = request.prospect.name if request.prospect else "the prospect"

        return TalkTrack(
            id=uuid4(),
            script_type=ScriptType.FOLLOW_UP_GUIDE,
            variant=variant_id,
            title=f"Follow-Up Call Guide - {request.persona.value.replace('_', ' ').title()}",
            description=f"Multi-touch follow-up framework for {request.deal_stage.value.replace('_', ' ')} stage",
            persona=request.persona,
            industry=request.industry,
            deal_stage=request.deal_stage,
            opening=ScriptSection(
                name="Re-engagement Opening",
                duration_seconds=60,
                content=f"""Hi {prospect_name}, it's [Your Name] from {product_name}. Do you have a quick moment?

I wanted to follow up on our conversation about [specific topic from last call].

[If they have time]:
\"Great! I've been thinking about what you shared regarding [their pain/challenge], and I wanted to share something that might be helpful.\"

[If they don't have time]:
\"No problem at all. What's a better time to reconnect? I have some thoughts on [their challenge] I'd like to share.\"""",
                coaching_notes="Lead with value, not 'just checking in.' Reference something specific from your last conversation.",
            ),
            sections=[
                ScriptSection(
                    name="Value-Add Content",
                    duration_seconds=120,
                    content="""Provide genuine value in every follow-up:

**Option 1 - Relevant Content:**
\"I came across [article/case study/data] about [their industry/challenge] and thought of your situation with [specific pain]. Would it be helpful if I sent that over?\"

**Option 2 - New Insight:**
\"Since we last spoke, we had a customer in [similar industry] achieve [specific result]. Given your situation, I thought the approach they took might be relevant.\"

**Option 3 - Helpful Connection:**
\"I was speaking with [relevant person/customer] who faced a similar challenge to yours. Would it be valuable to connect you with them?\"""",
                    coaching_notes="Every touchpoint should add value. If you don't have something valuable to share, don't call.",
                ),
                ScriptSection(
                    name="Progress Check",
                    duration_seconds=120,
                    content="""Check on their progress and any changes:

\"Last time we spoke, you mentioned [critical event/timeline]. How is that progressing?\"

\"Have there been any changes to your evaluation process or timeline?\"

\"Is [pain point] still a priority, or have other things moved up?\"

Listen for:
- Changes in urgency or priority
- New stakeholders involved
- Competitive activity
- Budget or timeline shifts""",
                    coaching_notes="Things change. Don't assume last conversation's context is still accurate.",
                    spiced_elements=[SPICEDElement.CRITICAL_EVENT, SPICEDElement.SITUATION],
                ),
                ScriptSection(
                    name="Advance the Deal",
                    duration_seconds=60,
                    content="""Based on what you learn, propose appropriate next step:

**If engaged and progressing:**
\"It sounds like things are moving forward. What would be the most valuable next step from your perspective?\"

**If stalled:**
\"I want to be respectful of your time. Is this still a priority? If so, what would need to happen to move forward? If not, I understand - things change.\"

**If new information:**
\"Given [new information], it might make sense to [specific action]. Does that seem valuable?\"""",
                    coaching_notes="Be direct about deal status. Stalled deals waste everyone's time. It's okay to qualify out.",
                ),
            ],
            closing=ScriptSection(
                name="Clear Next Step",
                duration_seconds=60,
                content="""Always end with a specific commitment:

\"Based on our conversation, it sounds like [next step] would be valuable. Does [specific day/time] work for you?\"

\"I'll send over [specific resource] by [specific time]. Would it be helpful to schedule a call to discuss it?\"

\"Let's reconnect in [timeframe] to [specific purpose]. Does [day] work?\"

Calendar the follow-up before hanging up.""",
                coaching_notes="Vague next steps = deal death. 'I'll follow up next week' is not a next step. Be specific.",
            ),
            key_tips=[
                "Every touchpoint must add value - no 'just checking in' calls",
                "Reference specific details from previous conversations",
                "Check for changes in situation, priorities, or timeline",
                "Be willing to qualify out if deal is truly stalled",
                "Always end with a specific, scheduled next step",
            ],
            common_mistakes=[
                "Following up without adding value",
                "Assuming nothing has changed since last conversation",
                "Being pushy instead of helpful",
                "Vague next steps like 'let's reconnect soon'",
                "Continuing to pursue deals that are clearly dead",
            ],
            success_metrics=[
                "Provided genuine value in the conversation",
                "Updated understanding of their situation",
                "Clear next step scheduled",
                "Deal status accurately reflected in CRM",
                "Relationship strengthened regardless of outcome",
            ],
            total_duration_minutes=request.call_duration_minutes or 15,
        )

    async def _generate_variants(
        self,
        request: TalkTrackRequest,
        primary: TalkTrack
    ) -> List[TalkTrack]:
        """Generate A/B variant versions of the talk track."""
        variants = []

        # Variant A: More direct/assertive tone
        variant_a_request = request.model_copy()
        variant_a_request.tone = "assertive"
        variant_a = await self._generate_talk_track(variant_a_request, variant_id="A")
        variant_a.title = f"{variant_a.title} (Variant A - Direct)"
        variants.append(variant_a)

        # Variant B: More consultative/exploratory tone
        variant_b_request = request.model_copy()
        variant_b_request.tone = "consultative"
        variant_b = await self._generate_talk_track(variant_b_request, variant_id="B")
        variant_b.title = f"{variant_b.title} (Variant B - Consultative)"
        variants.append(variant_b)

        return variants

    def _get_persona_opener(self, persona: PersonaType) -> str:
        """Get persona-specific opening line."""
        openers = {
            PersonaType.EXECUTIVE: "I know your time is valuable, so I'll make sure we make the most of it.",
            PersonaType.TECHNICAL: "I'd love to dive into the technical details of what you're looking for.",
            PersonaType.FINANCIAL: "I want to make sure we cover the ROI and business impact clearly.",
            PersonaType.OPERATIONS: "I'm looking forward to understanding your processes and where we can add efficiency.",
            PersonaType.END_USER: "I want to understand your day-to-day experience and what would make your job easier.",
            PersonaType.CHAMPION: "I really appreciate you championing this internally.",
            PersonaType.ECONOMIC_BUYER: "I want to make sure we address the business case and decision criteria clearly.",
        }
        return openers.get(persona, "I'm looking forward to learning more about your situation.")

    def _get_industry_context(self, industry: Industry) -> str:
        """Get industry-specific discovery context."""
        contexts = {
            Industry.TECHNOLOGY: "In tech companies, I often hear about rapid growth challenges, technical debt, and the need to scale efficiently.",
            Industry.HEALTHCARE: "Healthcare organizations often face regulatory compliance, patient experience, and operational efficiency challenges.",
            Industry.FINANCIAL_SERVICES: "Financial services companies typically prioritize risk management, compliance, and customer experience.",
            Industry.MANUFACTURING: "Manufacturing companies often focus on operational efficiency, supply chain, and quality control.",
            Industry.RETAIL: "Retail organizations frequently deal with omnichannel challenges, customer experience, and inventory management.",
            Industry.PROFESSIONAL_SERVICES: "Professional services firms often focus on utilization, client experience, and knowledge management.",
            Industry.EDUCATION: "Educational institutions typically prioritize student outcomes, operational efficiency, and engagement.",
            Industry.GOVERNMENT: "Government agencies often balance compliance requirements, citizen services, and budget constraints.",
            Industry.MEDIA_ENTERTAINMENT: "Media companies frequently face content monetization, audience engagement, and digital transformation challenges.",
            Industry.REAL_ESTATE: "Real estate organizations often focus on deal flow, relationship management, and market intelligence.",
        }
        return contexts.get(industry, "")
