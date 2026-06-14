"""create matching tables

Revision ID: 0001
Revises:
Create Date: 2026-06-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── match_requests ────────────────────────────────────────────────────
    op.create_table(
        "match_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("return_id", sa.String(36), nullable=False),
        sa.Column("product_id", sa.String(36), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lng", sa.Float(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_match_requests_return_id", "match_requests", ["return_id"], unique=True)
    op.create_index("ix_match_requests_product_id", "match_requests", ["product_id"])

    # ── matches ───────────────────────────────────────────────────────────
    op.create_table(
        "matches",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "match_request_id",
            sa.String(36),
            sa.ForeignKey("match_requests.id"),
            nullable=False,
        ),
        sa.Column("buyer_user_id", sa.String(36), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("estimated_savings", sa.Float(), nullable=False),
        sa.Column("distance_km", sa.Float(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False, server_default=""),
    )
    op.create_index("ix_matches_match_request_id", "matches", ["match_request_id"])
    op.create_index("ix_matches_buyer_user_id", "matches", ["buyer_user_id"])

    # ── listings ──────────────────────────────────────────────────────────
    op.create_table(
        "listings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("product_id", sa.String(36), nullable=False),
        sa.Column("passport_id", sa.String(36), nullable=False),
        sa.Column("return_id", sa.String(36), nullable=False),
        sa.Column(
            "match_request_id",
            sa.String(36),
            sa.ForeignKey("match_requests.id"),
            nullable=True,
        ),
        sa.Column("price", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_listings_product_id", "listings", ["product_id"])
    op.create_index("ix_listings_passport_id", "listings", ["passport_id"])
    op.create_index("ix_listings_return_id", "listings", ["return_id"])
    op.create_index("ix_listings_match_request_id", "listings", ["match_request_id"])


def downgrade() -> None:
    op.drop_table("listings")
    op.drop_table("matches")
    op.drop_table("match_requests")
