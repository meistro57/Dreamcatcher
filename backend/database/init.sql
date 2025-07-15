-- Dreamcatcher Database Initialization Script
-- This script creates the initial database schema for local development

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS dreamcatcher;

-- Connect to the dreamcatcher database
\c dreamcatcher;

-- Create user if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'dreamcatcher') THEN
        CREATE USER dreamcatcher WITH PASSWORD 'dreamcatcher_password';
    END IF;
END
$$;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE dreamcatcher TO dreamcatcher;
GRANT ALL ON SCHEMA public TO dreamcatcher;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- The actual tables will be created by the FastAPI app using SQLAlchemy
-- This script just ensures the database and user exist