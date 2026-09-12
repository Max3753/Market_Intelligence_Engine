"""API routes for DemandSignals."""

from fastapi import APIRouter,Depends, HTTPException

from app.schemas import DemandSignalRead
from app.db.session import get_db
from app.models.demand import DemandSignal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select



router = APIRouter(prefix="/demands", tags=["demands"])

@router.get("", response_model=list[DemandSignalRead])
async def list_demands(skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Return all demand signals."""
    result = await db.execute(
        select(DemandSignal).order_by(DemandSignal.id.desc()).offset(skip).limit(limit)
    )
    
    return list(result.scalars())

@router.get("/{demand_id}", response_model=DemandSignalRead)
async def get_demand(demand_id: int, db: AsyncSession = Depends(get_db)):
    """Return a single demand signal by ID."""
    signal = await db.get(DemandSignal, demand_id)
    if signal is None:
        raise HTTPException(status_code=404, detail="Demand signal not found")
    return signal
    