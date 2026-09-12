"""API routes for Documents."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.document import Document
from app.intelligence.analysis import LowValueSignal, analyze_one, analyze_unanalyzed
from app.schemas import DemandSignalRead, DocumentRead

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentRead])
async def list_documents(skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Return all documents."""
    result = await db.execute(
        select(Document).order_by(Document.id.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars())


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(document_id: int, db: AsyncSession = Depends(get_db)):
    """Return a single document by ID."""
    doc = await db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.post("/analyze-batch")
async def analyze_batch(db: AsyncSession = Depends(get_db)):
    """Analyze every document that has no demand signal yet.

    同步执行：每篇约 1-3 秒 LLM 调用。逐篇提交 —— 单篇失败不影响其余。
    """
    return await analyze_unanalyzed(db)


@router.post("/{document_id}/analyze", response_model=DemandSignalRead)
async def analyze_document(document_id: int, db: AsyncSession = Depends(get_db)):
    """Classify + extract a single document into a demand signal."""
    doc = await db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        signal = await analyze_one(db, doc)
    except LowValueSignal as e:
        raise HTTPException(status_code=422, detail=e.reason)

    await db.commit()
    return signal


@router.get("/{document_id}/similar", response_model=list[DocumentRead])
async def similar_documents(document_id: int, limit: int = 5, db: AsyncSession = Depends(get_db)):
    """Return documents semantically closest to the given one."""
    doc = await db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.embedding is None:
        raise HTTPException(
            status_code=409,
            detail="Document has no embedding yet — run analyze first",
        )
    result = await db.execute(
        select(Document)
        .where(Document.id != doc.id)
        .where(Document.embedding.is_not(None))
        .order_by(Document.embedding.cosine_distance(doc.embedding))
        .limit(limit)
    )
    return list(result.scalars())