"""
Database connectivity setup using SQLAlchemy.
Provides a single, shared engine and session factory for the whole app.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from app.core.logging_setup import get_logger
from app.core.models import GlobalSettings

logger = get_logger(__name__)


class Database:
    """
    Wraps SQLAlchemy engine/session creation based on GlobalSettings.
    One Database instance is expected to live for the lifetime of the app.
    """

    def __init__(self, settings: GlobalSettings):
        self.settings = settings
        self._engine = create_engine(settings.db_url, pool_pre_ping=True)
        self._session_factory = sessionmaker(bind=self._engine, expire_on_commit=False)
        logger.info("Database engine initialized for %s", settings.db_url.split("@")[-1])

    def get_engine(self):
        return self._engine

    def get_session(self) -> Session:
        return self._session_factory()

    def test_connection(self) -> bool:
        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection test succeeded.")
            return True
        except Exception as e:
            logger.error("Database connection test failed: %s", e)
            return False