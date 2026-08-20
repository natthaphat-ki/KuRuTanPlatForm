-- Phase 2: enable required PostgreSQL extensions before any migration runs.
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
