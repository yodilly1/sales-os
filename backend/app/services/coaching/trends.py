"""
Trend Analysis Service

Analyzes SPICED scores over time to identify patterns,
trends, and improvement opportunities for sales reps.
"""

import logging
from datetime import datetime
from statistics import mean, stdev
from typing import Optional
from uuid import UUID

from ...models.coaching import (
    ElementTrend,
    ImprovementFocus,
    ImprovementGoal,
    ScoreHistoryEntry,
    SPICEDElement,
    StrongestArea,
    TrendAnalysisReport,
    TrendDirection,
    TrendPattern,
)

logger = logging.getLogger(__name__)


class TrendAnalysisService:
    """
    Analyzes SPICED score trends over time.

    Provides:
    - Element-by-element trend analysis
    - Pattern recognition
    - Goal recommendations
    """

    # Threshold for determining if a trend is significant
    TREND_THRESHOLD = 0.3

    # Threshold for determining volatility
    VOLATILITY_THRESHOLD = 0.8

    async def analyze_trends(
        self,
        rep_id: UUID,
        rep_name: str,
        entries: list[ScoreHistoryEntry],
    ) -> TrendAnalysisReport:
        """
        Analyze trends for a rep's SPICED scores over time.

        Args:
            rep_id: ID of the sales rep
            rep_name: Name of the sales rep
            entries: List of historical score entries

        Returns:
            Comprehensive trend analysis report
        """
        if len(entries) < 3:
            raise ValueError("Need at least 3 data points for trend analysis")

        logger.info(f"Analyzing trends for {rep_name} with {len(entries)} entries")

        # Sort entries by date
        sorted_entries = sorted(entries, key=lambda e: e.call_date)

        # Analyze trends for each element
        element_trends = self._analyze_element_trends(sorted_entries)

        # Calculate overall trend
        overall_trend = self._calculate_overall_trend(sorted_entries)

        # Calculate overall averages
        first_half = sorted_entries[:len(sorted_entries) // 2]
        second_half = sorted_entries[len(sorted_entries) // 2:]

        overall_avg_start = mean(e.overall_score for e in first_half)
        overall_avg_end = mean(e.overall_score for e in second_half)

        # Find strongest and weakest areas
        strongest_areas = self._find_strongest_areas(element_trends)
        improvement_areas = self._find_improvement_areas(element_trends)

        # Identify patterns
        patterns = self._identify_patterns(sorted_entries, element_trends)

        # Generate goals
        goals = self._generate_goals(improvement_areas, element_trends)

        # Calculate next review date (typically 2 weeks from now)
        from datetime import timedelta
        next_review = datetime.utcnow() + timedelta(weeks=2)

        return TrendAnalysisReport(
            rep_id=rep_id,
            rep_name=rep_name,
            analysis_period_start=sorted_entries[0].call_date,
            analysis_period_end=sorted_entries[-1].call_date,
            total_calls_analyzed=len(entries),
            element_trends=element_trends,
            overall_trend=overall_trend,
            overall_avg_start=round(overall_avg_start, 2),
            overall_avg_end=round(overall_avg_end, 2),
            strongest_areas=strongest_areas,
            improvement_areas=improvement_areas,
            patterns=patterns,
            goals=goals,
            next_review_date=next_review,
        )

    def _analyze_element_trends(
        self,
        entries: list[ScoreHistoryEntry],
    ) -> dict[SPICEDElement, ElementTrend]:
        """Analyze trends for each SPICED element."""
        trends = {}

        for element in SPICEDElement:
            element_key = element.value

            # Extract scores for this element
            scores = [
                e.scores.get(element_key, 3)
                for e in entries
            ]

            if len(scores) < 3:
                continue

            # Calculate start and end averages
            first_half = scores[:len(scores) // 2]
            second_half = scores[len(scores) // 2:]

            start_avg = mean(first_half)
            end_avg = mean(second_half)
            change = end_avg - start_avg

            # Determine direction
            if change > self.TREND_THRESHOLD:
                direction = TrendDirection.IMPROVING
            elif change < -self.TREND_THRESHOLD:
                direction = TrendDirection.DECLINING
            else:
                direction = TrendDirection.STABLE

            # Determine consistency
            try:
                score_stdev = stdev(scores)
                consistency = "volatile" if score_stdev > self.VOLATILITY_THRESHOLD else "steady"
            except Exception:
                consistency = "steady"

            trends[element] = ElementTrend(
                element=element,
                direction=direction,
                start_avg=round(start_avg, 2),
                end_avg=round(end_avg, 2),
                change=round(change, 2),
                consistency=consistency,
                scores_history=[float(s) for s in scores],
            )

        return trends

    def _calculate_overall_trend(
        self,
        entries: list[ScoreHistoryEntry],
    ) -> TrendDirection:
        """Calculate the overall trend direction."""
        scores = [e.overall_score for e in entries]

        if len(scores) < 3:
            return TrendDirection.STABLE

        first_half = scores[:len(scores) // 2]
        second_half = scores[len(scores) // 2:]

        change = mean(second_half) - mean(first_half)

        if change > self.TREND_THRESHOLD:
            return TrendDirection.IMPROVING
        elif change < -self.TREND_THRESHOLD:
            return TrendDirection.DECLINING
        else:
            return TrendDirection.STABLE

    def _find_strongest_areas(
        self,
        element_trends: dict[SPICEDElement, ElementTrend],
    ) -> list[StrongestArea]:
        """Find the rep's strongest SPICED elements."""
        # Sort by end average (current performance)
        sorted_elements = sorted(
            element_trends.items(),
            key=lambda x: x[1].end_avg,
            reverse=True,
        )

        strongest = []
        for element, trend in sorted_elements[:2]:
            insight = self._generate_strength_insight(element, trend)
            strongest.append(StrongestArea(
                element=element,
                avg_score=trend.end_avg,
                insight=insight,
            ))

        return strongest

    def _find_improvement_areas(
        self,
        element_trends: dict[SPICEDElement, ElementTrend],
    ) -> list[ImprovementFocus]:
        """Find areas most in need of improvement."""
        # Sort by end average (lowest = most needs improvement)
        sorted_elements = sorted(
            element_trends.items(),
            key=lambda x: x[1].end_avg,
        )

        improvements = []
        for element, trend in sorted_elements[:2]:
            gap_analysis = self._generate_gap_analysis(element, trend)
            action = self._generate_improvement_action(element, trend)
            improvements.append(ImprovementFocus(
                element=element,
                avg_score=trend.end_avg,
                gap_analysis=gap_analysis,
                recommended_action=action,
            ))

        return improvements

    def _identify_patterns(
        self,
        entries: list[ScoreHistoryEntry],
        element_trends: dict[SPICEDElement, ElementTrend],
    ) -> list[TrendPattern]:
        """Identify patterns in the rep's performance."""
        patterns = []

        # Pattern 1: Consistent improver
        improving_count = sum(
            1 for t in element_trends.values()
            if t.direction == TrendDirection.IMPROVING
        )
        if improving_count >= 4:
            patterns.append(TrendPattern(
                pattern="Consistent improvement across multiple elements",
                insight="Strong growth trajectory showing dedication to skill development",
                recommendation="Continue current practice habits while focusing on remaining gaps",
            ))

        # Pattern 2: Volatile performer
        volatile_count = sum(
            1 for t in element_trends.values()
            if t.consistency == "volatile"
        )
        if volatile_count >= 3:
            patterns.append(TrendPattern(
                pattern="Inconsistent performance across calls",
                insight="Scores vary significantly, possibly due to different call contexts or preparation levels",
                recommendation="Focus on consistent preparation and structured discovery approach",
            ))

        # Pattern 3: Impact gap (common issue)
        if SPICEDElement.IMPACT in element_trends:
            impact_trend = element_trends[SPICEDElement.IMPACT]
            if impact_trend.end_avg < 3.0:
                patterns.append(TrendPattern(
                    pattern="Quantification gap in Impact discussions",
                    insight="Consistently missing opportunities to quantify business impact",
                    recommendation="Add 'What does that cost you?' to your standard question set",
                ))

        # Pattern 4: Strong opener, weak closer
        situation_score = element_trends.get(SPICEDElement.SITUATION, None)
        decision_score = element_trends.get(SPICEDElement.EXPECTED_DECISION, None)
        if situation_score and decision_score:
            if situation_score.end_avg >= 4.0 and decision_score.end_avg < 3.0:
                patterns.append(TrendPattern(
                    pattern="Strong situation discovery, weak stakeholder mapping",
                    insight="Excellent at understanding current state but missing decision process details",
                    recommendation="Add stakeholder questions to call structure after situational discovery",
                ))

        # Pattern 5: Call type correlation
        discovery_calls = [e for e in entries if e.call_type.value == "discovery"]
        demo_calls = [e for e in entries if e.call_type.value == "demo"]

        if len(discovery_calls) >= 3 and len(demo_calls) >= 3:
            discovery_avg = mean(e.overall_score for e in discovery_calls)
            demo_avg = mean(e.overall_score for e in demo_calls)

            if discovery_avg > demo_avg + 0.5:
                patterns.append(TrendPattern(
                    pattern="Stronger discovery than demo calls",
                    insight="SPICED skills drop during demos, possibly due to premature pitching",
                    recommendation="Maintain discovery mindset during demos - continue asking questions",
                ))
            elif demo_avg > discovery_avg + 0.5:
                patterns.append(TrendPattern(
                    pattern="Stronger demo than discovery calls",
                    insight="Better SPICED execution when product is involved",
                    recommendation="Use product references during discovery to anchor questions",
                ))

        return patterns[:5]  # Limit to 5 patterns

    def _generate_goals(
        self,
        improvement_areas: list[ImprovementFocus],
        element_trends: dict[SPICEDElement, ElementTrend],
    ) -> list[ImprovementGoal]:
        """Generate improvement goals based on analysis."""
        goals = []

        for area in improvement_areas[:3]:
            trend = element_trends.get(area.element)
            if not trend:
                continue

            # Set target based on current score
            current = trend.end_avg
            if current < 2.5:
                target = 3.0
                timeframe = "6 weeks"
            elif current < 3.5:
                target = 4.0
                timeframe = "4 weeks"
            else:
                target = 4.5
                timeframe = "4 weeks"

            action_plan = self._get_action_plan(area.element, current)

            goals.append(ImprovementGoal(
                element=area.element,
                current_avg=current,
                target_score=target,
                timeframe=timeframe,
                action_plan=action_plan,
            ))

        return goals

    def _generate_strength_insight(self, element: SPICEDElement, trend: ElementTrend) -> str:
        """Generate insight text for a strength."""
        insights = {
            SPICEDElement.SITUATION: "Strong ability to understand and map the prospect's current state",
            SPICEDElement.PAIN: "Effective at uncovering and validating prospect challenges",
            SPICEDElement.IMPACT: "Excellent at quantifying business impact and building urgency",
            SPICEDElement.CRITICAL_EVENT: "Skilled at identifying timeline drivers and creating urgency",
            SPICEDElement.EXPECTED_DECISION: "Strong stakeholder mapping and decision process understanding",
            SPICEDElement.DECISION_CRITERIA: "Effective at uncovering evaluation criteria and success metrics",
        }
        return insights.get(element, "Strong performance in this area")

    def _generate_gap_analysis(self, element: SPICEDElement, trend: ElementTrend) -> str:
        """Generate gap analysis text for an improvement area."""
        gaps = {
            SPICEDElement.SITUATION: "Limited exploration of current tools, processes, or team structure",
            SPICEDElement.PAIN: "Surface-level pain identification without deeper validation",
            SPICEDElement.IMPACT: "Missing quantification of business impact in time or dollars",
            SPICEDElement.CRITICAL_EVENT: "No clear timeline driver or urgency established",
            SPICEDElement.EXPECTED_DECISION: "Single-threaded with unclear decision process",
            SPICEDElement.DECISION_CRITERIA: "Vague or assumed requirements without validation",
        }
        return gaps.get(element, "Room for improvement in this area")

    def _generate_improvement_action(self, element: SPICEDElement, trend: ElementTrend) -> str:
        """Generate recommended action for an improvement area."""
        actions = {
            SPICEDElement.SITUATION: "Add 'Walk me through a typical day' to your opening questions",
            SPICEDElement.PAIN: "Use the '5 Whys' technique to dig deeper on stated challenges",
            SPICEDElement.IMPACT: "Always ask 'What does that cost you?' after identifying pain",
            SPICEDElement.CRITICAL_EVENT: "Ask 'What's driving the timing on this?' in every call",
            SPICEDElement.EXPECTED_DECISION: "Add 'Who else should be involved?' to your question list",
            SPICEDElement.DECISION_CRITERIA: "Ask 'How will you know if this is successful?' before closing",
        }
        return actions.get(element, "Focus practice time on this element")

    def _get_action_plan(self, element: SPICEDElement, current_score: float) -> str:
        """Get a detailed action plan for improving an element."""
        plans = {
            SPICEDElement.SITUATION: (
                "1) Review WbD situation questions list. "
                "2) Practice 'paint me a picture' technique. "
                "3) Include team structure and tools in every discovery."
            ),
            SPICEDElement.PAIN: (
                "1) Use 5 Whys on every pain point. "
                "2) Categorize pain (process, people, tech, financial). "
                "3) Validate assumptions by restating and confirming."
            ),
            SPICEDElement.IMPACT: (
                "1) Add 'What does that cost you?' to standard questions. "
                "2) Use CFO framing: 'What would your CFO say this costs?'. "
                "3) Quantify in time, money, or risk for every call."
            ),
            SPICEDElement.CRITICAL_EVENT: (
                "1) Ask 'Why now?' in every discovery. "
                "2) Explore consequences of inaction. "
                "3) Connect to external events (fiscal year, board meetings, etc.)."
            ),
            SPICEDElement.EXPECTED_DECISION: (
                "1) Ask about stakeholders early. "
                "2) Map the buying committee. "
                "3) Understand approval process and budget authority."
            ),
            SPICEDElement.DECISION_CRITERIA: (
                "1) Ask 'What does success look like?'. "
                "2) Prioritize must-haves vs nice-to-haves. "
                "3) Align our strengths to their criteria."
            ),
        }
        return plans.get(element, "Focus dedicated practice time on this skill")
