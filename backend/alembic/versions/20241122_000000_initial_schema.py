"""Initial database schema for Sales OS.

Revision ID: 001_initial
Revises:
Create Date: 2024-11-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all initial tables."""

    # Organizations table
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("size", sa.String(50), nullable=True),
        sa.Column("domain", sa.String(255), nullable=True, unique=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("settings", sa.Text, nullable=True),
        sa.Column("hubspot_api_key", sa.String(500), nullable=True),
        sa.Column("claude_api_key", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("role", sa.String(50), default="sales_rep", nullable=False),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("is_verified", sa.Boolean, default=False, nullable=False),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("timezone", sa.String(50), default="UTC", nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=False), nullable=True),  # FK added after teams table
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Teams table
    op.create_table(
        "teams",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("manager_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Add FK constraint for users.team_id
    op.create_foreign_key("fk_users_team_id", "users", "teams", ["team_id"], ["id"])

    # Companies table
    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, index=True),
        sa.Column("domain", sa.String(255), nullable=True, unique=True, index=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("sub_industry", sa.String(100), nullable=True),
        sa.Column("size", sa.String(50), nullable=True),
        sa.Column("employee_count", sa.Integer, nullable=True),
        sa.Column("annual_revenue", sa.Float, nullable=True),
        sa.Column("funding_stage", sa.String(50), nullable=True),
        sa.Column("total_funding", sa.Float, nullable=True),
        sa.Column("founded_year", sa.Integer, nullable=True),
        sa.Column("headquarters_city", sa.String(100), nullable=True),
        sa.Column("headquarters_state", sa.String(100), nullable=True),
        sa.Column("headquarters_country", sa.String(100), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("tagline", sa.String(500), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("tech_stack", sa.Text, nullable=True),
        sa.Column("tools_used", sa.Text, nullable=True),
        sa.Column("linkedin_url", sa.String(500), nullable=True),
        sa.Column("twitter_handle", sa.String(100), nullable=True),
        sa.Column("crunchbase_url", sa.String(500), nullable=True),
        sa.Column("enrichment_data", sa.Text, nullable=True),
        sa.Column("recent_news", sa.Text, nullable=True),
        sa.Column("recent_events", sa.Text, nullable=True),
        sa.Column("key_initiatives", sa.Text, nullable=True),
        sa.Column("is_verified", sa.Boolean, default=False, nullable=False),
        sa.Column("last_enriched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("hubspot_id", sa.String(100), nullable=True, index=True),
        sa.Column("salesforce_id", sa.String(100), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Prospects table
    op.create_table(
        "prospects",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, index=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("mobile", sa.String(50), nullable=True),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("department", sa.String(100), nullable=True),
        sa.Column("seniority", sa.String(50), nullable=True),
        sa.Column("status", sa.String(50), default="new", nullable=False),
        sa.Column("lead_score", sa.Integer, nullable=True),
        sa.Column("linkedin_url", sa.String(500), nullable=True),
        sa.Column("twitter_handle", sa.String(100), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("enrichment_data", sa.Text, nullable=True),
        sa.Column("work_history", sa.Text, nullable=True),
        sa.Column("education", sa.Text, nullable=True),
        sa.Column("interests", sa.Text, nullable=True),
        sa.Column("recent_posts", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("pain_points", sa.Text, nullable=True),
        sa.Column("goals", sa.Text, nullable=True),
        sa.Column("is_verified", sa.Boolean, default=False, nullable=False),
        sa.Column("last_enriched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_contacted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("hubspot_id", sa.String(100), nullable=True, index=True),
        sa.Column("salesforce_id", sa.String(100), nullable=True, index=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Calls table
    op.create_table(
        "calls",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("source", sa.String(50), default="manual_upload", nullable=False),
        sa.Column("call_type", sa.String(50), nullable=True),
        sa.Column("status", sa.String(50), default="pending", nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer, nullable=True),
        sa.Column("recording_url", sa.String(1000), nullable=True),
        sa.Column("external_id", sa.String(255), nullable=True, index=True),
        sa.Column("participants", sa.Text, nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("prospect_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("prospects.id"), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Transcripts table
    op.create_table(
        "transcripts",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("raw_text", sa.Text, nullable=False),
        sa.Column("structured_text", sa.Text, nullable=True),
        sa.Column("language", sa.String(10), default="en", nullable=False),
        sa.Column("word_count", sa.Integer, nullable=True),
        sa.Column("confidence_score", sa.Float, nullable=True),
        sa.Column("transcription_service", sa.String(100), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("call_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("calls.id"), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # SPICED Analyses table
    op.create_table(
        "spiced_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("situation", sa.Text, nullable=True),
        sa.Column("pain", sa.Text, nullable=True),
        sa.Column("impact", sa.Text, nullable=True),
        sa.Column("critical_event", sa.Text, nullable=True),
        sa.Column("expected_decision", sa.Text, nullable=True),
        sa.Column("decision_criteria", sa.Text, nullable=True),
        sa.Column("situation_score", sa.Integer, nullable=True),
        sa.Column("pain_score", sa.Integer, nullable=True),
        sa.Column("impact_score", sa.Integer, nullable=True),
        sa.Column("critical_event_score", sa.Integer, nullable=True),
        sa.Column("expected_decision_score", sa.Integer, nullable=True),
        sa.Column("decision_criteria_score", sa.Integer, nullable=True),
        sa.Column("overall_score", sa.Float, nullable=True),
        sa.Column("confidence_score", sa.Float, nullable=True),
        sa.Column("call_summary", sa.Text, nullable=True),
        sa.Column("call_notes", sa.Text, nullable=True),
        sa.Column("follow_up_tasks", sa.Text, nullable=True),
        sa.Column("key_quotes", sa.Text, nullable=True),
        sa.Column("action_items", sa.Text, nullable=True),
        sa.Column("gaps_identified", sa.Text, nullable=True),
        sa.Column("recommended_questions", sa.Text, nullable=True),
        sa.Column("model_version", sa.String(50), nullable=True),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("call_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("calls.id"), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Content Templates table
    op.create_table(
        "content_templates",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("content_type", sa.String(50), nullable=False),
        sa.Column("template_structure", sa.Text, nullable=False),
        sa.Column("brand_guidelines", sa.Text, nullable=True),
        sa.Column("color_scheme", sa.Text, nullable=True),
        sa.Column("font_family", sa.String(100), nullable=True),
        sa.Column("is_default", sa.Boolean, default=False, nullable=False),
        sa.Column("is_public", sa.Boolean, default=False, nullable=False),
        sa.Column("version", sa.Integer, default=1, nullable=False),
        sa.Column("usage_count", sa.Integer, default=0, nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Content table
    op.create_table(
        "content",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), default="draft", nullable=False),
        sa.Column("goal", sa.Text, nullable=True),
        sa.Column("product_info", sa.Text, nullable=True),
        sa.Column("audience_info", sa.Text, nullable=True),
        sa.Column("additional_context", sa.Text, nullable=True),
        sa.Column("content_data", sa.Text, nullable=True),
        sa.Column("rendered_html", sa.Text, nullable=True),
        sa.Column("rendered_pdf_url", sa.String(1000), nullable=True),
        sa.Column("rendered_pptx_url", sa.String(1000), nullable=True),
        sa.Column("version", sa.Integer, default=1, nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("content.id"), nullable=True),
        sa.Column("tags", sa.Text, nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("model_version", sa.String(50), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("content_templates.id"), nullable=True),
        sa.Column("prospect_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("prospects.id"), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Coaching Reports table
    op.create_table(
        "coaching_reports",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("overall_score", sa.Float, nullable=False),
        sa.Column("level", sa.String(50), nullable=False),
        sa.Column("confidence_score", sa.Float, nullable=True),
        sa.Column("executive_summary", sa.Text, nullable=True),
        sa.Column("key_strengths", sa.Text, nullable=True),
        sa.Column("key_improvements", sa.Text, nullable=True),
        sa.Column("wbd_methodology_alignment", sa.Float, nullable=True),
        sa.Column("wbd_feedback", sa.Text, nullable=True),
        sa.Column("action_items", sa.Text, nullable=True),
        sa.Column("learning_resources", sa.Text, nullable=True),
        sa.Column("practice_scenarios", sa.Text, nullable=True),
        sa.Column("improvement_areas", sa.Text, nullable=True),
        sa.Column("regression_areas", sa.Text, nullable=True),
        sa.Column("trend_summary", sa.Text, nullable=True),
        sa.Column("model_version", sa.String(50), nullable=True),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("call_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("calls.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Coaching Scores table
    op.create_table(
        "coaching_scores",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("component", sa.String(50), nullable=False),
        sa.Column("score", sa.Integer, nullable=False),
        sa.Column("feedback", sa.Text, nullable=True),
        sa.Column("strengths", sa.Text, nullable=True),
        sa.Column("areas_for_improvement", sa.Text, nullable=True),
        sa.Column("evidence_quotes", sa.Text, nullable=True),
        sa.Column("missed_opportunities", sa.Text, nullable=True),
        sa.Column("recommended_questions", sa.Text, nullable=True),
        sa.Column("best_practices", sa.Text, nullable=True),
        sa.Column("coaching_report_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("coaching_reports.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # HubSpot Integrations table
    op.create_table(
        "hubspot_integrations",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("access_token", sa.String(500), nullable=False),
        sa.Column("refresh_token", sa.String(500), nullable=False),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scopes", sa.Text, nullable=True),
        sa.Column("hub_id", sa.String(100), nullable=False, index=True),
        sa.Column("hub_domain", sa.String(255), nullable=True),
        sa.Column("hub_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sync_status", sa.String(50), nullable=True),
        sa.Column("last_sync_error", sa.Text, nullable=True),
        sa.Column("contacts_synced", sa.Integer, default=0, nullable=False),
        sa.Column("companies_synced", sa.Integer, default=0, nullable=False),
        sa.Column("deals_synced", sa.Integer, default=0, nullable=False),
        sa.Column("contact_field_mapping", sa.Text, nullable=True),
        sa.Column("company_field_mapping", sa.Text, nullable=True),
        sa.Column("deal_field_mapping", sa.Text, nullable=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("organizations.id"), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create indexes for better query performance
    op.create_index("ix_calls_user_id", "calls", ["user_id"])
    op.create_index("ix_calls_status", "calls", ["status"])
    op.create_index("ix_content_created_by_id", "content", ["created_by_id"])
    op.create_index("ix_content_status", "content", ["status"])
    op.create_index("ix_coaching_reports_user_id", "coaching_reports", ["user_id"])
    op.create_index("ix_coaching_reports_call_id", "coaching_reports", ["call_id"])


def downgrade() -> None:
    """Drop all tables."""
    # Drop indexes first
    op.drop_index("ix_coaching_reports_call_id", table_name="coaching_reports")
    op.drop_index("ix_coaching_reports_user_id", table_name="coaching_reports")
    op.drop_index("ix_content_status", table_name="content")
    op.drop_index("ix_content_created_by_id", table_name="content")
    op.drop_index("ix_calls_status", table_name="calls")
    op.drop_index("ix_calls_user_id", table_name="calls")

    # Drop tables in reverse order of creation
    op.drop_table("hubspot_integrations")
    op.drop_table("coaching_scores")
    op.drop_table("coaching_reports")
    op.drop_table("content")
    op.drop_table("content_templates")
    op.drop_table("spiced_analyses")
    op.drop_table("transcripts")
    op.drop_table("calls")
    op.drop_table("prospects")
    op.drop_table("companies")
    op.drop_constraint("fk_users_team_id", "users", type_="foreignkey")
    op.drop_table("teams")
    op.drop_table("users")
    op.drop_table("organizations")
