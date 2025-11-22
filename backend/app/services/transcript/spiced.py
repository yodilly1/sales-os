"""SPICED methodology analyzer using Claude API."""

import logging
from typing import Dict, Any, Optional

from pydantic import BaseModel, Field

from app.core.config import settings

logger = logging.getLogger(__name__)


class SPICEDScore(BaseModel):
    """Score and analysis for a single SPICED element."""

    score: int = Field(ge=1, le=5, description="Score from 1-5")
    analysis: str = Field(description="Analysis of this element")
    quotes: list[str] = Field(default_factory=list, description="Supporting quotes")
    suggestions: list[str] = Field(
        default_factory=list, description="Improvement suggestions"
    )


class SPICEDAnalysisResult(BaseModel):
    """Complete SPICED analysis result."""

    situation: SPICEDScore
    pain: SPICEDScore
    impact: SPICEDScore
    critical_event: SPICEDScore
    expected_decision: SPICEDScore
    decision_criteria: SPICEDScore
    overall_score: float = Field(description="Average score across all elements")
    summary: str = Field(description="Executive summary of the call")
    key_insights: list[str] = Field(default_factory=list)
    recommended_next_steps: list[str] = Field(default_factory=list)
    coaching_recommendations: list[str] = Field(default_factory=list)


# SPICED extraction prompt for Claude
SPICED_EXTRACTION_PROMPT = """You are an expert sales coach trained in the Winning by Design SPICED methodology. Analyze the following sales call transcript and extract SPICED elements.

## SPICED Framework

**S - Situation**: The prospect's current state, context, and background
- What is their current situation?
- What tools/processes do they use today?
- What is their team structure?

**P - Pain**: Problems, challenges, frustrations they're experiencing
- What specific problems did they mention?
- What frustrations were expressed?
- What's not working well for them?

**I - Impact**: Business impact and consequences of their pain
- What is the cost of their pain (time, money, reputation)?
- How does this affect their team/company?
- What happens if they don't solve this?

**C - Critical Event**: Timeline drivers and urgency factors
- Is there a deadline or event driving urgency?
- What's prompting them to look for a solution now?
- Any budget cycles, launches, or milestones mentioned?

**E - Expected Decision**: The decision process and criteria
- Who is involved in the decision?
- What's their evaluation process?
- What are they comparing against?

**D - Decision Criteria**: How they'll evaluate and choose a solution
- What features/capabilities matter most?
- What are their must-haves vs nice-to-haves?
- What would make them choose one solution over another?

## Instructions

1. Carefully read the transcript below
2. Extract relevant information for each SPICED element
3. Score each element from 1-5:
   - 1: Not addressed at all
   - 2: Briefly mentioned but not explored
   - 3: Partially explored with some detail
   - 4: Well explored with good detail
   - 5: Thoroughly explored with excellent detail
4. Provide specific quotes from the transcript as evidence
5. Suggest questions the rep could have asked to improve coverage

## Transcript

{transcript}

## Response Format

Respond with a JSON object containing your analysis. Use this exact structure:

```json
{
  "situation": {
    "score": <1-5>,
    "analysis": "<detailed analysis>",
    "quotes": ["<quote1>", "<quote2>"],
    "suggestions": ["<suggestion1>", "<suggestion2>"]
  },
  "pain": {
    "score": <1-5>,
    "analysis": "<detailed analysis>",
    "quotes": ["<quote1>", "<quote2>"],
    "suggestions": ["<suggestion1>", "<suggestion2>"]
  },
  "impact": {
    "score": <1-5>,
    "analysis": "<detailed analysis>",
    "quotes": ["<quote1>", "<quote2>"],
    "suggestions": ["<suggestion1>", "<suggestion2>"]
  },
  "critical_event": {
    "score": <1-5>,
    "analysis": "<detailed analysis>",
    "quotes": ["<quote1>", "<quote2>"],
    "suggestions": ["<suggestion1>", "<suggestion2>"]
  },
  "expected_decision": {
    "score": <1-5>,
    "analysis": "<detailed analysis>",
    "quotes": ["<quote1>", "<quote2>"],
    "suggestions": ["<suggestion1>", "<suggestion2>"]
  },
  "decision_criteria": {
    "score": <1-5>,
    "analysis": "<detailed analysis>",
    "quotes": ["<quote1>", "<quote2>"],
    "suggestions": ["<suggestion1>", "<suggestion2>"]
  },
  "summary": "<2-3 sentence executive summary of the call>",
  "key_insights": ["<insight1>", "<insight2>", "<insight3>"],
  "recommended_next_steps": ["<step1>", "<step2>", "<step3>"],
  "coaching_recommendations": ["<recommendation1>", "<recommendation2>"]
}
```
"""


