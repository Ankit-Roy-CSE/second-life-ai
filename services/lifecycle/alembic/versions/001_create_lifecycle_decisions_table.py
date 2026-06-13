"""Create lifecycle_decisions table

Revision ID: 001
Revises:
Create Date: 2026-06-14

"""
from alembic import op
import sqlalchemy as sa


revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lifecycle_decisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("return_id", sa.String(36), nullable=False, unique=True, index=True),
        sa.Column("grade_id", sa.String(36), nullable=False, index=True),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("value_recovery_estimate", sa.Float(), nullable=False),
        sa.Column("sustainability_score", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("lifecycle_decisions")
