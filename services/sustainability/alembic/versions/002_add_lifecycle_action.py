"""add lifecycle_action to sustainability_records

Revision ID: 002
Revises: 001
Create Date: 2026-06-14
"""

from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sustainability_records",
        sa.Column("lifecycle_action", sa.String(20), nullable=False, server_default="UNKNOWN"),
    )


def downgrade() -> None:
    op.drop_column("sustainability_records", "lifecycle_action")
