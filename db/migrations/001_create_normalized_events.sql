CREATE TABLE IF NOT EXISTS normalized_events (
    id              BIGSERIAL PRIMARY KEY,
    source_system   VARCHAR(100) NOT NULL,
    source_event_id VARCHAR(255) NOT NULL,
    event_time      DATE NOT NULL,
    status          VARCHAR(100),
    category        VARCHAR(255),
    severity        VARCHAR(50),
    owner           VARCHAR(255),
    description     TEXT,
    details         JSONB NOT NULL DEFAULT '{}',
    raw_table_name  VARCHAR(100) NOT NULL,
    raw_id          BIGINT NOT NULL,
    ingested_at     TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_normalized_events_source_event
        UNIQUE (source_system, source_event_id)
);

CREATE INDEX IF NOT EXISTS idx_normalized_events_event_time
    ON normalized_events (event_time);

CREATE INDEX IF NOT EXISTS idx_normalized_events_source_system
    ON normalized_events (source_system);

CREATE INDEX IF NOT EXISTS idx_normalized_events_details
    ON normalized_events USING GIN (details);