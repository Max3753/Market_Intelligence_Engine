"""API routes for Documents."""

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.document import Document
from app.models.demand import DemandSignal, Evidence
from app.intelligence.classifier import classify
from app.intelligence.extractor import extract
from app.intelligence.embedder import embed
from app.schemas import DemandSignalRead, DocumentRead

router = APIRouter(prefix="/documents", tags=["documents"])


class _LowValueSignal(Exception):
    """Internal: document classified as noise / general_discussion."""

    def __init__(self, reason: str):
        self.reason = reason


async def _analyze_one(db: AsyncSession, doc: Document) -> DemandSignal:
    """Shared analyze pipeline (single & batch endpoints).

    分类 → 低价值短路 → 抽取 → upsert signal + evidence + 向量化。
    不 commit —— 事务边界由调用方决定。
    Raises _LowValueSignal when the doc isn't a demand signal.
    """
    text = f"{doc.title}\n\n{doc.content or ''}"

    # 分类
    cls_result = await classify(text)
    if cls_result["demand_type"] in ("noise", "general_discussion"):
        raise _LowValueSignal(
            f"Not a demand signal: {cls_result['demand_type']} ({cls_result['reason']})"
        )

    # 抽取结构化字段
    ext_result = await extract(text, cls_result["demand_type"])

    # upsert DemandSignal —— ORM 模型，覆盖式更新
    result = await db.execute(
        select(DemandSignal).where(DemandSignal.document_id == doc.id)
    )
    signal = result.scalar_one_or_none()
    if signal is None:
        signal = DemandSignal(document_id=doc.id)
        db.add(signal)

    signal.demand_type = cls_result["demand_type"]
    signal.confidence = cls_result["confidence"]
    signal.problem = ext_result.get("problem")
    signal.pain_points = (
        json.dumps(ext_result["pain_points"], ensure_ascii=False)
        if ext_result.get("pain_points")
        else None
    )
    signal.job_to_be_done = ext_result.get("job_to_be_done")
    signal.desired_outcome = ext_result.get("desired_outcome")
    signal.current_solution = ext_result.get("current_solution")
    signal.severity = ext_result.get("severity")
    signal.willingness_to_pay = ext_result.get("willingness_to_pay")
    signal.evidence_strength = ext_result.get("evidence_strength")

    await db.flush()      # 拿 signal.id，供 Evidence 外键用

    # Evidence 刷新 —— 删旧插新，与分析版本保持一致
    old_evidence = await db.execute(
        select(Evidence).where(Evidence.demand_signal_id == signal.id)
    )
    for ev in old_evidence.scalars():
        await db.delete(ev)

    if ext_result.get("evidence_quote"):
        db.add(
            Evidence(
                demand_signal_id=signal.id,
                document_id=doc.id,
                snippet=ext_result["evidence_quote"],
            )
        )

    # 向量化（为聚类做准备）
    doc.embedding = await embed(text)
    return signal


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
    result = await db.execute(
        select(Document)
        .outerjoin(DemandSignal, DemandSignal.document_id == Document.id)
        .where(DemandSignal.id.is_(None))
    )
    doc_ids = [d.id for d in result.scalars()]   # 先取纯 id，rollback 后对象会失效

    stats: dict = {
        "candidates": len(doc_ids),
        "signals_created": 0,
        "skipped_lowvalue": 0,
        "failed": 0,
        "errors": [],
    }

    for did in doc_ids:
        try:
            doc = await db.get(Document, did)   # rollback 后重新获取，避免失效对象
            if doc is None:
                continue
            await _analyze_one(db, doc)
            await db.commit()
            stats["signals_created"] += 1
        except _LowValueSignal:
            await db.rollback()
            stats["skipped_lowvalue"] += 1
        except Exception as e:
            await db.rollback()
            stats["failed"] += 1
            stats["errors"].append(f"doc#{did}: {type(e).__name__}: {e}"[:200])

    return stats


@router.post("/{document_id}/analyze", response_model=DemandSignalRead)
async def analyze_document(document_id: int, db: AsyncSession = Depends(get_db)):
    """Classify + extract a single document into a demand signal."""
    doc = await db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        signal = await _analyze_one(db, doc)
    except _LowValueSignal as e:
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
