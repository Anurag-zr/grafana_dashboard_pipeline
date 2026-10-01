"""
Dynamically creates and loads data into per-source raw tables.
Raw tables preserve exact CSV columns (as TEXT) for audit/fidelity purposes.
"""

import uuid

import pandas as pd
from sqlalchemy import text

from app.core.db import Database
from app.core.logging_setup import get_logger
from app.core.models import SourceConfig
from app.load.base_loader import AbstractLoader

logger = get_logger(__name__)


class RawLoader(AbstractLoader):

    def __init__(self, db: Database):
        self.db = db

    @staticmethod
    def get_table_name(source_config: SourceConfig) -> str:
        return f"raw_{source_config.source_name.lower()}"

    @staticmethod
    def _quote_identifier(name: str) -> str:
        # Escape any double quotes within the identifier, then wrap in double quotes.
        escaped = name.replace('"', '""')
        return f'"{escaped}"'

    def _table_exists(self, table_name: str) -> bool:
        query = text(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = :table_name
            )
            """
        )
        with self.db.get_engine().connect() as conn:
            result = conn.execute(query, {"table_name": table_name}).scalar()
        return bool(result)

    def ensure_table_exists(self, source_config: SourceConfig, df: pd.DataFrame) -> str:
        table_name = self.get_table_name(source_config)

        if self._table_exists(table_name):
            logger.debug("Raw table '%s' already exists.", table_name)
            return table_name

        column_defs = ", ".join(
            f"{self._quote_identifier(col)} TEXT" for col in df.columns
        )

        create_sql = text(
            f"""
            CREATE TABLE {self._quote_identifier(table_name)} (
                id BIGSERIAL PRIMARY KEY,
                {column_defs},
                batch_id VARCHAR(36) NOT NULL,
                ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )

        with self.db.get_engine().begin() as conn:
            conn.execute(create_sql)

        logger.info("Created raw table '%s' with columns: %s", table_name, list(df.columns))
        return table_name

    def load(self, df: pd.DataFrame, source_config: SourceConfig) -> list[int]:
        """
        Inserts all rows in df into the raw table for this source.
        Returns a list of generated raw row IDs, in the same order as df rows.
        """
        if df.empty:
            logger.info("No rows to load into raw table for '%s'.", source_config.source_name)
            return []

        table_name = self.ensure_table_exists(source_config, df)
        batch_id = str(uuid.uuid4())

        columns = list(df.columns)
        quoted_columns = ", ".join(self._quote_identifier(c) for c in columns)
        placeholders = ", ".join(f":{c}" for c in columns)

        insert_sql = text(
            f"""
            INSERT INTO {self._quote_identifier(table_name)}
                ({quoted_columns}, batch_id)
            VALUES
                ({placeholders}, :batch_id)
            RETURNING id
            """
        )

        raw_ids: list[int] = []
        with self.db.get_engine().begin() as conn:
            for _, row in df.iterrows():
                params = row.to_dict()
                params["batch_id"] = batch_id
                result = conn.execute(insert_sql, params)
                raw_ids.append(result.scalar())

        logger.info(
            "Loaded %d row(s) into '%s' (batch_id=%s)",
            len(raw_ids), table_name, batch_id,
        )
        return raw_ids