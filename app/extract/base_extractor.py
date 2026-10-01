"""
Abstract base class defining the extractor contract.
Allows swapping CSV-based extraction for API-based extraction later
without changing Pipeline code.
"""

from abc import ABC, abstractmethod

import pandas as pd

from app.core.models import SourceConfig


class AbstractExtractor(ABC):
    @abstractmethod
    def extract(self, source_config: SourceConfig, last_watermark: int) -> pd.DataFrame:
        """
        Returns only the new rows for this source, beyond what was
        already processed (as tracked by last_watermark).
        """
        raise NotImplementedError