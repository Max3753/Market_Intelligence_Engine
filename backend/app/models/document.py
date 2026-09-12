"""Document, RawDocument & Author — crawled content and its provenance."""

from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

from typing import Optional          # 如果还没有的话
from pgvector.sqlalchemy import Vector
from app.intelligence.embedder import EMBEDDING_DIM

class RawDocument(Base):
    """Original unprocessed crawl payload (traceability layer, §8.1)."""

    __tablename__ = "raw_documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    crawl_job_id: Mapped[int] = mapped_column(nullable=False)
    source_id: Mapped[int] = mapped_column(nullable=False)
    url: Mapped[str] = mapped_column(String(1024))
    payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class Author(Base):
    """The creator of a document on a data source."""

    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(nullable=False)
    source_author_id: Mapped[str] = mapped_column(String(255))
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    profile_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    karma: Mapped[Optional[int]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class Document(Base):
    """A crawled content item from a data source (normalized layer, §8.2)."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    source_item_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    url: Mapped[str] = mapped_column(String(1024))
    canonical_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    author_id: Mapped[Optional[int]] = mapped_column(ForeignKey("authors.id"), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    engagement_score: Mapped[Optional[float]] = mapped_column(nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )
    embedding: Mapped[Optional[list[float]]] = mapped_column(
        Vector(EMBEDDING_DIM), nullable=True
    )