-- =============================================================================
-- Postgres multi-DB init script for Amazon Second Life AI
-- =============================================================================
-- The default database (slmai_user) is already created by the Postgres image
-- via POSTGRES_DB. This script creates the remaining service databases
-- and ensures the shared user has full access to each.
--
-- Run order: this file is mounted at /docker-entrypoint-initdb.d/00_init.sql
-- and runs exactly once when the data volume is first created.
-- =============================================================================

-- Gateway service DB (owns Return table)
SELECT 'CREATE DATABASE slmai_gateway OWNER slmai'
  WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'slmai_gateway') \gexec

-- Grading service DB
SELECT 'CREATE DATABASE slmai_grading OWNER slmai'
  WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'slmai_grading') \gexec

-- Lifecycle Decision service DB
SELECT 'CREATE DATABASE slmai_lifecycle OWNER slmai'
  WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'slmai_lifecycle') \gexec

-- Product Passport service DB
SELECT 'CREATE DATABASE slmai_passport OWNER slmai'
  WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'slmai_passport') \gexec

-- Hyperlocal Matching service DB
SELECT 'CREATE DATABASE slmai_matching OWNER slmai'
  WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'slmai_matching') \gexec

-- Sustainability service DB
SELECT 'CREATE DATABASE slmai_sustainability OWNER slmai'
  WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'slmai_sustainability') \gexec

-- Grant privileges (belt-and-suspenders; OWNER already implies full access)
GRANT ALL PRIVILEGES ON DATABASE slmai_gateway TO slmai;
GRANT ALL PRIVILEGES ON DATABASE slmai_grading TO slmai;
GRANT ALL PRIVILEGES ON DATABASE slmai_lifecycle TO slmai;
GRANT ALL PRIVILEGES ON DATABASE slmai_passport TO slmai;
GRANT ALL PRIVILEGES ON DATABASE slmai_matching TO slmai;
GRANT ALL PRIVILEGES ON DATABASE slmai_sustainability TO slmai;
