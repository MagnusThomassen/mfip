-- MFIP logging schema. Idempotent — every statement uses IF NOT EXISTS.
-- Schemas: decisions.md 2026-05-14 "decision_log schema: medium structure"
--          decisions.md 2026-05-14 "security_log schema extension"
-- Append-only enforcement for security_log lives in the Python writer
-- (mfip/logging/writers.py); see CLAUDE.md rule 3.

CREATE TABLE IF NOT EXISTS decision_log (
    id                UUID PRIMARY KEY,
    correlation_id    UUID NOT NULL,
    timestamp         TIMESTAMP NOT NULL DEFAULT current_timestamp,
    agent             VARCHAR NOT NULL,
    decision_type     VARCHAR NOT NULL,
    phase             VARCHAR NOT NULL,
    ticker            VARCHAR(10),
    confidence_score  DECIMAL(4,3),
    payload           JSON NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_decision_log_correlation
    ON decision_log (correlation_id);
CREATE INDEX IF NOT EXISTS idx_decision_log_ticker_ts
    ON decision_log (ticker, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_decision_log_phase_ts
    ON decision_log (phase, timestamp DESC);

CREATE TABLE IF NOT EXISTS security_log (
    log_id             UUID PRIMARY KEY,
    correlation_id     UUID,  -- nullable: system-level events outside pipeline runs
    timestamp          TIMESTAMP NOT NULL DEFAULT current_timestamp,
    severity           VARCHAR NOT NULL
                       CHECK (severity IN ('Advisory', 'Warning', 'Critical')),
    issuing_agent      VARCHAR NOT NULL,
    flagging_officer   VARCHAR,
    issue_description  TEXT NOT NULL,
    impact_assessment  TEXT,
    recommended_action TEXT,
    pipeline_status    VARCHAR,
    resolved_at        TIMESTAMP,
    resolution_note    TEXT
);

CREATE INDEX IF NOT EXISTS idx_security_log_severity_ts
    ON security_log (severity, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_security_log_correlation
    ON security_log (correlation_id);
