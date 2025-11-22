from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class DateRangeParams(BaseModel):
    """Common date range query parameters."""
    start_date: str = Field(..., alias="startDate", description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., alias="endDate", description="End date (YYYY-MM-DD)")

    class Config:
        populate_by_name = True


class MetricValue(BaseModel):
    """A metric value with trend information."""
    value: float
    change: float
    change_percent: float = Field(alias="changePercent")
    trend: Literal["up", "down", "stable"]

    class Config:
        populate_by_name = True


class AnalyticsResponse(BaseModel):
    """Standard analytics response wrapper."""
    data: dict | list
    date_range: DateRangeParams = Field(alias="dateRange")
    generated_at: datetime = Field(alias="generatedAt")

    class Config:
        populate_by_name = True


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    data: list
    total: int
    page: int
    page_size: int = Field(alias="pageSize")
    has_more: bool = Field(alias="hasMore")

    class Config:
        populate_by_name = True


# Call Analytics Models
class CallMetrics(BaseModel):
    """Call analytics summary metrics."""
    total_calls: MetricValue = Field(alias="totalCalls")
    avg_duration: MetricValue = Field(alias="avgDuration")
    avg_spiced_score: MetricValue = Field(alias="avgSpicedScore")
    conversion_rate: MetricValue = Field(alias="conversionRate")

    class Config:
        populate_by_name = True


class CallVolumeData(BaseModel):
    """Daily call volume data."""
    date: str
    calls: int
    answered: int
    missed: int


class CallDurationData(BaseModel):
    """Daily call duration data."""
    date: str
    avg_duration: float = Field(alias="avgDuration")
    min_duration: float = Field(alias="minDuration")
    max_duration: float = Field(alias="maxDuration")

    class Config:
        populate_by_name = True


class SpicedScoreData(BaseModel):
    """Daily SPICED score data."""
    date: str
    situation: float
    pain: float
    impact: float
    critical_event: float = Field(alias="criticalEvent")
    decision: float
    overall: float

    class Config:
        populate_by_name = True


class SpicedDistribution(BaseModel):
    """SPICED score distribution."""
    range: str
    count: int
    percentage: float


# Content Analytics Models
class ContentMetrics(BaseModel):
    """Content analytics summary metrics."""
    total_generated: MetricValue = Field(alias="totalGenerated")
    total_downloaded: MetricValue = Field(alias="totalDownloaded")
    total_shared: MetricValue = Field(alias="totalShared")
    engagement_rate: MetricValue = Field(alias="engagementRate")

    class Config:
        populate_by_name = True


class ContentTypeData(BaseModel):
    """Content metrics by type."""
    type: str
    generated: int
    downloaded: int
    shared: int


class ContentTrendData(BaseModel):
    """Daily content trend data."""
    date: str
    generated: int
    downloaded: int
    shared: int


class ContentPerformance(BaseModel):
    """Individual content performance."""
    id: str
    title: str
    type: str
    generated_at: datetime = Field(alias="generatedAt")
    downloads: int
    shares: int
    views: int

    class Config:
        populate_by_name = True


# Pipeline Analytics Models
class PipelineMetrics(BaseModel):
    """Pipeline analytics summary metrics."""
    prospects_enriched: MetricValue = Field(alias="prospectsEnriched")
    conversion_rate: MetricValue = Field(alias="conversionRate")
    avg_deal_size: MetricValue = Field(alias="avgDealSize")
    pipeline_value: MetricValue = Field(alias="pipelineValue")

    class Config:
        populate_by_name = True


class PipelineStageData(BaseModel):
    """Pipeline data by stage."""
    stage: str
    count: int
    value: float
    conversion_rate: float = Field(alias="conversionRate")

    class Config:
        populate_by_name = True


class EnrichmentTrendData(BaseModel):
    """Daily enrichment trend data."""
    date: str
    enriched: int
    converted: int
    value: float


class ProspectSource(BaseModel):
    """Prospect source performance."""
    source: str
    count: int
    conversion_rate: float = Field(alias="conversionRate")
    avg_deal_size: float = Field(alias="avgDealSize")

    class Config:
        populate_by_name = True


# Team Performance Models
class TeamMetrics(BaseModel):
    """Team performance summary metrics."""
    total_members: int = Field(alias="totalMembers")
    avg_calls_per_rep: MetricValue = Field(alias="avgCallsPerRep")
    avg_content_per_rep: MetricValue = Field(alias="avgContentPerRep")
    avg_deals_per_rep: MetricValue = Field(alias="avgDealsPerRep")

    class Config:
        populate_by_name = True


class TeamMemberPerformance(BaseModel):
    """Individual team member performance."""
    id: str
    name: str
    avatar: Optional[str] = None
    calls: int
    content_generated: int = Field(alias="contentGenerated")
    prospects_enriched: int = Field(alias="prospectsEnriched")
    deals_won: int = Field(alias="dealsWon")
    deal_value: float = Field(alias="dealValue")
    spiced_score: float = Field(alias="spicedScore")
    rank: int
    trend: Literal["up", "down", "stable"]

    class Config:
        populate_by_name = True


class TeamTrendData(BaseModel):
    """Daily team trend data."""
    date: str
    calls: int
    content: int
    deals: int


class LeaderboardEntry(BaseModel):
    """Leaderboard entry."""
    rank: int
    user_id: str = Field(alias="userId")
    name: str
    avatar: Optional[str] = None
    metric: float
    change: float

    class Config:
        populate_by_name = True
