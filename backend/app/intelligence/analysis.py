"""Intelligence pipeline — analyze documents into demand signals + auto-pipeline.

分析流水线（分类 → 低价值短路 → 抽取 → 信号+证据+向量化）的共享实现，
供单篇/批量端点与爬取后自动流水线复用。事务边界由调用方决定。
"""
import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory
from app.intelligence.classifier import classify
from app.intelligence.clustering import rebuild_clusters, rescore_clusters
from app.intelligence.embedder import embed
from app.intelligence.extractor import extract
from app.models.demand import DemandSignal, Evidence
from app.models.document import Document

logger = logging.getLogger(__name__)


class LowValueSignal(Exception):
    """Internal: document classified as noise / general_discussion."""


async def analyze_one(db: AsyncSession, doc: Document) -> DemandSignal:
    """Shared analyze pipeline (single & batch endpoints).

    分类 → 低价值短路 → 抽取 → upsert signal + evidence + 向量化。
    不 commit —— 事务边界由调用方决定。
    Raises LowValueSignal when the doc isn't a demand signal.
    """
    text = f"{doc.title}\n\n{doc.content or ''}"

    # 分类
    cls_result = await classify(text)
    if cls_result["demand_type"] in ("noise", "general_discussion"):
        raise LowValueSignal(
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


async def analyze_unanalyzed(db: AsyncSession) -> dict:
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
            await analyze_one(db, doc)
            await db.commit()
            stats["signals_created"] += 1
        except LowValueSignal:
            await db.rollback()
            stats["skipped_lowvalue"] += 1
        except Exception as e:
            await db.rollback()
            stats["failed"] += 1
            stats["errors"].append(f"doc#{did}: {type(e).__name__}: {e}"[:200])

    return stats


async def auto_pipeline() -> None:
    """爬取后自动流水线：分析未分析文档 → 聚类 → 评分。

    由 process_job 在爬取成功后触发（fire-and-forget）。
    独立 session；信号不足/无簇时正常跳过，其余失败只记日志不阻断。
    """
    try:
        async with async_session_factory() as db:
            stats = await analyze_unanalyzed(db)
        logger.info("auto-pipeline analyze: %s", stats)

        if stats["signals_created"] > 0:
            async with async_session_factory() as db:
                result = await rebuild_clusters(db)
                logger.info("auto-pipeline rebuild: %s", result)
            async with async_session_factory() as db:
                result = await rescore_clusters(db)
                logger.info("auto-pipeline rescore: %s", result)
    except ValueError as e:
        # 信号不足 / 无簇 —— 正常跳过，不是错误
        logger.info("auto-pipeline skipped: %s", e)
    except Exception as e:
        logger.error("auto-pipeline failed: %s", e, exc_info=True)