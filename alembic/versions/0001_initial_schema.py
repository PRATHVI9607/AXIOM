"""Initial AXIOM schema: users, projects, functions, jobs, patches, api_keys.

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-05
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("github_id", sa.String, unique=True, nullable=True),
        sa.Column("username", sa.String, nullable=False),
        sa.Column("email", sa.String, unique=True, nullable=False),
        sa.Column("password_hash", sa.String, nullable=True),
        sa.Column("role", sa.String, server_default="developer"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "projects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("root_path", sa.String, nullable=False),
        sa.Column("languages", sa.JSON),
        sa.Column("owner_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("settings", sa.JSON),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "functions",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("file_path", sa.String, nullable=False),
        sa.Column("function_name", sa.String, nullable=False),
        sa.Column("language", sa.String, nullable=False),
        sa.Column("start_line", sa.Integer, nullable=False),
        sa.Column("end_line", sa.Integer, nullable=False),
        sa.Column("content_hash", sa.String, nullable=False),
        sa.Column("current_risk", sa.Float, server_default="0.0"),
        sa.Column("last_analyzed", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_functions_project", "functions", ["project_id"])
    op.create_index("idx_functions_risk", "functions", ["current_risk"])
    op.create_table(
        "analysis_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id")),
        sa.Column("type", sa.String, nullable=False),
        sa.Column("status", sa.String, server_default="queued"),
        sa.Column("target", sa.String, nullable=True),
        sa.Column("result", sa.JSON, nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "patches",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("function_id", sa.String, sa.ForeignKey("functions.id"), nullable=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id")),
        sa.Column("pattern", sa.String, nullable=False),
        sa.Column("original_code", sa.Text, nullable=False),
        sa.Column("patched_code", sa.Text, nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("verified", sa.Boolean, server_default=sa.false()),
        sa.Column("test_results", sa.JSON, nullable=True),
        sa.Column("status", sa.String, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id")),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("key_hash", sa.String, unique=True, nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("last_used", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("api_keys")
    op.drop_table("patches")
    op.drop_index("idx_functions_risk", table_name="functions")
    op.drop_index("idx_functions_project", table_name="functions")
    op.drop_table("functions")
    op.drop_table("analysis_jobs")
    op.drop_table("projects")
    op.drop_table("users")
