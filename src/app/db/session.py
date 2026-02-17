"""
Database Session Management.

Provides async SQLAlchemy 2.0 session management with proper
connection pooling and dependency injection pattern for PostgreSQL.
"""
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from ..core.config import get_settings, Settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    
    Provides declarative base with common configurations.
    All models should inherit from this class.
    """
    pass


class DatabaseManager:
    """
    Manages PostgreSQL database connections and sessions.
    
    Implements the singleton pattern for connection management
    with async connection pooling.
    """
    
    _engine: AsyncEngine | None = None
    _session_factory: async_sessionmaker[AsyncSession] | None = None
    
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
    
    def _create_engine(self) -> AsyncEngine:
        """Create async SQLAlchemy engine for PostgreSQL."""
        database_url = self.settings.DATABASE_URL
        
        engine = create_async_engine(
            database_url,
            echo=self.settings.DATABASE_ECHO,
            pool_size=self.settings.DATABASE_POOL_SIZE,
            max_overflow=self.settings.DATABASE_MAX_OVERFLOW,
            pool_timeout=self.settings.DATABASE_POOL_TIMEOUT,
            pool_pre_ping=True,
        )
        logger.info(
            f"Created PostgreSQL engine with pool_size={self.settings.DATABASE_POOL_SIZE}"
        )
        
        return engine
    
    @property
    def engine(self) -> AsyncEngine:
        """Get or create the database engine."""
        if self._engine is None:
            self._engine = self._create_engine()
        return self._engine
    
    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get or create the session factory."""
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False,
            )
        return self._session_factory
    
    async def create_tables(self) -> None:
        """Create all tables defined in models."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")
    
    async def drop_tables(self) -> None:
        """Drop all tables (use with caution!)."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.warning("Database tables dropped")
    
    async def close(self) -> None:
        """Close database connections."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database connections closed")
    
    async def health_check(self) -> dict:
        """Check database health."""
        from sqlalchemy import text
        try:
            async with self.session_factory() as session:
                await session.execute(text("SELECT 1"))
            return {"status": "healthy", "error": None}
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Async context manager for database sessions.
        
        Usage:
            async with db_manager.session() as session:
                result = await session.execute(query)
        """
        session = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Global database manager instance
_db_manager: DatabaseManager | None = None


def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.
    
    Provides a session that auto-commits on success and
    rolls back on exception.
    """
    db_manager = get_db_manager()
    async with db_manager.session() as session:
        yield session


# Type alias for dependency injection
DbSession = Annotated[AsyncSession, Depends(get_db)]


async def init_db() -> None:
    """Initialize database on application startup."""
    db_manager = get_db_manager()
    await db_manager.create_tables()


async def close_db() -> None:
    """Close database connections on application shutdown."""
    db_manager = get_db_manager()
    await db_manager.close()
