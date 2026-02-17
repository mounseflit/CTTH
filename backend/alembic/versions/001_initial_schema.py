"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-02-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("role", sa.String(50), nullable=False, server_default="analyst"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_users_email", "users", ["email"])

    # Trade data table
    op.create_table(
        "trade_data",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("period_date", sa.Date, nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("reporter_code", sa.String(10), nullable=False),
        sa.Column("reporter_name", sa.String(255), nullable=True),
        sa.Column("partner_code", sa.String(10), nullable=False),
        sa.Column("partner_name", sa.String(255), nullable=True),
        sa.Column("hs_code", sa.String(10), nullable=False),
        sa.Column("hs_description", sa.String(500), nullable=True),
        sa.Column("flow", sa.String(10), nullable=False),
        sa.Column("value_usd", sa.Numeric(18, 2), nullable=True),
        sa.Column("value_eur", sa.Numeric(18, 2), nullable=True),
        sa.Column("weight_kg", sa.Numeric(18, 2), nullable=True),
        sa.Column("quantity", sa.Numeric(18, 2), nullable=True),
        sa.Column("frequency", sa.String(5), nullable=False, server_default="A"),
        sa.Column("raw_json", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "source",
            "reporter_code",
            "partner_code",
            "hs_code",
            "flow",
            "period_date",
            "frequency",
            name="uq_trade_data_composite",
        ),
    )
    op.create_index("idx_trade_data_period", "trade_data", ["period_date"])
    op.create_index("idx_trade_data_hs_code", "trade_data", ["hs_code"])
    op.create_index(
        "idx_trade_data_source_flow", "trade_data", ["source", "flow"]
    )
    op.create_index(
        "idx_trade_data_reporter", "trade_data", ["reporter_code"]
    )

    # Convert trade_data to TimescaleDB hypertable
    op.execute(
        "SELECT create_hypertable('trade_data', 'period_date', "
        "chunk_time_interval => INTERVAL '1 year', "
        "if_not_exists => TRUE, "
        "migrate_data => TRUE)"
    )

    # News articles table
    op.create_table(
        "news_articles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("content", sa.Text, nullable=True),
        sa.Column("source_url", sa.String(1024), unique=True, nullable=False),
        sa.Column("source_name", sa.String(255), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("tags", postgresql.JSONB, nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("relevance_score", sa.Float, nullable=True),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_news_category", "news_articles", ["category"])
    op.create_index(
        "idx_news_published", "news_articles", ["published_at"]
    )

    # pgvector HNSW index for similarity search
    op.execute(
        "CREATE INDEX idx_news_embedding ON news_articles "
        "USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )

    # Reports table
    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("report_type", sa.String(50), nullable=False),
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="pending"
        ),
        sa.Column("parameters", postgresql.JSONB, nullable=True),
        sa.Column("content_markdown", sa.Text, nullable=True),
        sa.Column("content_html", sa.Text, nullable=True),
        sa.Column("pdf_path", sa.String(500), nullable=True),
        sa.Column(
            "generated_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("generation_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "generation_completed_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Data source status table
    op.create_table(
        "data_source_status",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_name", sa.String(100), unique=True, nullable=False),
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="active"
        ),
        sa.Column(
            "last_successful_fetch", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column("last_error_message", sa.Text, nullable=True),
        sa.Column(
            "records_fetched_today", sa.Integer, nullable=False, server_default="0"
        ),
        sa.Column(
            "api_calls_today", sa.Integer, nullable=False, server_default="0"
        ),
        sa.Column("config", postgresql.JSONB, nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("data_source_status")
    op.drop_table("reports")
    op.drop_table("news_articles")
    op.drop_table("trade_data")
    op.drop_table("users")
