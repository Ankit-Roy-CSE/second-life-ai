-- Postgres init script
-- Creates one database per service (single container, logical isolation).
-- The POSTGRES_DB env var already creates slmai_user as the default DB.
-- This script creates the remaining five.

CREATE DATABASE slmai_grading;
CREATE DATABASE slmai_lifecycle;
CREATE DATABASE slmai_passport;
CREATE DATABASE slmai_matching;
CREATE DATABASE slmai_sustainability;

-- Grant all privileges to the shared user
GRANT ALL PRIVILEGES ON DATABASE slmai_grading TO slmai;
GRANT ALL PRIVILEGES ON DATABASE slmai_lifecycle TO slmai;
GRANT ALL PRIVILEGES ON DATABASE slmai_passport TO slmai;
GRANT ALL PRIVILEGES ON DATABASE slmai_matching TO slmai;
GRANT ALL PRIVILEGES ON DATABASE slmai_sustainability TO slmai;
