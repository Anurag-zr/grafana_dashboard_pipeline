"""
Abstract base class defining the normalizer contract.
"""

from abc import ABC, abstractmethod

import pandas as pd

from app.core.models import SourceConfig


class AbstractNormalizer(ABC):
    @abstractmethod
    def normalize(self, df: pd.DataFrame, source_config: SourceConfig, raw_ids: list[int]) -> pd.DataFrame:
        """
        Transforms a raw dataframe into the normalized schema shape
        (normalized_events or normalized_metrics columns).
        raw_ids must be the same length and order as df rows, so each
        normalized row can be traced back to its raw table row.
        """
        raise NotImplementedError