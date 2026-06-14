"""
REST routes for the Product Passport Service.

Endpoints:
    GET /passports/{id}                    — fetch a specific passport by UUID
    GET /passports/by-product/{product_id} — list passports for a product (paginated)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.domain.schemas import PassportListResponse, PassportResponse
from app.domain.service import PassportService

router = APIRouter(prefix="/passports", tags=["passports"])


@router.get("/by-product/{product_id}", response_model=PassportListResponse)
async def get_passports_by_product(
    product_id: str,
    limit: int = Query(default=20, ge=1, le=100, description="Max items to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
):
    """
    List all digital product passports for a given product.

    Used by the frontend passport timeline and by the API Gateway aggregation layer.
    """
    service = PassportService(db)
    items, total = await service.get_passports_by_product(
        product_id, limit=limit, offset=offset
    )
    return PassportListResponse(items=list(items), total=total, limit=limit, offset=offset)


@router.get("/{passport_id}", response_model=PassportResponse)
async def get_passport(
    passport_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve a specific digital product passport by its UUID.

    Called by: API Gateway (for the passport detail/timeline view).
    """
    service = PassportService(db)
    passport = await service.get_passport_by_id(passport_id)

    if passport is None:
        raise HTTPException(status_code=404, detail=f"Passport not found: id={passport_id}")

    return passport
