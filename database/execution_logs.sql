-- =============================================================================
-- EXECUTION LOGS TABLE
-- Ultra-simple table for testing and debugging
-- Just stores raw inputs/outputs as JSON blobs
-- =============================================================================

CREATE TABLE execution_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- What ran
    automation_slug VARCHAR(200),          -- Reference to automation (optional)
    worker_name VARCHAR(200),              -- e.g., "scrapers.permits", "research.entity"
    
    -- Timing
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    runtime_seconds FLOAT,
    
    -- Status
    status VARCHAR(50) DEFAULT 'running',  -- running, success, failed, timeout
    
    -- The good stuff (all JSON blobs)
    input JSONB,                           -- Raw input params
    output JSONB,                          -- Raw output (whatever the worker returned)
    error JSONB,                           -- Error details if failed
    metadata JSONB,                        -- Anything else (progress updates, stats, etc.)
    
    -- Simple text fields for quick scanning
    notes TEXT,                            -- Your notes ("testing new endpoint")
    tags TEXT[]                            -- Quick tags ["test", "permits", "va"]
);

-- Index for quick lookups
CREATE INDEX idx_logs_automation ON execution_logs(automation_slug);
CREATE INDEX idx_logs_worker ON execution_logs(worker_name);
CREATE INDEX idx_logs_status ON execution_logs(status);
CREATE INDEX idx_logs_started ON execution_logs(started_at DESC);
CREATE INDEX idx_logs_tags ON execution_logs USING GIN(tags);

-- =============================================================================
-- HELPER FUNCTIONS
-- =============================================================================

-- Quick insert for testing
CREATE OR REPLACE FUNCTION log_start(
    p_worker VARCHAR,
    p_input JSONB,
    p_automation_slug VARCHAR DEFAULT NULL,
    p_notes TEXT DEFAULT NULL,
    p_tags TEXT[] DEFAULT '{}'
) RETURNS UUID AS $$
DECLARE
    log_id UUID;
BEGIN
    INSERT INTO execution_logs (worker_name, automation_slug, input, notes, tags)
    VALUES (p_worker, p_automation_slug, p_input, p_notes, p_tags)
    RETURNING id INTO log_id;
    RETURN log_id;
END;
$$ LANGUAGE plpgsql;

-- Mark complete with output
CREATE OR REPLACE FUNCTION log_complete(
    p_log_id UUID,
    p_output JSONB,
    p_metadata JSONB DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    UPDATE execution_logs SET
        status = 'success',
        completed_at = NOW(),
        runtime_seconds = EXTRACT(EPOCH FROM (NOW() - started_at)),
        output = p_output,
        metadata = COALESCE(metadata, '{}') || COALESCE(p_metadata, '{}')
    WHERE id = p_log_id;
END;
$$ LANGUAGE plpgsql;

-- Mark failed with error
CREATE OR REPLACE FUNCTION log_fail(
    p_log_id UUID,
    p_error JSONB
) RETURNS VOID AS $$
BEGIN
    UPDATE execution_logs SET
        status = 'failed',
        completed_at = NOW(),
        runtime_seconds = EXTRACT(EPOCH FROM (NOW() - started_at)),
        error = p_error
    WHERE id = p_log_id;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- VIEWS FOR QUICK INSPECTION
-- =============================================================================

-- Recent runs (last 50)
CREATE VIEW v_recent_logs AS
SELECT 
    id,
    worker_name,
    automation_slug,
    status,
    runtime_seconds,
    started_at,
    notes,
    tags,
    -- Truncated previews
    LEFT(input::text, 200) as input_preview,
    LEFT(output::text, 200) as output_preview,
    LEFT(error::text, 200) as error_preview
FROM execution_logs
ORDER BY started_at DESC
LIMIT 50;

-- Failed runs
CREATE VIEW v_failed_logs AS
SELECT * FROM execution_logs
WHERE status = 'failed'
ORDER BY started_at DESC
LIMIT 20;

-- =============================================================================
-- EXAMPLE USAGE
-- =============================================================================

-- Start a test run:
-- SELECT log_start('scrapers.permits', '{"endpoint": "https://..."}', 'va-loudoun-permits', 'testing new filters', ARRAY['test', 'permits']);
-- Returns: UUID of the log entry

-- Complete it:
-- SELECT log_complete('uuid-here', '{"records_found": 42, "data": [...]}');

-- Or fail it:
-- SELECT log_fail('uuid-here', '{"message": "Connection timeout", "traceback": "..."}');

-- Quick inspect:
-- SELECT * FROM v_recent_logs;
-- SELECT * FROM execution_logs WHERE 'test' = ANY(tags);
-- SELECT * FROM execution_logs WHERE automation_slug = 'va-loudoun-permits' ORDER BY started_at DESC LIMIT 5;
