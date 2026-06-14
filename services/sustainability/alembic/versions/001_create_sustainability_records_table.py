"""create sustainability_records table

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
        "sustainability_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("return_id", sa.String(36), nullable=False),
        sa.Column("product_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("co2_avoided_kg", sa.Float, nullable=False, server_default="0"),
        sa.Column("waste_diverted_kg", sa.Float, nullable=False, server_default="0"),
        sa.Column("value_recovered", sa.Float, nullable=False, server_default="0"),
        sa.Column("green_credits", sa.Float, nullable=False, server_default="0"),
        sa.Column("lifecycle_stage", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_sustainability_return_id", "sustainability_records", ["return_id"], unique=True)
    op.create_index("ix_sustainability_product_id", "sustainability_records", ["product_id"])
    op.create_index("ix_sustainability_user_id", "sustainability_records", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_sustainability_user_id", table_name="sustainability_records")
    op.drop_index("ix_sustainability_product_id", table_name="sustainability_records")
    op.drop_index("ix_sustainability_return_id", table_name="sustainability_records")
    op.drop_table("sustainability_records")
