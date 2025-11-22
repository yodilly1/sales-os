"""
Analytics API endpoints for Sales OS.

Provides comprehensive analytics for:
- Call metrics (volume, duration, SPICED scores)
- Content metrics (generated, downloaded, shared)
- Pipeline metrics (prospects, conversions)
- Team performance (leaderboards, trends)
"""

from datetime import datetime, timedelta
from typing import Optional, Literal
from io import BytesIO
import csv
import random

from fastapi import APIRouter, Query, Response
from fastapi.responses import StreamingResponse

from app.models.analytics import (
    AnalyticsResponse,
    PaginatedResponse,
    MetricValue,
    CallMetrics,
    CallVolumeData,
    CallDurationData,
    SpicedScoreData,
    SpicedDistribution,
    ContentMetrics,
    ContentTypeData,
    ContentTrendData,
    ContentPerformance,
    PipelineMetrics,
    PipelineStageData,
    EnrichmentTrendData,
    ProspectSource,
    TeamMetrics,
    TeamMemberPerformance,
    TeamTrendData,
    LeaderboardEntry,
)

router = APIRouter()


def generate_date_range(start_date: str, end_date: str) -> list[str]:
    """Generate a list of dates between start and end."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    return dates


def make_metric_value(value: float, change_pct: float) -> MetricValue:
    """Create a MetricValue with calculated change."""
    change = value * (change_pct / 100)
    trend: Literal["up", "down", "stable"] = "up" if change_pct > 0 else "down" if change_pct < 0 else "stable"
    return MetricValue(
        value=value,
        change=change,
        change_percent=change_pct,
        trend=trend,
    )


# ============================================
# Call Analytics Endpoints
# ============================================

@router.get("/calls/metrics")
async def get_call_metrics(
    startDate: str = Query(..., description="Start date (YYYY-MM-DD)"),
    endDate: str = Query(..., description="End date (YYYY-MM-DD)"),
) -> AnalyticsResponse:
    """Get call analytics summary metrics."""
    metrics = CallMetrics(
        total_calls=make_metric_value(560, 9.4),
        avg_duration=make_metric_value(27, 12.5),
        avg_spiced_score=make_metric_value(7.5, 5.6),
        conversion_rate=make_metric_value(94.2, 1.4),
    )
    return AnalyticsResponse(
        data=metrics.model_dump(by_alias=True),
        date_range={"startDate": startDate, "endDate": endDate},
        generated_at=datetime.utcnow(),
    )


@router.get("/calls/volume")
async def get_call_volume(
    startDate: str = Query(..., description="Start date (YYYY-MM-DD)"),
    endDate: str = Query(..., description="End date (YYYY-MM-DD)"),
) -> AnalyticsResponse:
    """Get daily call volume data."""
    dates = generate_date_range(startDate, endDate)
    data = []
    for date in dates[:30]:  # Limit to 30 days for demo
        total = random.randint(40, 70)
        answered = int(total * random.uniform(0.9, 0.98))
        data.append(CallVolumeData(
            date=date,
            calls=total,
            answered=answered,
            missed=total - answered,
        ))
    return AnalyticsResponse(
        data=[d.model_dump() for d in data],
        date_range={"startDate": startDate, "endDate": endDate},
        generated_at=datetime.utcnow(),
    )


@router.get("/calls/duration")
async def get_call_duration(
    startDate: str = Query(..., description="Start date (YYYY-MM-DD)"),
    endDate: str = Query(..., description="End date (YYYY-MM-DD)"),
) -> AnalyticsResponse:
    """Get daily call duration data."""
    dates = generate_date_range(startDate, endDate)
    data = []
    for date in dates[:30]:
        avg = random.uniform(22, 35)
        data.append(CallDurationData(
            date=date,
            avg_duration=round(avg, 1),
            min_duration=round(avg * random.uniform(0.2, 0.4), 1),
            max_duration=round(avg * random.uniform(1.5, 2.0), 1),
        ))
    return AnalyticsResponse(
        data=[d.model_dump(by_alias=True) for d in data],
        date_range={"startDate": startDate, "endDate": endDate},
        generated_at=datetime.utcnow(),
    )


@router.get("/calls/spiced-scores")
async def get_spiced_scores(
    startDate: str = Query(..., description="Start date (YYYY-MM-DD)"),
    endDate: str = Query(..., description="End date (YYYY-MM-DD)"),
) -> AnalyticsResponse:
    """Get daily SPICED score data."""
    dates = generate_date_range(startDate, endDate)
    data = []
    for date in dates[:30]:
        base = random.uniform(6.5, 8.5)
        data.append(SpicedScoreData(
            date=date,
            situation=round(base + random.uniform(-0.5, 0.5), 1),
            pain=round(base + random.uniform(-0.8, 0.2), 1),
            impact=round(base + random.uniform(-0.3, 0.3), 1),
            critical_event=round(base + random.uniform(-1.0, 0), 1),
            decision=round(base + random.uniform(-0.4, 0.4), 1),
            overall=round(base, 1),
        ))
    return AnalyticsResponse(
        data=[d.model_dump(by_alias=True) for d in data],
        date_range={"startDate": startDate, "endDate": endDate},
        generated_at=datetime.utcnow(),
    )


@router.get("/calls/spiced-distribution")
async def get_spiced_distribution(
    startDate: str = Query(..., description="Start date (YYYY-MM-DD)"),
    endDate: str = Query(..., description="End date (YYYY-MM-DD)"),
) -> AnalyticsResponse:
    """Get SPICED score distribution."""
    data = [
        SpicedDistribution(range="Excellent (8-10)", count=140, percentage=25),
        SpicedDistribution(range="Good (6-8)", count=252, percentage=45),
        SpicedDistribution(range="Average (4-6)", count=112, percentage=20),
        SpicedDistribution(range="Needs Work (0-4)", count=56, percentage=10),
    ]
    return AnalyticsResponse(
        data=[d.model_dump() for d in data],
        date_range={"startDate": startDate, "endDate": endDate},
        generated_at=datetime.utcnow(),
    )


# ============================================
# Content Analytics Endpoints
# ============================================

@router.get("/content/metrics")
async def get_content_metrics(
    startDate: str = Query(..., description="Start date (YYYY-MM-DD)"),
    endDate: str = Query(..., description="End date (YYYY-MM-DD)"),
) -> AnalyticsResponse:
    """Get content analytics summary metrics."""
    metrics = ContentMetrics(
        total_generated=make_metric_value(444, 13.3),
        total_downloaded=make_metric_value(373, 11.3),
        total_shared=make_metric_value(242, 13.1),
        engagement_rate=make_metric_value(68.4, 6.5),
    )
    return AnalyticsResponse(
        data=metrics.model_dump(by_alias=True),
        date_range={"startDate": startDate, "endDate": endDate},
        generated_at=datetime.utcnow(),
    )


@router.get("/content/by-type")
async def get_content_by_type(
    startDate: str = Query(..., description="Start date (YYYY-MM-DD)"),
    endDate: str = Query(..., description="End date (YYYY-MM-DD)"),
) -> AnalyticsResponse:
    """Get content metrics by type."""
    data = [
        ContentTypeData(type="Sales Deck", generated=85, downloaded=72, shared=45),
        ContentTypeData(type="Proposal", generated=62, downloaded=58, shared=32),
        ContentTypeData(type="One-Pager", generated=94, downloaded=76, shared=54),
        ContentTypeData(type="Case Study", generated=48, downloaded=42, shared=28),
        ContentTypeData(type="Email Template", generated=120, downloaded=95, shared=65),
        ContentTypeData(type="Battle Card", generated=35, downloaded=30, shared=18),
    ]
    return AnalyticsResponse(
        data=[d.model_dump() for d in data],
        date_range={"startDate": startDate, "endDate": endDate},
        generated_at=datetime.utcnow(),
    )


@router.get("/content/trends")
async def get_content_trends(
    startDate: str = Query(..., description="Start date (YYYY-MM-DD)"),
    endDate: str = Query(..., description="End date (YYYY-MM-DD)"),
) -> AnalyticsResponse:
    """Get daily content trend data."""
    dates = generate_date_range(startDate, endDate)
    data = []
    for date in dates[:30]:
        generated = random.randint(10, 25)
        downloaded = int(generated * random.uniform(0.6, 0.9))
        shared = int(downloaded * random.uniform(0.4, 0.7))
        data.append(ContentTrendData(
            date=date,
            generated=generated,
            downloaded=downloaded,
            shared=shared,
        ))
    return AnalyticsResponse(
        data=[d.model_dump() for d in data],
        date_range={"startDate": startDate, "endDate": endDate},
        generated_at=datetime.utcnow(),
    )


@router.get("/content/top")
async def get_top_content(
    startDate: str = Query(..., description="Start date (YYYY-MM-DD)"),
    endDate: str = Query(..., description="End date (YYYY-MM-DD)"),
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
) -> PaginatedResponse:
    """Get top performing content."""
    content_types = ["Sales Deck", "Proposal", "One-Pager", "Case Study", "Email Template"]
    all_data = []
    for i in range(50):
        all_data.append(ContentPerformance(
            id=f"content-{i+1}",
            title=f"Content Item {i+1}",
            type=random.choice(content_types),
            generated_at=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
            downloads=random.randint(10, 100),
            shares=random.randint(5, 50),
            views=random.randint(50, 300),
        ))

    # Sort by views descending
    all_data.sort(key=lambda x: x.views, reverse=True)

    # Paginate
    start_idx = (page - 1) * pageSize
    end_idx = start_idx + pageSize
    page_data = all_data[start_idx:end_idx]

    return PaginatedResponse(
        data=[d.model_dump(by_alias=True) for d in page_data],
        total=len(all_data),
        page=page,
        page_size=pageSize,
        has_more=end_idx < len(all_data),
    )


# ============================================
# Pipeline Analytics Endpoints
# ============================================

@router.get("/pipeline/metrics")
async def get_pipeline_metrics(
    startDate: str = Query(..., description="Start date (YYYY-MM-DD)"),
    endDate: str = Query(..., description="End date (YYYY-MM-DD)"),
) -> AnalyticsResponse:
    """Get pipeline analytics summary metrics."""
    metrics = PipelineMetrics(
        prospects_enriched=make_metric_value(363, 13.1),
        conversion_rate=make_metric_value(24.5, 10.4),
        avg_deal_size=make_metric_value(42500, 8.1),
        pipeline_value=make_metric_value(2400000, 13.2),
    )
    return AnalyticsResponse(
        data=metrics.model_dump(by_alias=True),
        date_range={"startDate": startDate, "endDate": endDate},
        generated_at=datetime.utcnow(),
    )


@router.get("/pipeline/stages")
async def get_pipeline_stages(
    startDate: str = Query(..., description="Start date (YYYY-MM-DD)"),
    endDate: str = Query(..., description="End date (YYYY-MM-DD)"),
) -> AnalyticsResponse:
    """Get pipeline data by stage."""
    data = [
        PipelineStageData(stage="Lead", count=245, value=2450000, conversion_rate=100),
        PipelineStageData(stage="Qualified", count=156, value=1560000, conversion_rate=63.7),
        PipelineStageData(stage="Meeting", count=98, value=980000, conversion_rate=62.8),
        PipelineStageData(stage="Proposal", count=64, value=640000, conversion_rate=65.3),
        PipelineStageData(stage="Negotiation", count=42, value=420000, conversion_rate=65.6),
        PipelineStageData(stage="Closed Won", count=28, value=280000, conversion_rate=66.7),
    ]
    return AnalyticsResponse(
        data=[d.model_dump(by_alias=True) for d in data],
        date_range={"startDate": startDate, "endDate": endDate},
        generated_at=datetime.utcnow(),
    )


@router.get("/pipeline/enrichment-trends")
async def get_enrichment_trends(
    startDate: str = Query(..., description="Start date (YYYY-MM-DD)"),
    endDate: str = Query(..., description="End date (YYYY-MM-DD)"),
) -> AnalyticsResponse:
    """Get daily enrichment trend data."""
    dates = generate_date_range(startDate, endDate)
    data = []
    for date in dates[:30]:
        enriched = random.randint(25, 50)
        converted = int(enriched * random.uniform(0.25, 0.4))
        value = converted * random.randint(30000, 70000)
        data.append(EnrichmentTrendData(
            date=date,
            enriched=enriched,
            converted=converted,
            value=value,
        ))
    return AnalyticsResponse(
        data=[d.model_dump() for d in data],
        date_range={"startDate": startDate, "endDate": endDate},
        generated_at=datetime.utcnow(),
    )


@router.get("/pipeline/sources")
async def get_prospect_sources(
    startDate: str = Query(..., description="Start date (YYYY-MM-DD)"),
    endDate: str = Query(..., description="End date (YYYY-MM-DD)"),
) -> AnalyticsResponse:
    """Get prospect source performance."""
    data = [
        ProspectSource(source="Inbound", count=312, conversion_rate=28.5, avg_deal_size=42000),
        ProspectSource(source="Outbound", count=248, conversion_rate=22.3, avg_deal_size=38000),
        ProspectSource(source="Referral", count=156, conversion_rate=35.2, avg_deal_size=52000),
        ProspectSource(source="Event", count=108, conversion_rate=18.5, avg_deal_size=35000),
        ProspectSource(source="Partner", count=68, conversion_rate=32.4, avg_deal_size=48000),
    ]
    return AnalyticsResponse(
        data=[d.model_dump(by_alias=True) for d in data],
        date_range={"startDate": startDate, "endDate": endDate},
        generated_at=datetime.utcnow(),
    )


# ============================================
# Team Performance Endpoints
# ============================================

@router.get("/team/metrics")
async def get_team_metrics(
    startDate: str = Query(..., description="Start date (YYYY-MM-DD)"),
    endDate: str = Query(..., description="End date (YYYY-MM-DD)"),
) -> AnalyticsResponse:
    """Get team performance summary metrics."""
    metrics = TeamMetrics(
        total_members=8,
        avg_calls_per_rep=make_metric_value(98, 8.9),
        avg_content_per_rep=make_metric_value(37, 15.6),
        avg_deals_per_rep=make_metric_value(5.25, 8.4),
    )
    return AnalyticsResponse(
        data=metrics.model_dump(by_alias=True),
        date_range={"startDate": startDate, "endDate": endDate},
        generated_at=datetime.utcnow(),
    )


@router.get("/team/performance")
async def get_team_performance(
    startDate: str = Query(..., description="Start date (YYYY-MM-DD)"),
    endDate: str = Query(..., description="End date (YYYY-MM-DD)"),
    sortBy: str = Query("deals", description="Sort by metric"),
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
) -> PaginatedResponse:
    """Get team member performance data."""
    team_data = [
        TeamMemberPerformance(id="1", name="Sarah Johnson", avatar="SJ", calls=125, content_generated=45, prospects_enriched=82, deals_won=8, deal_value=245000, spiced_score=8.5, rank=1, trend="up"),
        TeamMemberPerformance(id="2", name="Michael Chen", avatar="MC", calls=118, content_generated=38, prospects_enriched=75, deals_won=7, deal_value=218000, spiced_score=8.2, rank=2, trend="down"),
        TeamMemberPerformance(id="3", name="Emily Davis", avatar="ED", calls=105, content_generated=52, prospects_enriched=68, deals_won=6, deal_value=185000, spiced_score=7.9, rank=3, trend="stable"),
        TeamMemberPerformance(id="4", name="David Wilson", avatar="DW", calls=98, content_generated=35, prospects_enriched=62, deals_won=5, deal_value=162000, spiced_score=7.6, rank=4, trend="up"),
        TeamMemberPerformance(id="5", name="Jessica Martinez", avatar="JM", calls=92, content_generated=42, prospects_enriched=58, deals_won=5, deal_value=148000, spiced_score=7.8, rank=5, trend="down"),
        TeamMemberPerformance(id="6", name="James Brown", avatar="JB", calls=88, content_generated=32, prospects_enriched=52, deals_won=4, deal_value=125000, spiced_score=7.4, rank=6, trend="up"),
        TeamMemberPerformance(id="7", name="Amanda Taylor", avatar="AT", calls=82, content_generated=28, prospects_enriched=48, deals_won=4, deal_value=112000, spiced_score=7.2, rank=7, trend="down"),
        TeamMemberPerformance(id="8", name="Robert Lee", avatar="RL", calls=78, content_generated=25, prospects_enriched=45, deals_won=3, deal_value=95000, spiced_score=7.0, rank=8, trend="stable"),
    ]

    # Sort by specified metric
    sort_key = {
        "calls": lambda x: x.calls,
        "content": lambda x: x.content_generated,
        "deals": lambda x: x.deal_value,
        "spiced": lambda x: x.spiced_score,
    }.get(sortBy, lambda x: x.deal_value)

    team_data.sort(key=sort_key, reverse=True)

    # Update ranks after sorting
    for i, member in enumerate(team_data):
        member.rank = i + 1

    # Paginate
    start_idx = (page - 1) * pageSize
    end_idx = start_idx + pageSize
    page_data = team_data[start_idx:end_idx]

    return PaginatedResponse(
        data=[d.model_dump(by_alias=True) for d in page_data],
        total=len(team_data),
        page=page,
        page_size=pageSize,
        has_more=end_idx < len(team_data),
    )


@router.get("/team/trends")
async def get_team_trends(
    startDate: str = Query(..., description="Start date (YYYY-MM-DD)"),
    endDate: str = Query(..., description="End date (YYYY-MM-DD)"),
) -> AnalyticsResponse:
    """Get daily team trend data."""
    dates = generate_date_range(startDate, endDate)
    data = []
    for date in dates[:30]:
        data.append(TeamTrendData(
            date=date,
            calls=random.randint(140, 200),
            content=random.randint(35, 65),
            deals=random.randint(5, 15),
        ))
    return AnalyticsResponse(
        data=[d.model_dump() for d in data],
        date_range={"startDate": startDate, "endDate": endDate},
        generated_at=datetime.utcnow(),
    )


@router.get("/team/leaderboard")
async def get_leaderboard(
    startDate: str = Query(..., description="Start date (YYYY-MM-DD)"),
    endDate: str = Query(..., description="End date (YYYY-MM-DD)"),
    metric: str = Query("deals", description="Metric to rank by"),
) -> AnalyticsResponse:
    """Get leaderboard by specified metric."""
    team_data = [
        {"id": "1", "name": "Sarah Johnson", "avatar": "SJ", "calls": 125, "content": 45, "deals": 245000, "spiced": 8.5},
        {"id": "2", "name": "Michael Chen", "avatar": "MC", "calls": 118, "content": 38, "deals": 218000, "spiced": 8.2},
        {"id": "3", "name": "Emily Davis", "avatar": "ED", "calls": 105, "content": 52, "deals": 185000, "spiced": 7.9},
        {"id": "4", "name": "David Wilson", "avatar": "DW", "calls": 98, "content": 35, "deals": 162000, "spiced": 7.6},
        {"id": "5", "name": "Jessica Martinez", "avatar": "JM", "calls": 92, "content": 42, "deals": 148000, "spiced": 7.8},
    ]

    # Sort by metric
    team_data.sort(key=lambda x: x.get(metric, 0), reverse=True)

    data = []
    for i, member in enumerate(team_data):
        data.append(LeaderboardEntry(
            rank=i + 1,
            user_id=member["id"],
            name=member["name"],
            avatar=member["avatar"],
            metric=member.get(metric, 0),
            change=random.uniform(-5, 10),
        ))

    return AnalyticsResponse(
        data=[d.model_dump(by_alias=True) for d in data],
        date_range={"startDate": startDate, "endDate": endDate},
        generated_at=datetime.utcnow(),
    )


# ============================================
# Export Endpoints
# ============================================

@router.get("/calls/export")
async def export_calls(
    startDate: str = Query(..., description="Start date (YYYY-MM-DD)"),
    endDate: str = Query(..., description="End date (YYYY-MM-DD)"),
    format: str = Query("csv", description="Export format (csv or pdf)"),
) -> StreamingResponse:
    """Export call analytics data."""
    if format == "csv":
        dates = generate_date_range(startDate, endDate)

        output = BytesIO()
        output.write(b"Date,Total Calls,Answered,Missed,Avg Duration,SPICED Score\n")

        for date in dates[:30]:
            total = random.randint(40, 70)
            answered = int(total * random.uniform(0.9, 0.98))
            missed = total - answered
            duration = round(random.uniform(22, 35), 1)
            spiced = round(random.uniform(6.5, 8.5), 1)
            output.write(f"{date},{total},{answered},{missed},{duration},{spiced}\n".encode())

        output.seek(0)

        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=calls-{startDate}-{endDate}.csv"
            }
        )

    # For PDF, return a placeholder
    return Response(
        content=b"PDF export not yet implemented",
        media_type="application/pdf",
    )


@router.get("/content/export")
async def export_content(
    startDate: str = Query(..., description="Start date (YYYY-MM-DD)"),
    endDate: str = Query(..., description="End date (YYYY-MM-DD)"),
    format: str = Query("csv", description="Export format (csv or pdf)"),
) -> StreamingResponse:
    """Export content analytics data."""
    if format == "csv":
        output = BytesIO()
        output.write(b"Type,Generated,Downloaded,Shared,Engagement Rate\n")

        types = [
            ("Sales Deck", 85, 72, 45),
            ("Proposal", 62, 58, 32),
            ("One-Pager", 94, 76, 54),
            ("Case Study", 48, 42, 28),
            ("Email Template", 120, 95, 65),
            ("Battle Card", 35, 30, 18),
        ]

        for t in types:
            engagement = round((t[2] + t[3]) / t[1] * 100, 1) if t[1] > 0 else 0
            output.write(f"{t[0]},{t[1]},{t[2]},{t[3]},{engagement}%\n".encode())

        output.seek(0)

        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=content-{startDate}-{endDate}.csv"
            }
        )

    return Response(content=b"PDF export not yet implemented", media_type="application/pdf")


@router.get("/pipeline/export")
async def export_pipeline(
    startDate: str = Query(..., description="Start date (YYYY-MM-DD)"),
    endDate: str = Query(..., description="End date (YYYY-MM-DD)"),
    format: str = Query("csv", description="Export format (csv or pdf)"),
) -> StreamingResponse:
    """Export pipeline analytics data."""
    if format == "csv":
        output = BytesIO()
        output.write(b"Stage,Count,Value,Conversion Rate\n")

        stages = [
            ("Lead", 245, 2450000, 100),
            ("Qualified", 156, 1560000, 63.7),
            ("Meeting", 98, 980000, 62.8),
            ("Proposal", 64, 640000, 65.3),
            ("Negotiation", 42, 420000, 65.6),
            ("Closed Won", 28, 280000, 66.7),
        ]

        for s in stages:
            output.write(f"{s[0]},{s[1]},{s[2]},{s[3]}%\n".encode())

        output.seek(0)

        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=pipeline-{startDate}-{endDate}.csv"
            }
        )

    return Response(content=b"PDF export not yet implemented", media_type="application/pdf")


@router.get("/team/export")
async def export_team(
    startDate: str = Query(..., description="Start date (YYYY-MM-DD)"),
    endDate: str = Query(..., description="End date (YYYY-MM-DD)"),
    format: str = Query("csv", description="Export format (csv or pdf)"),
) -> StreamingResponse:
    """Export team performance data."""
    if format == "csv":
        output = BytesIO()
        output.write(b"Rank,Name,Calls,Content,Prospects,Deals,Deal Value,SPICED Score\n")

        team = [
            (1, "Sarah Johnson", 125, 45, 82, 8, 245000, 8.5),
            (2, "Michael Chen", 118, 38, 75, 7, 218000, 8.2),
            (3, "Emily Davis", 105, 52, 68, 6, 185000, 7.9),
            (4, "David Wilson", 98, 35, 62, 5, 162000, 7.6),
            (5, "Jessica Martinez", 92, 42, 58, 5, 148000, 7.8),
            (6, "James Brown", 88, 32, 52, 4, 125000, 7.4),
            (7, "Amanda Taylor", 82, 28, 48, 4, 112000, 7.2),
            (8, "Robert Lee", 78, 25, 45, 3, 95000, 7.0),
        ]

        for t in team:
            output.write(f"{t[0]},{t[1]},{t[2]},{t[3]},{t[4]},{t[5]},{t[6]},{t[7]}\n".encode())

        output.seek(0)

        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=team-{startDate}-{endDate}.csv"
            }
        )

    return Response(content=b"PDF export not yet implemented", media_type="application/pdf")
