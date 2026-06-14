"""
Data access helpers for the Product Passport Service.

The service layer (domain/service.py) is the primary home for business logic.
This module provides low-level CRUD helpers that can be reused across service methods.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Passport, Product


async def get_passport_by_id(db: AsyncSession, passport_id: str) -> Optional[Passport]:
    """Return a Passport by primary key, or None."""
    result = await db.execute(select(Passport).where(Passport.id == passport_id))
    return result.scalar_one_or_none()


async def get_passport_by_return_id(db: AsyncSession, return_id: str) -> Optional[Passport]:
    """Return a Passport by return_id, or None."""
    result = await db.execute(select(Passport).where(Passport.return_id == return_id))
    return result.scalar_one_or_none()


async def get_product_by_id(db: AsyncSession, product_id: str) -> Optional[Product]:
    """Return a Product by primary key, or None."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()
