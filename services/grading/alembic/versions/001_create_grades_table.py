"""create grades table

Revision ID: 001
Revises: 
Create Date: 2026-06-13
"""

from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "grades",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("return_id", sa.String(36), nullable=False),
        sa.Column("product_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("grade", sa.String(1), nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("damage_summary", sa.Text, nullable=False),
        sa.Column("key_points", sa.JSON, nullable=True),
        sa.Column("defects", sa.JSON, nullable=True),
        sa.Column("model_version", sa.String(50), nullable=True),
        sa.Column("return_reason", sa.Text, nullable=False),
        sa.Column("media_keys", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_grades_return_id", "grades", ["return_id"], unique=True)
    op.create_index("ix_grades_product_id", "grades", ["product_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_grades_product_id", table_name="grades")
    op.drop_index("ix_grades_return_id", table_name="grades")
    op.drop_table("grades")
