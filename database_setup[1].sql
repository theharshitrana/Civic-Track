-- Enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create issues table
CREATE TABLE IF NOT EXISTS issues (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    status VARCHAR(20) DEFAULT 'reported',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create spatial index
CREATE INDEX IF NOT EXISTS idx_issues_location ON issues USING GIST(location);

-- Add status options
ALTER TABLE issues 
    ADD CONSTRAINT status_check 
    CHECK (status IN ('reported', 'in_progress', 'resolved'));

-- Verify setup
SELECT 
    'PostGIS' AS check, 
    PostGIS_version() AS result
UNION ALL
SELECT 
    'Table Exists', 
    EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'issues')::TEXT
UNION ALL
SELECT 
    'Spatial Index Exists',
    EXISTS(
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'issues' AND indexname = 'idx_issues_location'
    )::TEXT;