"""
Abstract base class defining the loader contract.
"""

from abc import ABC, abstractmethod

import pandas as pd


class AbstractLoader(ABC):
    @abstractmethod
    def load(self, df: pd.DataFrame, *args, **kwargs):
        raise NotImplementedError