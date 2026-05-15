-- MFIP logging schema. Idempotent — every statement uses IF NOT EXISTS.
-- Schemas: decisions.md 2026-05-14 "decision_log schema: medium structure"
--          decisions.md 2026-05-14 "security_log schema extension"
--          decisions.md 2026-05-15 "Add row_seq IDENTITY column to log tables
--          for monotonic cursor"
-- Append-only enforcement for security_log lives in the Python writer
-- (mfip/logging/writers.py); see CLAUDE.md rule 3.
--
-- row_seq uses CREATE SEQUENCE + DEFAULT nextval(...) because DuckDB 1.5.2
-- does not support GENERATED ALWAYS AS IDENTITY. End-state semantics
-- (monotonic, NOT NULL, auto-assigned) match what IDENTITY would provide.

CREATE SEQUENCE IF NOT EXISTS seq_decision_log_row_seq;
CREATE SEQUENCE IF NOT EXISTS seq_security_log_row_seq;

CREATE TABLE IF NOT EXISTS decision_log (
    row_seq           BIGINT NOT NULL DEFAULT nextval('seq_decision_log_row_seq'),
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
    row_seq            BIGINT NOT NULL DEFAULT nextval('seq_security_log_row_seq'),
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
