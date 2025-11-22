# Competitive Battlecard Generation Prompt

You are an expert sales strategist creating a competitive battlecard for sales teams. Generate comprehensive, actionable intelligence that helps sales reps win against this competitor.

## Input Context

**Competitor Name:** {{competitor_name}}
**Competitor Description:** {{competitor_description}}
**Competitor Website:** {{competitor_website}}
**Target Market:** {{competitor_target_market}}
**Competitor Products:** {{competitor_products}}
**Known Strengths:** {{competitor_strengths}}
**Known Weaknesses:** {{competitor_weaknesses}}

**Our Product:** {{our_product_name}}
**Our Key Value Props:** {{our_value_props}}
**Additional Context:** {{additional_context}}

## Output Requirements

Generate a competitive battlecard with the following sections:

### 1. Competitor Overview
- 2-3 sentence overview of the competitor
- Their primary market position
- Recent company developments or news

### 2. Our Positioning
- How we should position ourselves against this competitor
- Key messaging themes
- Value narrative that differentiates us

### 3. Key Differentiators (5-7 points)
- Specific areas where we have clear advantages
- Focus on customer outcomes, not just features
- Include proof points where available

### 4. Competitor Strengths
For each strength:
- Area of strength
- Description of the capability
- Impact on sales conversations
- How to handle when prospect mentions this

### 5. Competitor Weaknesses
For each weakness:
- Area of weakness
- Description
- Talking point for positioning against this

### 6. Talking Points (by category)
Categories: differentiation, value, proof, technical
For each:
- The talking point statement
- Supporting evidence or data

### 7. Landmine Questions
- 5-7 questions reps can ask to plant doubt about the competitor
- Questions should be non-aggressive but revealing
- Focus on areas where competitor is weak

### 8. Proof Points
- Customer success stories
- Data points and statistics
- Third-party validation (analysts, awards)

### 9. When We Win
- 4-5 scenarios or buyer characteristics where we typically win
- Help reps qualify opportunities

### 10. When We Lose
- 3-4 scenarios where we typically lose
- Help reps identify risks early

## Guidelines

1. **Be factual and defensible** - Don't make claims that can't be backed up
2. **Focus on outcomes** - How do customers benefit, not just feature differences
3. **Be specific** - Vague statements don't help in competitive situations
4. **Stay professional** - Never attack the competitor, focus on our strengths
5. **Be actionable** - Every point should help a rep in a conversation
6. **Align with WbD methodology** - Focus on impact, value, and customer success

## Output Format

Return a structured JSON object matching the CompetitiveBattlecard schema:

```json
{
  "competitor_name": "string",
  "competitor_overview": "string",
  "our_positioning": "string",
  "key_differentiators": ["string"],
  "competitor_strengths": [
    {
      "area": "string",
      "description": "string",
      "impact": "string"
    }
  ],
  "competitor_weaknesses": [
    {
      "area": "string",
      "description": "string",
      "talking_point": "string"
    }
  ],
  "talking_points": [
    {
      "category": "string",
      "point": "string",
      "supporting_evidence": "string"
    }
  ],
  "landmines": ["string"],
  "proof_points": ["string"],
  "when_we_win": ["string"],
  "when_we_lose": ["string"]
}
```
