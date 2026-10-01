"""
Builds fully-wired Pipeline instances for a given source config.
"""

from app.core.db import Database
from app.core.models import SourceConfig
from app.extract.csv_extractor import CSVExtractor
from app.extract.watermark_store import WatermarkStore
from app.load.raw_loader import RawLoader
from app.load.normalized_loader import NormalizedLoader
from app.pipeline.pipeline import Pipeline


class PipelineFactory:

    def __init__(self, db: Database):
        self.db = db
        self.extractor = CSVExtractor()
        self.raw_loader = RawLoader(db)
        self.normalized_loader = NormalizedLoader(db)
        self.watermark_store = WatermarkStore(db)

    def build(self, source_config: SourceConfig) -> Pipeline:
        return Pipeline(
            source_config=source_config,
            db=self.db,
            extractor=self.extractor,
            raw_loader=self.raw_loader,
            normalized_loader=self.normalized_loader,
            watermark_store=self.watermark_store,
        )