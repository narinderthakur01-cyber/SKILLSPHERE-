-- ==============================================================================
-- SkillSphere: PostgreSQL Role and Database Initialization Script
-- Usage: psql -U postgres -h localhost -p 5432 -v app_pwd="YOUR_PASSWORD_HERE" -f init_db.sql
-- ==============================================================================

-- 1. Check if dedicated role 'skillsphere_user' already exists before creating.
-- Never reset existing credentials or overwrite existing users.
\if :{?app_pwd}
  SELECT 'CREATE ROLE skillsphere_user WITH LOGIN PASSWORD ' || quote_literal(:'app_pwd')
  WHERE NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'skillsphere_user')\gexec
\else
  \echo 'ERROR: Variable app_pwd is required. Run with -v app_pwd="<password>"'
\endif

-- 2. Check if database 'skillsphere' already exists before creating.
-- Never drops or overwrites any existing database.
SELECT 'CREATE DATABASE skillsphere OWNER skillsphere_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'skillsphere')\gexec

-- 3. Grant schema permissions to skillsphere_user on skillsphere database
GRANT ALL PRIVILEGES ON DATABASE skillsphere TO skillsphere_user;

\c skillsphere
GRANT ALL ON SCHEMA public TO skillsphere_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO skillsphere_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO skillsphere_user;
