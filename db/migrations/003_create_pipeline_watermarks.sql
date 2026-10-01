CREATE TABLE IF NOT EXISTS pipeline_watermarks (
    source_name     VARCHAR(100) PRIMARY KEY,
    last_value      VARCHAR(255),
    last_run_at     TIMESTAMP NOT NULL DEFAULT NOW()
);