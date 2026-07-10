"""initial schema

Revision ID: 202607090001
Revises:
Create Date: 2026-07-09 00:01:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202607090001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "hcp",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("hospital", sa.String(length=180), nullable=True),
        sa.Column("specialization", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_hcp_name", "hcp", ["name"])
    op.create_index("ix_hcp_hospital", "hcp", ["hospital"])
    op.create_index("ix_hcp_specialization", "hcp", ["specialization"])
    op.create_index("ix_hcp_name_hospital", "hcp", ["name", "hospital"])
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=140), nullable=False, unique=True),
        sa.Column("benefits", sa.Text(), nullable=False),
        sa.Column("dosage", sa.Text(), nullable=False),
        sa.Column("side_effects", sa.Text(), nullable=False),
        sa.Column("clinical_notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_products_name", "products", ["name"])
    op.create_table(
        "interactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("hcp_id", sa.Integer(), sa.ForeignKey("hcp.id", ondelete="CASCADE"), nullable=False),
        sa.Column("interaction_type", sa.String(length=80), nullable=True),
        sa.Column("interaction_date", sa.Date(), nullable=True),
        sa.Column("interaction_time", sa.Time(), nullable=True),
        sa.Column("attendees", sa.Text(), nullable=True),
        sa.Column("topics_discussed", sa.Text(), nullable=True),
        sa.Column("voice_summary", sa.Text(), nullable=True),
        sa.Column("materials_shared", sa.Text(), nullable=True),
        sa.Column("samples_distributed", sa.Text(), nullable=True),
        sa.Column("sentiment", sa.Enum("positive", "neutral", "negative", name="sentiment"), nullable=False),
        sa.Column("outcome", sa.Text(), nullable=True),
        sa.Column("follow_up", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_interactions_hcp_id", "interactions", ["hcp_id"])
    op.create_index("ix_interactions_interaction_date", "interactions", ["interaction_date"])
    op.create_index("ix_interactions_sentiment", "interactions", ["sentiment"])
    op.create_index("ix_interactions_created_at", "interactions", ["created_at"])
    op.create_index("ix_interactions_hcp_date", "interactions", ["hcp_id", "interaction_date"])
    op.create_table(
        "reminders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("hcp_id", sa.Integer(), sa.ForeignKey("hcp.id", ondelete="CASCADE"), nullable=False),
        sa.Column("interaction_id", sa.Integer(), sa.ForeignKey("interactions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_reminders_hcp_id", "reminders", ["hcp_id"])
    op.create_index("ix_reminders_interaction_id", "reminders", ["interaction_id"])
    op.create_index("ix_reminders_due_at", "reminders", ["due_at"])
    op.create_index("ix_reminders_status", "reminders", ["status"])
    op.create_table(
        "chat_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.String(length=80), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_chat_history_session_id", "chat_history", ["session_id"])
    op.create_index("ix_chat_history_created_at", "chat_history", ["created_at"])
    op.create_table(
        "tool_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.String(length=80), nullable=False),
        sa.Column("tool_name", sa.String(length=120), nullable=False),
        sa.Column("input_json", sa.Text(), nullable=False),
        sa.Column("output_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_tool_logs_session_id", "tool_logs", ["session_id"])
    op.create_index("ix_tool_logs_tool_name", "tool_logs", ["tool_name"])
    op.create_index("ix_tool_logs_status", "tool_logs", ["status"])
    op.create_index("ix_tool_logs_created_at", "tool_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_tool_logs_created_at", table_name="tool_logs")
    op.drop_index("ix_tool_logs_status", table_name="tool_logs")
    op.drop_index("ix_tool_logs_tool_name", table_name="tool_logs")
    op.drop_index("ix_tool_logs_session_id", table_name="tool_logs")
    op.drop_table("tool_logs")
    op.drop_index("ix_chat_history_created_at", table_name="chat_history")
    op.drop_index("ix_chat_history_session_id", table_name="chat_history")
    op.drop_table("chat_history")
    op.drop_index("ix_reminders_status", table_name="reminders")
    op.drop_index("ix_reminders_due_at", table_name="reminders")
    op.drop_index("ix_reminders_interaction_id", table_name="reminders")
    op.drop_index("ix_reminders_hcp_id", table_name="reminders")
    op.drop_table("reminders")
    op.drop_index("ix_interactions_hcp_date", table_name="interactions")
    op.drop_index("ix_interactions_created_at", table_name="interactions")
    op.drop_index("ix_interactions_sentiment", table_name="interactions")
    op.drop_index("ix_interactions_interaction_date", table_name="interactions")
    op.drop_index("ix_interactions_hcp_id", table_name="interactions")
    op.drop_table("interactions")
    op.drop_index("ix_products_name", table_name="products")
    op.drop_table("products")
    op.drop_index("ix_hcp_name_hospital", table_name="hcp")
    op.drop_index("ix_hcp_specialization", table_name="hcp")
    op.drop_index("ix_hcp_hospital", table_name="hcp")
    op.drop_index("ix_hcp_name", table_name="hcp")
    op.drop_table("hcp")
