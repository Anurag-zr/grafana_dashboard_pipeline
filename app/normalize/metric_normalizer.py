"""
Normalizes Type B (metric/periodic-aggregate) raw data into the common
normalized_metrics shape. Supports two input shapes:
  - wide: multiple metric columns per row (melted into multiple rows)
  - long: metric name/value already in two columns (reshaped/relabeled)
"""

from datetime import timedelta

import pandas as pd

from app.core.logging_setup import get_logger
from app.core.models import SourceConfig, MetricMode, PeriodAnchor
from app.normalize.base_normalizer import AbstractNormalizer

logger = get_logger(__name__)


class MetricNormalizer(AbstractNormalizer):

    def normalize(self, df: pd.DataFrame, source_config: SourceConfig, raw_ids: list[int]) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame(columns=[
                "source_system", "metric_name", "metric_value", "metric_rank",
                "period_start", "period_end", "source_row_key",
                "raw_table_name", "raw_id",
            ])

        working = df.reset_index(drop=True).copy()
        working["_raw_id"] = raw_ids

        if source_config.metric_mode == MetricMode.WIDE:
            long_df = self._melt_wide(working, source_config)
        elif source_config.metric_mode == MetricMode.LONG:
            long_df = self._reshape_long(working, source_config)
        else:
            raise ValueError(f"Unknown metric_mode for '{source_config.source_name}'")

        long_df = long_df.reset_index(drop=True)
        result_df = self._finalize(long_df, source_config)

        logger.info(
            "Normalized %d metric row(s) for '%s' (mode=%s)",
            len(result_df), source_config.source_name, source_config.metric_mode,
        )
        return result_df

    def _melt_wide(self, df: pd.DataFrame, source_config: SourceConfig) -> pd.DataFrame:
        date_col = source_config.date_column
        metric_cols = source_config.metric_columns

        id_vars = [date_col, "_raw_id"]
        melted = df.melt(
            id_vars=id_vars,
            value_vars=metric_cols,
            var_name="metric_name",
            value_name="metric_value",
        )
        melted["metric_rank"] = 0
        melted["source_row_key"] = None
        melted = melted.rename(columns={date_col: "_date"})
        return melted

    def _reshape_long(self, df: pd.DataFrame, source_config: SourceConfig) -> pd.DataFrame:
        date_col = source_config.date_column
        dim_col = source_config.dimension_column
        val_col = source_config.value_column
        rank_col = source_config.rank_column
        row_key_col = source_config.row_key_column

        reshaped = df[[date_col, dim_col, val_col, "_raw_id"]].copy()
        reshaped = reshaped.rename(columns={
            date_col: "_date",
            dim_col: "metric_name",
            val_col: "metric_value",
        })

        reshaped["metric_rank"] = df[rank_col].values if rank_col and rank_col in df.columns else None
        reshaped["source_row_key"] = df[row_key_col].values if row_key_col and row_key_col in df.columns else None

        return reshaped

    def _compute_period(self, date_series: pd.Series, source_config: SourceConfig):
        parsed_dates = pd.to_datetime(
            date_series, format="mixed", dayfirst=False, errors="coerce"
        )

        unparsed = parsed_dates.isna() & date_series.notna()
        if unparsed.any():
            logger.warning(
                "%d date value(s) could not be parsed for '%s'. Offending raw values: %s",
                unparsed.sum(), source_config.source_name,
                date_series[unparsed].tolist(),
            )

        period_days = source_config.period_days
        delta = timedelta(days=period_days - 1)

        if source_config.period_anchor == PeriodAnchor.END:
            period_end = parsed_dates
            period_start = parsed_dates - delta
        else:
            period_start = parsed_dates
            period_end = parsed_dates + delta

        return period_start.dt.date.values, period_end.dt.date.values


    def _finalize(self, long_df: pd.DataFrame, source_config: SourceConfig) -> pd.DataFrame:
        period_start_vals, period_end_vals = self._compute_period(long_df["_date"], source_config)

        result = pd.DataFrame({
            "source_system": [source_config.source_system] * len(long_df),
            "metric_name": long_df["metric_name"].values,
            "metric_value": pd.to_numeric(long_df["metric_value"], errors="coerce").values,
            "metric_rank": pd.to_numeric(long_df["metric_rank"], errors="coerce").values,
            "period_start": period_start_vals,
            "period_end": period_end_vals,
            "source_row_key": long_df["source_row_key"].values,
            "raw_table_name": [f"raw_{source_config.source_name.lower()}"] * len(long_df),
            "raw_id": long_df["_raw_id"].values,
        })

        bad_values = result["metric_value"].isna().sum()
        if bad_values > 0:
            logger.warning(
                "%d row(s) in '%s' had unparseable metric_value.",
                bad_values, source_config.source_name,
            )

        return result