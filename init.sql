-- Initialize database with TimescaleDB extension and initial data

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create hypertables after the main tables are created
-- This will be done in a separate migration after table creation

-- Insert initial AI tools data
DO $$ 
BEGIN
    -- This will be executed after tables are created via Alembic
    RAISE NOTICE 'Database initialized with TimescaleDB support';
END $$;