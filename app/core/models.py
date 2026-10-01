"""
Core pydantic models for the CSV ingestion pipeline.

SourceConfig  -> validated representation of one entry in sources.yaml
GlobalSettings -> validated representation of environment/.env settings
"""

import re
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SourceType(str, Enum):
    EVENT = "event"
    METRIC = "metric"


class MetricMode(str, Enum):
    WIDE = "wide"
    LONG = "long"


class PeriodAnchor(str, Enum):
    START = "start"
    END = "end"


_POLL_INTERVAL_PATTERN = re.compile(r"^\d+[smhd]$")  # e.g. 30s, 15m, 6h, 1d


class SourceConfig(BaseModel):
    """
    Validated configuration for a single CSV source, as defined in sources.yaml.
    Supports two shapes: EVENT (row-per-incident) and METRIC (periodic aggregates).
    """

    # --- Common fields (required for every source) ---
    source_name: str
    source_system: str
    source_type: SourceType
    file_path: str
    poll_interval: str = Field(..., description="e.g. '1d', '6h', '30m', '45s'")
    enabled: bool = True

    # --- Event-only fields ---
    id_column: Optional[str] = None
    column_mapping: Optional[dict[str, str]] = None

    # --- Metric-only fields ---
    date_column: Optional[str] = None
    period_days: Optional[int] = None
    period_anchor: Optional[PeriodAnchor] = None
    metric_mode: Optional[MetricMode] = None
    metric_columns: Optional[list[str]] = None       # required if metric_mode == WIDE
    dimension_column: Optional[str] = None            # required if metric_mode == LONG
    value_column: Optional[str] = None                 # required if metric_mode == LONG
    rank_column: Optional[str] = None                  # optional, LONG mode only
    row_key_column: Optional[str] = None                # optional, LONG mode only

    @model_validator(mode="after")
    def validate_poll_interval_format(self) -> "SourceConfig":
        if not _POLL_INTERVAL_PATTERN.match(self.poll_interval):
            raise ValueError(
                f"Invalid poll_interval '{self.poll_interval}' for source "
                f"'{self.source_name}'. Expected format like '1d', '6h', '30m', '45s'."
            )
        return self

    @model_validator(mode="after")
    def validate_type_specific_fields(self) -> "SourceConfig":
        if self.source_type == SourceType.EVENT:
            if not self.id_column:
                raise ValueError(
                    f"Source '{self.source_name}' is type EVENT but missing 'id_column'."
                )
            if not self.date_column:
                raise ValueError(
                    f"Source '{self.source_name}' is type EVENT but missing 'date_column'."
                )

        elif self.source_type == SourceType.METRIC:
            if not self.date_column:
                raise ValueError(
                    f"Source '{self.source_name}' is type METRIC but missing 'date_column'."
                )
            if self.period_days is None:
                raise ValueError(
                    f"Source '{self.source_name}' is type METRIC but missing 'period_days'."
                )
            if self.period_anchor is None:
                raise ValueError(
                    f"Source '{self.source_name}' is type METRIC but missing 'period_anchor'."
                )
            if self.metric_mode is None:
                raise ValueError(
                    f"Source '{self.source_name}' is type METRIC but missing 'metric_mode'."
                )

            if self.metric_mode == MetricMode.WIDE:
                if not self.metric_columns:
                    raise ValueError(
                        f"Source '{self.source_name}' uses metric_mode=WIDE but "
                        f"missing 'metric_columns'."
                    )
            elif self.metric_mode == MetricMode.LONG:
                if not self.dimension_column or not self.value_column:
                    raise ValueError(
                        f"Source '{self.source_name}' uses metric_mode=LONG but "
                        f"missing 'dimension_column' and/or 'value_column'."
                    )

        return self


class GlobalSettings(BaseSettings):
    """
    Global application settings, loaded from environment variables / .env file.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    db_host: str = Field(alias="DB_HOST")
    db_port: int = Field(alias="DB_PORT")
    db_name: str = Field(alias="DB_NAME")
    db_user: str = Field(alias="DB_USER")
    db_password: str = Field(alias="DB_PASSWORD")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_path: str = Field(default="./logs/pipeline.log", alias="LOG_PATH")

    @property
    def db_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )
