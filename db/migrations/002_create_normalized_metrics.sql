CREATE TABLE IF NOT EXISTS normalized_metrics (
    id              BIGSERIAL PRIMARY KEY,
    source_system   VARCHAR(100) NOT NULL,
    metric_name     VARCHAR(255) NOT NULL,
    metric_value    NUMERIC NOT NULL,
    metric_rank            INTEGER,
    period_start    DATE NOT NULL,
    period_end      DATE NOT NULL,
    source_row_key  VARCHAR(255),
    raw_table_name  VARCHAR(100) NOT NULL,
    raw_id          BIGINT NOT NULL,
    ingested_at     TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_normalized_metrics_natural_key
        UNIQUE (source_system, metric_name, period_end, metric_rank)
);

CREATE INDEX IF NOT EXISTS idx_normalized_metrics_period
    ON normalized_metrics (period_start, period_end);

CREATE INDEX IF NOT EXISTS idx_normalized_metrics_source_system
    ON normalized_metrics (source_system);

CREATE INDEX IF NOT EXISTS idx_normalized_metrics_metric_name
    ON normalized_metrics (metric_name);