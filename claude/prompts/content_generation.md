# Content Generation Prompts

This document contains the prompt templates and guidelines for AI-powered sales content generation in Sales OS.

## Overview

The content generation system creates professional sales materials aligned with the Winning by Design (WbD) SPICED methodology:

- **S**ituation: Understanding the customer's current state
- **P**ain: Identifying problems and challenges
- **I**mpact: Quantifying business impact
- **C**ritical Event: Recognizing timeline drivers
- **E**xpected Decision: Understanding the decision process
- **D**ecision Criteria: Knowing how solutions are evaluated

## Supported Content Types

### 1. Sales Decks
- **Pitch Deck**: Initial presentation to prospects
- **Renewal Deck**: Customer renewal conversations
- **QBR Deck**: Quarterly business reviews

### 2. Proposals
- **Custom Proposal**: Fully tailored to specific opportunities
- **Templated Proposal**: Based on standard templates

### 3. One-Pagers
- **Product One-Pager**: Product overview and benefits
- **Solution One-Pager**: Solution-focused messaging
- **Case Study One-Pager**: Customer success stories

### 4. Battlecards
- **Competitive Battlecard**: Competitor comparison and positioning
- **Objection Battlecard**: Common objections and responses

---

## System Prompt Template

```
You are an expert B2B sales content creator specializing in {content_type}s.
Your content follows the Winning by Design (WbD) methodology and SPICED framework.

SPICED Methodology Guidelines:
- SITUATION: Understand and reflect the customer's current state
- PAIN: Clearly articulate the problems and challenges they face
- IMPACT: Quantify the business impact of these problems
- CRITICAL EVENT: Identify timeline drivers and urgency factors
- EXPECTED DECISION: Understand their decision process
- DECISION CRITERIA: Address how they will evaluate solutions

Align all content with customer-centric value selling principles.
Focus on outcomes and business impact, not just features.

Brand Voice Guidelines:
{brand_voice_guidelines}

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
```

---

## Brand Voice Guidelines

### Professional (Default)
```
- Use clear, confident language
- Avoid jargon unless industry-standard
- Focus on value and outcomes
- Maintain a polished, business-appropriate tone
- Use data and evidence to support claims
```

### Conversational
```
- Use friendly, approachable language
- Write as if having a dialogue
- Use contractions naturally
- Keep sentences shorter and more dynamic
- Include occasional questions to engage
```

### Technical
```
- Use precise technical terminology
- Include specific details and specifications
- Focus on functionality and capabilities
- Reference technical standards when relevant
- Be thorough but avoid unnecessary complexity
```

### Executive
```
- Lead with business impact and ROI
- Be concise and direct
- Focus on strategic outcomes
- Use metrics and KPIs
- Emphasize competitive advantage
```

---

## Deck Generation Prompts

### Pitch Deck Structure
```
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
```

### Renewal Deck Structure
```
1. Title Slide
2. Partnership Overview & Timeline
3. Key Achievements & Wins
4. Usage & Adoption Metrics
5. Value Delivered (ROI)
6. What's New & Roadmap
7. Expansion Opportunities
8. Renewal Terms & Investment
```

### QBR Deck Structure
```
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
```

### Deck Slide Output Format
```json
{
    "title": "Deck title",
    "subtitle": "Optional subtitle",
    "estimated_duration_minutes": 30,
    "key_messages": ["message1", "message2", "message3"],
    "call_to_action": "Clear CTA",
    "slides": [
        {
            "slide_number": 1,
            "title": "Slide title",
            "subtitle": "Optional subtitle",
            "content_type": "text|bullets|chart|image|quote",
            "main_content": "Content text or [array of bullets]",
            "speaker_notes": "Notes for presenter",
            "visual_suggestions": "Suggested visuals",
            "transition_note": "How to transition to next slide"
        }
    ]
}
```

---

## Proposal Generation Prompts

### Standard Proposal Sections
1. Executive Summary
2. Understanding Your Challenges (SPICED-aligned)
3. Proposed Solution
4. Implementation Approach
5. Investment & ROI
6. Why Choose Us
7. Next Steps

### Proposal Output Format
```json
{
    "title": "Proposal title",
    "executive_summary": "Compelling executive summary paragraph",
    "sections": [
        {
            "section_number": 1,
            "title": "Section title",
            "content": "Section content (markdown supported)",
            "subsections": [
                {"title": "Subsection", "content": "Content"}
            ]
        }
    ],
    "pricing_table": {
        "items": [
            {"name": "Item", "description": "Desc", "price": "$X,XXX"}
        ],
        "total": "$XX,XXX",
        "notes": "Pricing notes"
    },
    "terms_and_conditions": "Standard terms",
    "next_steps": ["Step 1", "Step 2", "Step 3"],
    "validity_period": "30 days",
    "signature_block": {
        "company": "Company name",
        "prepared_by": "Name",
        "date": "Date"
    }
}
```

---

## One-Pager Generation Prompts

### Product/Solution One-Pager Output Format
```json
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
    "contact_info": {"email": "email", "phone": "phone", "website": "url"}
}
```

### Case Study One-Pager Output Format
```json
{
    "title": "One-pager title",
    "headline": "Compelling headline",
    "subheadline": "Supporting subheadline",
    "overview": "Brief overview paragraph",
    "key_points": [...],
    "benefits": [...],
    "proof_points": [...],
    "call_to_action": "Clear CTA",
    "contact_info": {...},
    "customer_name": "Customer Name",
    "challenge": "Challenge description",
    "solution": "Solution description",
    "results": [
        {"metric": "50%", "description": "improvement in X"}
    ],
    "customer_quote": "Customer testimonial"
}
```

---

## Battlecard Generation Prompts

### Competitive Battlecard Output Format
```json
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
}
```

### Objection Handling Battlecard Output Format
```json
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
        {
            "objection": "Objection",
            "context": "When it arises",
            "response": "Detailed response",
            "follow_up": "Follow-up question"
        }
    ],
    "prevention_tips": ["How to prevent this objection"],
    "related_proof_points": ["Evidence to support responses"]
}
```

---

## Best Practices

### Writing Effective Sales Content

1. **Lead with Value**: Start with outcomes and benefits, not features
2. **Be Specific**: Use concrete numbers and examples
3. **Address Pain Points**: Connect solutions to customer challenges
4. **Create Urgency**: Highlight critical events and timing
5. **Include Social Proof**: Add testimonials and case studies
6. **Clear CTAs**: Every piece should drive action

### SPICED Alignment Checklist

- [ ] Does the content reflect the customer's current situation?
- [ ] Are the customer's pain points clearly addressed?
- [ ] Is the business impact quantified?
- [ ] Are timeline drivers and urgency factors highlighted?
- [ ] Does the content align with their decision process?
- [ ] Are evaluation criteria addressed?

### Quality Control

- [ ] Content is free of grammatical errors
- [ ] Brand voice is consistent throughout
- [ ] Claims are supported with evidence
- [ ] Structure is logical and easy to follow
- [ ] Call to action is clear and compelling
- [ ] Content is appropriately personalized

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-01-15 | Initial release |
