from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from typing import AsyncGenerator
from config import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global engine variable
engine = None
AsyncSessionLocal = None

def get_async_session_local():
    """Get or create the async session factory lazily"""
    global engine, AsyncSessionLocal
    
    if AsyncSessionLocal is None:
        try:
            # Create async engine
            engine = create_async_engine(
                config.DATABASE_URL,
                echo=False,  # Set to False in production
                future=True,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10
            )
            
            # Create async session factory
            AsyncSessionLocal = async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False
            )
            
            logger.info(f"Database engine created for {config.DATABASE_URL}")
        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            raise
    
    return AsyncSessionLocal

# Base class for models
Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session"""
    session_local = get_async_session_local()
    session = session_local()
    try:
        logger.debug("Database session created")
        yield session
    except Exception as e:
        logger.error(f"Database session error: {e}")
        await session.rollback()
        raise
    finally:
        await session.close()
        logger.debug("Database session closed")

async def init_db():
    """Initialize database tables"""
    global engine
    
    # Get the engine (it's already created by get_async_session_local)
    if engine is None:
        engine = create_async_engine(
            config.DATABASE_URL,
            echo=False,
            future=True
        )
    
    try:
        async with engine.begin() as conn:
            # Create tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

async def drop_db():
    """Drop all tables (for testing)"""
    global engine
    
    if engine is None:
        engine = create_async_engine(
            config.DATABASE_URL,
            echo=False,
            future=True
        )
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Failed to drop database: {e}")
        raise

async def close_db():
    """Close database connection"""
    global engine
    if engine is None:
        logger.warning("Database engine already closed or not initialized")
        return
    
    try:
        await engine.dispose()
        engine = None
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Failed to close database connection: {e}")
        raise

# Context manager for testing
class DatabaseSession:
    """Context manager for database sessions"""
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        session_local = get_async_session_local()
        self.session = session_local()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            if exc_type:
                await self.session.rollback()
            await self.session.close()

# Helper function to get session for background tasks
async def get_session() -> AsyncSession:
    """Get a database session for background tasks"""
    session_local = get_async_session_local()
    return session_local()
