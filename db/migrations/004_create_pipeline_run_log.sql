CREATE TABLE IF NOT EXISTS pipeline_run_log (
    id              BIGSERIAL PRIMARY KEY,
    source_name     VARCHAR(100) NOT NULL,
    run_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    rows_extracted  INTEGER,
    rows_loaded     INTEGER,
    status          VARCHAR(20) NOT NULL,   -- SUCCESS | FAILED | PARTIAL
    error_message   TEXT
);

CREATE INDEX IF NOT EXISTS idx_pipeline_run_log_source_time
    ON pipeline_run_log (source_name, run_at);