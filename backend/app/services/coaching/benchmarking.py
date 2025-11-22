"""
Team Benchmarking Service

Compares SPICED scores across team members to identify
top performers, coaching opportunities, and team-wide gaps.
"""

import logging
from datetime import datetime
from statistics import mean
from typing import Optional
from uuid import UUID

from ...models.coaching import (
    BestPractice,
    IndividualBenchmark,
    MentoringOpportunity,
    PerformanceDistribution,
    PerformanceTier,
    RepScoreHistory,
    SPICEDElement,
    TeamBenchmarkReport,
    TeamElementAverages,
)

logger = logging.getLogger(__name__)


class TeamBenchmarkingService:
    """
    Benchmarks individual rep performance against team averages.

    Provides:
    - Team-wide scoring averages
    - Individual comparisons and percentiles
    - Mentoring opportunity identification
    - Best practice extraction
    """

    # Tier thresholds
    HIGH_PERFORMER_THRESHOLD = 4.0
    SOLID_PERFORMER_THRESHOLD = 3.0

    async def generate_benchmark(
        self,
        team_id: UUID,
        team_name: str,
        rep_histories: list[RepScoreHistory],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> TeamBenchmarkReport:
        """
        Generate a team benchmarking report.

        Args:
            team_id: ID of the team
            team_name: Name of the team
            rep_histories: Score histories for all team members
            start_date: Optional start of analysis period
            end_date: Optional end of analysis period

        Returns:
            Comprehensive team benchmark report
        """
        if len(rep_histories) < 2:
            raise ValueError("Need at least 2 reps for team benchmarking")

        logger.info(f"Generating benchmark for team {team_name} with {len(rep_histories)} reps")

        # Calculate team element averages
        element_averages = self._calculate_element_averages(rep_histories)

        # Calculate overall team average
        all_scores = []
        total_calls = 0
        for history in rep_histories:
            for entry in history.entries:
                all_scores.append(entry.overall_score)
                total_calls += 1

        avg_overall_score = round(mean(all_scores), 2) if all_scores else 3.0

        # Generate individual benchmarks
        individual_benchmarks = self._generate_individual_benchmarks(
            rep_histories,
            element_averages,
        )

        # Calculate performance distribution
        performance_distribution = self._calculate_distribution(individual_benchmarks)

        # Find strongest and weakest elements
        element_scores = {
            SPICEDElement.SITUATION: element_averages.situation,
            SPICEDElement.PAIN: element_averages.pain,
            SPICEDElement.IMPACT: element_averages.impact,
            SPICEDElement.CRITICAL_EVENT: element_averages.critical_event,
            SPICEDElement.EXPECTED_DECISION: element_averages.expected_decision,
            SPICEDElement.DECISION_CRITERIA: element_averages.decision_criteria,
        }

        strongest = max(element_scores.items(), key=lambda x: x[1])
        weakest = min(element_scores.items(), key=lambda x: x[1])

        # Generate mentoring opportunities
        mentoring_opportunities = self._identify_mentoring_opportunities(
            individual_benchmarks,
            rep_histories,
        )

        # Extract best practices
        best_practices = self._extract_best_practices(
            individual_benchmarks,
            element_averages,
        )

        # Generate recommended actions
        actions = self._generate_team_actions(
            weakest[0],
            performance_distribution,
            individual_benchmarks,
        )

        # Determine date range
        all_dates = []
        for history in rep_histories:
            for entry in history.entries:
                all_dates.append(entry.call_date)

        period_start = start_date or min(all_dates) if all_dates else datetime.utcnow()
        period_end = end_date or max(all_dates) if all_dates else datetime.utcnow()

        return TeamBenchmarkReport(
            team_id=team_id,
            team_name=team_name,
            total_reps=len(rep_histories),
            total_calls_analyzed=total_calls,
            analysis_period_start=period_start,
            analysis_period_end=period_end,
            avg_overall_score=avg_overall_score,
            element_averages=element_averages,
            performance_distribution=performance_distribution,
            individual_benchmarks=individual_benchmarks,
            strongest_element=strongest[0],
            strongest_element_score=strongest[1],
            weakest_element=weakest[0],
            weakest_element_score=weakest[1],
            recommended_training=self._get_training_recommendation(weakest[0]),
            mentoring_opportunities=mentoring_opportunities,
            best_practices=best_practices,
            immediate_actions=actions["immediate"],
            short_term_actions=actions["short_term"],
            long_term_actions=actions["long_term"],
        )

    def _calculate_element_averages(
        self,
        rep_histories: list[RepScoreHistory],
    ) -> TeamElementAverages:
        """Calculate team-wide averages for each SPICED element."""
        element_scores: dict[str, list[float]] = {
            "situation": [],
            "pain": [],
            "impact": [],
            "critical_event": [],
            "expected_decision": [],
            "decision_criteria": [],
        }

        for history in rep_histories:
            for entry in history.entries:
                for element, score in entry.scores.items():
                    if element in element_scores:
                        element_scores[element].append(float(score))

        return TeamElementAverages(
            situation=round(mean(element_scores["situation"]), 2) if element_scores["situation"] else 3.0,
            pain=round(mean(element_scores["pain"]), 2) if element_scores["pain"] else 3.0,
            impact=round(mean(element_scores["impact"]), 2) if element_scores["impact"] else 3.0,
            critical_event=round(mean(element_scores["critical_event"]), 2) if element_scores["critical_event"] else 3.0,
            expected_decision=round(mean(element_scores["expected_decision"]), 2) if element_scores["expected_decision"] else 3.0,
            decision_criteria=round(mean(element_scores["decision_criteria"]), 2) if element_scores["decision_criteria"] else 3.0,
        )

    def _generate_individual_benchmarks(
        self,
        rep_histories: list[RepScoreHistory],
        team_averages: TeamElementAverages,
    ) -> list[IndividualBenchmark]:
        """Generate benchmark data for each rep compared to team."""
        benchmarks = []

        # Calculate each rep's average
        rep_averages = []
        for history in rep_histories:
            if history.average_overall_score is not None:
                rep_averages.append((history, history.average_overall_score))

        # Sort for percentile calculation
        sorted_by_avg = sorted(rep_averages, key=lambda x: x[1])

        for history, avg in rep_averages:
            # Calculate percentile
            rank = sorted_by_avg.index((history, avg))
            percentile = int((rank / len(sorted_by_avg)) * 100)

            # Determine tier
            if avg >= self.HIGH_PERFORMER_THRESHOLD:
                tier = PerformanceTier.HIGH_PERFORMER
            elif avg >= self.SOLID_PERFORMER_THRESHOLD:
                tier = PerformanceTier.SOLID_PERFORMER
            else:
                tier = PerformanceTier.DEVELOPING

            # Calculate element averages for this rep
            rep_element_avgs = self._calculate_rep_element_averages(history)

            # Find strengths (above team avg) and gaps (below team avg)
            team_avgs_dict = {
                SPICEDElement.SITUATION: team_averages.situation,
                SPICEDElement.PAIN: team_averages.pain,
                SPICEDElement.IMPACT: team_averages.impact,
                SPICEDElement.CRITICAL_EVENT: team_averages.critical_event,
                SPICEDElement.EXPECTED_DECISION: team_averages.expected_decision,
                SPICEDElement.DECISION_CRITERIA: team_averages.decision_criteria,
            }

            strengths = []
            gaps = []

            for element, team_avg in team_avgs_dict.items():
                rep_avg = rep_element_avgs.get(element.value, 3.0)
                if rep_avg > team_avg + 0.2:
                    strengths.append(element)
                elif rep_avg < team_avg - 0.2:
                    gaps.append(element)

            # Determine priority focus
            if gaps:
                priority_focus = self._get_priority_focus(gaps[0])
            else:
                priority_focus = "Continue current practice and mentor others"

            benchmarks.append(IndividualBenchmark(
                rep_id=history.rep_id,
                rep_name=history.rep_name,
                overall_avg=round(avg, 2),
                percentile=percentile,
                tier=tier,
                strengths=strengths,
                gaps=gaps,
                priority_focus=priority_focus,
                calls_analyzed=len(history.entries),
            ))

        return benchmarks

    def _calculate_rep_element_averages(
        self,
        history: RepScoreHistory,
    ) -> dict[str, float]:
        """Calculate element averages for a single rep."""
        element_scores: dict[str, list[float]] = {
            "situation": [],
            "pain": [],
            "impact": [],
            "critical_event": [],
            "expected_decision": [],
            "decision_criteria": [],
        }

        for entry in history.entries:
            for element, score in entry.scores.items():
                if element in element_scores:
                    element_scores[element].append(float(score))

        return {
            element: round(mean(scores), 2) if scores else 3.0
            for element, scores in element_scores.items()
        }

    def _calculate_distribution(
        self,
        benchmarks: list[IndividualBenchmark],
    ) -> PerformanceDistribution:
        """Calculate performance tier distribution."""
        high = [b.rep_name for b in benchmarks if b.tier == PerformanceTier.HIGH_PERFORMER]
        solid = [b.rep_name for b in benchmarks if b.tier == PerformanceTier.SOLID_PERFORMER]
        developing = [b.rep_name for b in benchmarks if b.tier == PerformanceTier.DEVELOPING]

        return PerformanceDistribution(
            high_performers=high,
            solid_performers=solid,
            developing=developing,
        )

    def _identify_mentoring_opportunities(
        self,
        benchmarks: list[IndividualBenchmark],
        histories: list[RepScoreHistory],
    ) -> list[MentoringOpportunity]:
        """Identify opportunities for peer mentoring."""
        opportunities = []

        # Find high performers with specific strengths
        high_performers = [b for b in benchmarks if b.tier == PerformanceTier.HIGH_PERFORMER]

        for element in SPICEDElement:
            # Find mentor (high performer strong in this element)
            potential_mentors = [
                b for b in high_performers
                if element in b.strengths
            ]

            if not potential_mentors:
                continue

            mentor = potential_mentors[0]

            # Find mentees (those with this element as a gap)
            mentees = [
                b.rep_name for b in benchmarks
                if element in b.gaps and b.rep_name != mentor.rep_name
            ]

            if mentees:
                opportunities.append(MentoringOpportunity(
                    mentor_name=mentor.rep_name,
                    mentor_id=mentor.rep_id,
                    skill=element,
                    mentees=mentees[:3],  # Limit to 3 mentees
                ))

        return opportunities[:5]  # Limit to 5 opportunities

    def _extract_best_practices(
        self,
        benchmarks: list[IndividualBenchmark],
        team_averages: TeamElementAverages,
    ) -> list[BestPractice]:
        """Extract best practices from top performers."""
        practices = []

        # Map elements to generic best practice talk tracks
        practice_templates = {
            SPICEDElement.SITUATION: {
                "technique": "Deep situational mapping",
                "talk_track": "Walk me through a typical day for your team when handling [process]...",
            },
            SPICEDElement.PAIN: {
                "technique": "5 Whys pain excavation",
                "talk_track": "That's interesting - why do you think that happens? And what drives that?",
            },
            SPICEDElement.IMPACT: {
                "technique": "CFO framing for quantification",
                "talk_track": "If your CFO asked what this costs the company, what would you tell them?",
            },
            SPICEDElement.CRITICAL_EVENT: {
                "technique": "Urgency anchoring",
                "talk_track": "What happens if this isn't solved by [date]? What are the consequences?",
            },
            SPICEDElement.EXPECTED_DECISION: {
                "technique": "Early stakeholder mapping",
                "talk_track": "Who else would need to weigh in before making a decision like this?",
            },
            SPICEDElement.DECISION_CRITERIA: {
                "technique": "Success criteria alignment",
                "talk_track": "How will you measure success if we were to move forward?",
            },
        }

        # Find high performers for each element
        high_performers = [b for b in benchmarks if b.tier == PerformanceTier.HIGH_PERFORMER]

        for element in SPICEDElement:
            experts = [b for b in high_performers if element in b.strengths]
            if experts:
                template = practice_templates.get(element, {})
                practices.append(BestPractice(
                    technique=template.get("technique", f"Excellence in {element.value}"),
                    example_rep=experts[0].rep_name,
                    talk_track=template.get("talk_track", "Ask open-ended questions"),
                    applicable_to=element,
                ))

        return practices[:5]

    def _generate_team_actions(
        self,
        weakest_element: SPICEDElement,
        distribution: PerformanceDistribution,
        benchmarks: list[IndividualBenchmark],
    ) -> dict[str, list[str]]:
        """Generate prioritized team actions."""
        actions = {
            "immediate": [],
            "short_term": [],
            "long_term": [],
        }

        # Immediate: Address developing reps
        if distribution.developing:
            actions["immediate"].append(
                f"Schedule 1:1 coaching sessions with developing reps: {', '.join(distribution.developing)}"
            )

        # Immediate: Team-wide skill gap
        actions["immediate"].append(
            f"Run team training on {weakest_element.value.replace('_', ' ')} - current team gap"
        )

        # Short-term: Establish mentoring
        if distribution.high_performers and (distribution.solid_performers or distribution.developing):
            actions["short_term"].append(
                f"Pair high performers ({', '.join(distribution.high_performers[:2])}) with developing reps for peer coaching"
            )

        # Short-term: Call review sessions
        actions["short_term"].append(
            "Establish weekly call review sessions focusing on SPICED elements"
        )

        # Short-term: Practice sessions
        actions["short_term"].append(
            f"Role-play sessions focusing on {weakest_element.value.replace('_', ' ')} improvement"
        )

        # Long-term: Certification program
        actions["long_term"].append(
            "Implement SPICED certification levels (Bronze: 3.0+, Silver: 3.5+, Gold: 4.0+)"
        )

        # Long-term: Regular benchmarking
        actions["long_term"].append(
            "Monthly team benchmark reviews with goal setting and recognition"
        )

        # Long-term: Best practice library
        actions["long_term"].append(
            "Build internal library of best practice call recordings by SPICED element"
        )

        return actions

    def _get_training_recommendation(self, element: SPICEDElement) -> str:
        """Get training recommendation for a specific element."""
        recommendations = {
            SPICEDElement.SITUATION: "Workshop on comprehensive situational discovery - mapping current state, tools, and team dynamics",
            SPICEDElement.PAIN: "Training on pain excavation techniques - the 5 Whys, pain categorization, and validation",
            SPICEDElement.IMPACT: "Impact quantification bootcamp - translating pain to business metrics and ROI",
            SPICEDElement.CRITICAL_EVENT: "Urgency creation training - identifying and leveraging timeline drivers",
            SPICEDElement.EXPECTED_DECISION: "Stakeholder mapping workshop - identifying and engaging the buying committee",
            SPICEDElement.DECISION_CRITERIA: "Criteria alignment training - uncovering requirements and positioning strengths",
        }
        return recommendations.get(element, "General SPICED methodology training")

    def _get_priority_focus(self, element: SPICEDElement) -> str:
        """Get priority focus message for an element gap."""
        focuses = {
            SPICEDElement.SITUATION: "Focus on deeper situational discovery - understand the full context before exploring pain",
            SPICEDElement.PAIN: "Dig deeper on pain points - don't accept surface-level challenges, use follow-up questions",
            SPICEDElement.IMPACT: "Quantify every pain point - always ask about the cost in time, money, or risk",
            SPICEDElement.CRITICAL_EVENT: "Establish urgency - understand why now and what happens if they don't act",
            SPICEDElement.EXPECTED_DECISION: "Map stakeholders early - never stay single-threaded past first call",
            SPICEDElement.DECISION_CRITERIA: "Clarify success criteria - understand how they'll evaluate and what matters most",
        }
        return focuses.get(element, "Continue developing overall SPICED skills")
