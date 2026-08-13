-- ============================================================
-- NileConnect AI Contact Center — Database Init
-- Run this file to bootstrap the database from scratch.
-- Usage:  psql -U postgres -d nileconnect -f init.sql
-- ============================================================

\echo 'Creating schema...'
\i schema.sql

\echo 'Loading seed data...'
\i seed.sql

\echo 'Database ready.'
