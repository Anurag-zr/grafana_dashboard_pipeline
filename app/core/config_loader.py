"""
Loads and validates pipeline configuration from sources.yaml and .env.
"""

from pathlib import Path

import yaml

from app.core.logging_setup import get_logger
from app.core.models import GlobalSettings, SourceConfig

logger = get_logger(__name__)


class ConfigLoader:
    """
    Responsible for reading sources.yaml and producing validated SourceConfig
    objects, plus loading GlobalSettings from environment/.env.
    """

    def __init__(self, sources_yaml_path: str = "./config/sources.yaml"):
        self.sources_yaml_path = Path(sources_yaml_path)

    def load_sources(self) -> list[SourceConfig]:
        """
        Reads sources.yaml, validates each entry into a SourceConfig.
        Collects and logs all validation errors rather than failing on the first one.
        Returns only the successfully validated sources.
        """
        if not self.sources_yaml_path.exists():
            raise FileNotFoundError(
                f"sources.yaml not found at path: {self.sources_yaml_path}"
            )

        with open(self.sources_yaml_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        raw_sources = raw.get("sources", []) if raw else []
        if not raw_sources:
            logger.warning("No sources found in %s", self.sources_yaml_path)
            return []

        valid_configs: list[SourceConfig] = []
        errors: list[str] = []

        for index, entry in enumerate(raw_sources):
            source_label = entry.get("source_name", f"<unnamed entry #{index}>")
            try:
                config = SourceConfig(**entry)
                valid_configs.append(config)
                logger.info("Loaded source config: %s", source_label)
            except Exception as e:
                errors.append(f"Source '{source_label}': {e}")

        if errors:
            logger.error(
                "Encountered %d invalid source config(s):\n%s",
                len(errors),
                "\n".join(errors),
            )

        logger.info(
            "Config load complete | valid=%d | invalid=%d | total=%d",
            len(valid_configs),
            len(errors),
            len(raw_sources),
        )

        return valid_configs

    def load_enabled_sources(self) -> list[SourceConfig]:
        """
        Convenience method: returns only sources where enabled=True.
        """
        all_sources = self.load_sources()
        enabled = [s for s in all_sources if s.enabled]
        logger.info("Enabled sources: %d of %d", len(enabled), len(all_sources))
        return enabled

    @staticmethod
    def load_settings() -> GlobalSettings:
        """
        Loads global application settings from environment variables / .env.
        """
        settings = GlobalSettings()
        logger.info(
            "Global settings loaded | db=%s:%s/%s | log_level=%s",
            settings.db_host,
            settings.db_port,
            settings.db_name,
            settings.log_level,
        )
        return settings