class SPICEDAnalyzer:
    """Analyzes sales call transcripts using SPICED methodology."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the analyzer.

        Args:
            api_key: Anthropic API key, defaults to settings
        """
        self.api_key = api_key or settings.anthropic_api_key

    async def analyze(self, transcript_text: str) -> Dict[str, Any]:
        """Analyze a transcript using SPICED methodology.

        Args:
            transcript_text: The full transcript text

        Returns:
            SPICED analysis results
        """
        if not self.api_key:
            logger.warning("No Anthropic API key configured, returning mock analysis")
            return self._get_mock_analysis()

        try:
            import anthropic

            client = anthropic.AsyncAnthropic(api_key=self.api_key)

            prompt = SPICED_EXTRACTION_PROMPT.format(transcript=transcript_text)

            message = await client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            # Extract JSON from response
            response_text = message.content[0].text

            # Find JSON in the response
            import json
            import re

            # Try to find JSON block
            json_match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Assume the whole response is JSON
                json_str = response_text

            analysis = json.loads(json_str)

            # Calculate overall score
            scores = [
                analysis["situation"]["score"],
                analysis["pain"]["score"],
                analysis["impact"]["score"],
                analysis["critical_event"]["score"],
                analysis["expected_decision"]["score"],
                analysis["decision_criteria"]["score"],
            ]
            analysis["overall_score"] = sum(scores) / len(scores)

            return analysis

        except ImportError:
            logger.error("anthropic package not installed")
            return self._get_mock_analysis()
        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            return self._get_mock_analysis()

    def _get_mock_analysis(self) -> Dict[str, Any]:
        """Return a mock analysis for testing/development."""
        return {
            "situation": {
                "score": 3,
                "analysis": "The prospect's current situation was partially explored.",
                "quotes": [],
                "suggestions": [
                    "Ask more about their current tech stack",
                    "Explore team size and structure",
                ],
            },
            "pain": {
                "score": 3,
                "analysis": "Some pain points were identified but not deeply explored.",
                "quotes": [],
                "suggestions": [
                    "Ask 'What happens when...' questions",
                    "Probe deeper into specific frustrations",
                ],
            },
            "impact": {
                "score": 2,
                "analysis": "Business impact was briefly mentioned but not quantified.",
                "quotes": [],
                "suggestions": [
                    "Ask about time lost to current process",
                    "Explore revenue impact of the problem",
                ],
            },
            "critical_event": {
                "score": 2,
                "analysis": "No clear timeline or urgency driver was established.",
                "quotes": [],
                "suggestions": [
                    "Ask 'Why now?' directly",
                    "Explore upcoming deadlines or events",
                ],
            },
            "expected_decision": {
                "score": 3,
                "analysis": "Decision process was partially discussed.",
                "quotes": [],
                "suggestions": [
                    "Identify all stakeholders in the decision",
                    "Understand their evaluation timeline",
                ],
            },
            "decision_criteria": {
                "score": 2,
                "analysis": "Decision criteria were not explicitly discussed.",
                "quotes": [],
                "suggestions": [
                    "Ask what features matter most",
                    "Understand their must-haves vs nice-to-haves",
                ],
            },
            "overall_score": 2.5,
            "summary": "This call covered basic discovery but missed opportunities to explore impact and urgency.",
            "key_insights": [
                "Prospect is evaluating solutions",
                "Pain exists but impact not quantified",
                "Decision timeline unclear",
            ],
            "recommended_next_steps": [
                "Send follow-up email summarizing discussion",
                "Schedule deeper dive on business impact",
                "Identify other stakeholders to include",
            ],
            "coaching_recommendations": [
                "Practice asking impact-focused questions",
                "Work on establishing urgency earlier in calls",
            ],
        }
