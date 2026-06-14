"""create products and passports tables

Revision ID: 001
Revises:
Create Date: 2026-01-01 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── products ──────────────────────────────────────────────────────────────
    op.create_table(
        "products",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("owner_user_id", sa.String(36), nullable=False),
        sa.Column("category", sa.String(100), nullable=False, server_default="electronics"),
        sa.Column("title", sa.String(255), nullable=False, server_default="Returned Product"),
        sa.Column("brand", sa.String(100), nullable=False, server_default="Unknown"),
        sa.Column("attributes", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_products_owner_user_id", "products", ["owner_user_id"])

    # ── passports ─────────────────────────────────────────────────────────────
    op.create_table(
        "passports",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("return_id", sa.String(36), nullable=False, unique=True),
        sa.Column("product_id", sa.String(36), nullable=False),
        sa.Column("current_grade", sa.String(1), nullable=True),
        sa.Column("grade_confidence", sa.Float(), nullable=True),
        sa.Column("damage_summary", sa.Text(), nullable=True),
        sa.Column("lifecycle_action", sa.String(20), nullable=True),
        sa.Column("value_recovery_estimate", sa.Float(), nullable=True),
        sa.Column("sustainability_score", sa.Float(), nullable=True),
        sa.Column("ownership_history", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("refurb_history", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("sustainability", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_passports_return_id", "passports", ["return_id"], unique=True)
    op.create_index("ix_passports_product_id", "passports", ["product_id"])


def downgrade() -> None:
    op.drop_index("ix_passports_product_id", table_name="passports")
    op.drop_index("ix_passports_return_id", table_name="passports")
    op.drop_table("passports")
    op.drop_index("ix_products_owner_user_id", table_name="products")
    op.drop_table("products")
