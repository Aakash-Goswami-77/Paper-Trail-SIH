import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Boolean, Float, DateTime, Text
from datetime import datetime

# Default to a local postgres container or local instance URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@cert_postgres_db:5432/cert_verifier")

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class CertificateModel(Base):
    __tablename__ = "certificates"

    cert_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    student_name: Mapped[str] = mapped_column(String(100))
    degree_title: Mapped[str] = mapped_column(String(150))
    institution: Mapped[str] = mapped_column(String(150))
    leaf_hash: Mapped[str] = mapped_column(String(64))
    transcript_leaf_hash: Mapped[str] = mapped_column(String(64))
    revocation_status: Mapped[str] = mapped_column(String(20), default="Valid")

class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cert_id: Mapped[str] = mapped_column(String(50), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    merkle_valid: Mapped[bool] = mapped_column(Boolean)
    watermark_authentic: Mapped[bool] = mapped_column(Boolean)
    cdp_authentic: Mapped[bool] = mapped_column(Boolean)
    composite_score: Mapped[float] = mapped_column(Float)
    audit_reason: Mapped[str] = mapped_column(Text)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with async_session_maker() as session:
        yield session
