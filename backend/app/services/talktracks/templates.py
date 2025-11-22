"""
Script Templates Module

Provides template components for talk track generation including
WbD methodology snippets, persona-specific language, and industry terms.
"""

from typing import Dict, List
from backend.app.models.talktrack import (
    PersonaType,
    Industry,
    ScriptType,
    DealStage,
    SPICEDElement,
)


class ScriptTemplates:
    """
    Repository of script templates and components for talk track generation.

    Provides:
    - Persona-specific language patterns
    - Industry-specific terminology
    - WbD methodology snippets
    - SPICED question templates
    """

    # =========================================================================
    # SPICED Question Templates
    # =========================================================================

    SPICED_QUESTIONS: Dict[SPICEDElement, List[Dict[str, str]]] = {
        SPICEDElement.SITUATION: [
            {
                "question": "Can you walk me through your current process for [area]?",
                "what_to_listen_for": "Current tools, team structure, workflow",
                "follow_ups": ["How long has that been in place?", "Who's involved?"],
            },
            {
                "question": "What does a typical [day/week/month] look like for your team?",
                "what_to_listen_for": "Time allocation, priorities, pain points",
                "follow_ups": ["Where do you spend most of your time?", "What's most challenging?"],
            },
            {
                "question": "Help me understand how your team is structured.",
                "what_to_listen_for": "Roles, responsibilities, decision making",
                "follow_ups": ["How do teams collaborate?", "Who owns this area?"],
            },
        ],
        SPICEDElement.PAIN: [
            {
                "question": "What's not working as well as you'd like today?",
                "what_to_listen_for": "Frustrations, bottlenecks, complaints",
                "follow_ups": ["Can you give me an example?", "How often does that happen?"],
            },
            {
                "question": "What would you change about your current approach if you could?",
                "what_to_listen_for": "Ideal state, known limitations",
                "follow_ups": ["What's preventing that change?", "What have you tried?"],
            },
            {
                "question": "Where do things break down or cause friction?",
                "what_to_listen_for": "Process gaps, manual work, errors",
                "follow_ups": ["Who does that impact?", "What's the workaround?"],
            },
        ],
        SPICEDElement.IMPACT: [
            {
                "question": "When [pain] happens, what's the impact on the business?",
                "what_to_listen_for": "Revenue, efficiency, morale metrics",
                "follow_ups": ["Can you quantify that?", "What goals does it affect?"],
            },
            {
                "question": "How does this affect your ability to hit your targets?",
                "what_to_listen_for": "KPIs, quota, objectives at risk",
                "follow_ups": ["What's at stake?", "How much is this costing you?"],
            },
            {
                "question": "If this doesn't get solved, what happens?",
                "what_to_listen_for": "Consequences, urgency, stakes",
                "follow_ups": ["What's the timeline on that?", "Who else is affected?"],
            },
        ],
        SPICEDElement.CRITICAL_EVENT: [
            {
                "question": "Is there anything driving the timeline for solving this?",
                "what_to_listen_for": "Deadlines, initiatives, external factors",
                "follow_ups": ["What happens if you miss that?", "Is there flexibility?"],
            },
            {
                "question": "What's prompting you to look at this now versus six months ago?",
                "what_to_listen_for": "Trigger events, new priorities, changes",
                "follow_ups": ["What changed?", "Why now specifically?"],
            },
            {
                "question": "Are there any upcoming events or deadlines this ties into?",
                "what_to_listen_for": "Board meetings, fiscal year, launches",
                "follow_ups": ["What needs to happen before then?", "Who's driving that?"],
            },
        ],
        SPICEDElement.EXPECTED_DECISION: [
            {
                "question": "Help me understand how decisions like this get made here.",
                "what_to_listen_for": "Process, stakeholders, timeline",
                "follow_ups": ["Who else is involved?", "What's the approval process?"],
            },
            {
                "question": "Who else would need to be involved in evaluating this?",
                "what_to_listen_for": "Decision makers, influencers, blockers",
                "follow_ups": ["What's their perspective?", "How do we engage them?"],
            },
            {
                "question": "Have you evaluated similar solutions before? What happened?",
                "what_to_listen_for": "Past experiences, lessons learned, concerns",
                "follow_ups": ["Why didn't that work out?", "What would be different?"],
            },
        ],
        SPICEDElement.DECISION_CRITERIA: [
            {
                "question": "What criteria would you use to compare options?",
                "what_to_listen_for": "Must-haves, nice-to-haves, dealbreakers",
                "follow_ups": ["What's most important?", "What would be a dealbreaker?"],
            },
            {
                "question": "What would success look like 6 months after implementation?",
                "what_to_listen_for": "Desired outcomes, metrics, expectations",
                "follow_ups": ["How would you measure that?", "What's realistic?"],
            },
            {
                "question": "What concerns would need to be addressed before moving forward?",
                "what_to_listen_for": "Objections, risks, requirements",
                "follow_ups": ["What would resolve that?", "How important is that?"],
            },
        ],
    }

    # =========================================================================
    # Persona-Specific Language
    # =========================================================================

    PERSONA_LANGUAGE: Dict[PersonaType, Dict[str, List[str]]] = {
        PersonaType.EXECUTIVE: {
            "priorities": ["strategic growth", "competitive advantage", "market position", "shareholder value", "operational excellence"],
            "metrics": ["revenue growth", "market share", "profitability", "customer retention", "NPS"],
            "concerns": ["risk", "ROI", "time to value", "board visibility", "team capacity"],
            "phrases": [
                "From a strategic perspective...",
                "How does this impact the bottom line?",
                "What's the competitive advantage?",
                "How does this scale?",
            ],
        },
        PersonaType.TECHNICAL: {
            "priorities": ["system reliability", "integration", "scalability", "security", "developer experience"],
            "metrics": ["uptime", "latency", "error rates", "deployment frequency", "technical debt"],
            "concerns": ["architecture", "compatibility", "maintenance burden", "vendor lock-in", "data security"],
            "phrases": [
                "Let's dive into the technical details...",
                "How does this integrate with...",
                "What's the architecture?",
                "How do you handle...",
            ],
        },
        PersonaType.FINANCIAL: {
            "priorities": ["cost efficiency", "ROI", "budget predictability", "compliance", "risk management"],
            "metrics": ["total cost of ownership", "payback period", "cost savings", "budget variance"],
            "concerns": ["pricing", "hidden costs", "contract terms", "audit requirements", "financial risk"],
            "phrases": [
                "What's the total cost of ownership?",
                "How does pricing work?",
                "What's the ROI timeline?",
                "Are there any hidden costs?",
            ],
        },
        PersonaType.OPERATIONS: {
            "priorities": ["efficiency", "process optimization", "team productivity", "quality", "consistency"],
            "metrics": ["throughput", "cycle time", "error rate", "utilization", "SLA compliance"],
            "concerns": ["implementation", "training", "change management", "process disruption", "adoption"],
            "phrases": [
                "How will this affect our workflows?",
                "What's the implementation process?",
                "How do we train the team?",
                "What support do you provide?",
            ],
        },
        PersonaType.END_USER: {
            "priorities": ["ease of use", "time savings", "daily workflow", "reliability", "support"],
            "metrics": ["time saved", "tasks completed", "satisfaction", "feature usage"],
            "concerns": ["learning curve", "daily disruption", "reliability", "getting help when needed"],
            "phrases": [
                "Will this make my job easier?",
                "How long does it take to learn?",
                "What happens if something goes wrong?",
                "Can I customize it to my workflow?",
            ],
        },
        PersonaType.CHAMPION: {
            "priorities": ["internal advocacy", "demonstrating value", "stakeholder buy-in", "implementation success"],
            "metrics": ["adoption rate", "stakeholder satisfaction", "project milestones", "executive visibility"],
            "concerns": ["internal resistance", "proving ROI", "implementation risk", "personal credibility"],
            "phrases": [
                "How do I get buy-in from...",
                "What proof points can I share?",
                "How do we handle internal pushback?",
                "What's the success rate for implementations?",
            ],
        },
        PersonaType.ECONOMIC_BUYER: {
            "priorities": ["business impact", "ROI", "risk mitigation", "strategic alignment", "resource allocation"],
            "metrics": ["revenue impact", "cost reduction", "productivity gains", "time to value"],
            "concerns": ["investment justification", "opportunity cost", "vendor stability", "long-term value"],
            "phrases": [
                "What's the business case?",
                "How does this compare to alternatives?",
                "What's the risk if we don't do this?",
                "How have similar companies benefited?",
            ],
        },
    }

    # =========================================================================
    # Industry-Specific Terminology
    # =========================================================================

    INDUSTRY_TERMINOLOGY: Dict[Industry, Dict[str, List[str]]] = {
        Industry.TECHNOLOGY: {
            "pain_points": ["technical debt", "scaling challenges", "talent retention", "release velocity", "security vulnerabilities"],
            "metrics": ["MRR/ARR", "churn rate", "CAC/LTV", "NPS", "time to value"],
            "buzzwords": ["SaaS", "cloud-native", "API-first", "DevOps", "microservices", "AI/ML"],
            "regulations": ["SOC 2", "GDPR", "CCPA", "ISO 27001"],
        },
        Industry.HEALTHCARE: {
            "pain_points": ["patient experience", "regulatory compliance", "interoperability", "staff burnout", "cost containment"],
            "metrics": ["patient satisfaction", "readmission rates", "revenue cycle", "clinical outcomes"],
            "buzzwords": ["EHR/EMR", "telehealth", "value-based care", "population health", "SDOH"],
            "regulations": ["HIPAA", "HITECH", "Meaningful Use", "CMS requirements"],
        },
        Industry.FINANCIAL_SERVICES: {
            "pain_points": ["regulatory compliance", "fraud detection", "customer experience", "digital transformation", "legacy systems"],
            "metrics": ["AUM", "NIM", "cost-to-income", "customer acquisition cost", "digital adoption"],
            "buzzwords": ["fintech", "open banking", "RegTech", "blockchain", "AML/KYC"],
            "regulations": ["SOX", "GDPR", "PCI-DSS", "Basel III", "Dodd-Frank"],
        },
        Industry.MANUFACTURING: {
            "pain_points": ["supply chain disruption", "quality control", "equipment downtime", "labor shortage", "sustainability"],
            "metrics": ["OEE", "yield rate", "defect rate", "inventory turns", "on-time delivery"],
            "buzzwords": ["Industry 4.0", "IoT", "predictive maintenance", "digital twin", "lean manufacturing"],
            "regulations": ["ISO 9001", "OSHA", "EPA", "FDA (for applicable)"],
        },
        Industry.RETAIL: {
            "pain_points": ["omnichannel experience", "inventory management", "customer loyalty", "margin pressure", "supply chain"],
            "metrics": ["same-store sales", "inventory turnover", "basket size", "conversion rate", "customer lifetime value"],
            "buzzwords": ["omnichannel", "D2C", "clienteling", "unified commerce", "last-mile delivery"],
            "regulations": ["PCI-DSS", "CCPA/GDPR", "ADA compliance"],
        },
        Industry.PROFESSIONAL_SERVICES: {
            "pain_points": ["utilization", "talent management", "client experience", "knowledge sharing", "project profitability"],
            "metrics": ["billable utilization", "realization rate", "client satisfaction", "revenue per partner"],
            "buzzwords": ["practice management", "matter management", "knowledge management", "alternative fee arrangements"],
            "regulations": ["professional licensing", "conflicts of interest", "confidentiality"],
        },
        Industry.EDUCATION: {
            "pain_points": ["student outcomes", "enrollment management", "budget constraints", "technology adoption", "equity"],
            "metrics": ["graduation rates", "enrollment yield", "student satisfaction", "cost per student"],
            "buzzwords": ["EdTech", "LMS", "adaptive learning", "competency-based", "online/hybrid"],
            "regulations": ["FERPA", "Title IX", "ADA", "accreditation standards"],
        },
        Industry.GOVERNMENT: {
            "pain_points": ["citizen experience", "legacy modernization", "cybersecurity", "budget cycles", "compliance"],
            "metrics": ["citizen satisfaction", "processing time", "cost per transaction", "digital adoption"],
            "buzzwords": ["GovTech", "digital services", "shared services", "FedRAMP", "zero trust"],
            "regulations": ["FedRAMP", "FISMA", "508 compliance", "FAR/DFAR"],
        },
        Industry.MEDIA_ENTERTAINMENT: {
            "pain_points": ["content monetization", "audience fragmentation", "piracy", "ad tech", "rights management"],
            "metrics": ["ARPU", "subscriber growth", "engagement time", "ad revenue", "content ROI"],
            "buzzwords": ["OTT", "streaming", "programmatic", "first-party data", "creator economy"],
            "regulations": ["COPPA", "GDPR", "content licensing", "FCC (where applicable)"],
        },
        Industry.REAL_ESTATE: {
            "pain_points": ["deal velocity", "market intelligence", "relationship management", "portfolio performance", "sustainability"],
            "metrics": ["cap rate", "NOI", "occupancy rate", "days on market", "transaction volume"],
            "buzzwords": ["PropTech", "smart buildings", "ESG", "CRE", "co-working"],
            "regulations": ["fair housing", "ADA", "environmental regulations", "zoning"],
        },
    }

    # =========================================================================
    # Objection Categories and Responses
    # =========================================================================

    OBJECTION_CATEGORIES: Dict[str, Dict[str, str]] = {
        "price": {
            "name": "Price/Budget",
            "description": "Concerns about cost, budget, or ROI",
            "strategy": "Shift from cost to value and ROI. Quantify the cost of inaction.",
        },
        "timing": {
            "name": "Timing",
            "description": "Not the right time, other priorities",
            "strategy": "Connect to critical events. Explore cost of delay.",
        },
        "competition": {
            "name": "Competition",
            "description": "Using or considering alternatives",
            "strategy": "Focus on differentiation and unique value. Understand what's working/not working.",
        },
        "authority": {
            "name": "Authority/Stakeholders",
            "description": "Need to involve others, can't decide alone",
            "strategy": "Help build internal case. Offer to engage stakeholders directly.",
        },
        "need": {
            "name": "Need",
            "description": "Don't see the problem or urgency",
            "strategy": "Revisit discovery. Help quantify hidden costs of status quo.",
        },
        "trust": {
            "name": "Trust/Risk",
            "description": "Concerns about vendor, implementation, or change",
            "strategy": "Provide proof points, references, and risk mitigation.",
        },
    }

    # =========================================================================
    # Transition Phrases
    # =========================================================================

    TRANSITION_PHRASES: Dict[str, List[str]] = {
        "to_pain": [
            "That's helpful context. Now I'm curious about what challenges you're facing...",
            "Thanks for walking me through that. What's not working as well as you'd like?",
            "Interesting. Where do things tend to break down?",
        ],
        "to_impact": [
            "I can see why that's frustrating. What's the impact when that happens?",
            "That sounds significant. How does that affect the business?",
            "Understood. Help me understand the downstream effects...",
        ],
        "to_critical_event": [
            "That's a meaningful impact. What's driving the timeline on this?",
            "Given those numbers, is there urgency to solve this?",
            "Is there anything that makes solving this time-sensitive?",
        ],
        "to_decision": [
            "Let me ask about the decision process...",
            "Help me understand how you'd evaluate a solution...",
            "If we were to move forward, who else would need to be involved?",
        ],
        "to_next_steps": [
            "Based on what you've shared, here's what I'd recommend...",
            "Given your timeline, the logical next step would be...",
            "Here's what I think would be most valuable as a next step...",
        ],
        "after_objection": [
            "Does that address your concern?",
            "Is there anything else holding you back?",
            "What else would you need to feel confident moving forward?",
        ],
    }

    # =========================================================================
    # Helper Methods
    # =========================================================================

    @classmethod
    def get_spiced_questions(cls, element: SPICEDElement) -> List[Dict[str, str]]:
        """Get SPICED questions for a specific element."""
        return cls.SPICED_QUESTIONS.get(element, [])

    @classmethod
    def get_persona_language(cls, persona: PersonaType) -> Dict[str, List[str]]:
        """Get language patterns for a specific persona."""
        return cls.PERSONA_LANGUAGE.get(persona, {})

    @classmethod
    def get_industry_terms(cls, industry: Industry) -> Dict[str, List[str]]:
        """Get terminology for a specific industry."""
        return cls.INDUSTRY_TERMINOLOGY.get(industry, {})

    @classmethod
    def get_transition_phrase(cls, transition_type: str) -> str:
        """Get a random transition phrase for the given type."""
        import random
        phrases = cls.TRANSITION_PHRASES.get(transition_type, [])
        return random.choice(phrases) if phrases else ""

    @classmethod
    def get_objection_strategy(cls, category: str) -> Dict[str, str]:
        """Get objection handling strategy for a category."""
        return cls.OBJECTION_CATEGORIES.get(category, {})

    @classmethod
    def customize_for_context(
        cls,
        base_text: str,
        persona: PersonaType,
        industry: Industry,
    ) -> str:
        """
        Customize text for specific persona and industry.

        Replaces generic placeholders with context-appropriate terms.
        """
        persona_lang = cls.get_persona_language(persona)
        industry_terms = cls.get_industry_terms(industry)

        # Replace generic terms with industry-specific ones
        text = base_text

        if industry_terms.get("metrics"):
            text = text.replace("[relevant metric]", industry_terms["metrics"][0])

        if industry_terms.get("pain_points"):
            text = text.replace("[common challenge]", industry_terms["pain_points"][0])

        if persona_lang.get("priorities"):
            text = text.replace("[key priority]", persona_lang["priorities"][0])

        return text
