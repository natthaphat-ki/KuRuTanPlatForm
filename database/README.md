# Database — Migrations, Seeds & Schema Reference

This folder documents the KuRuTan V2 database. The actual, executable
migration/seed code lives inside the FastAPI service so it can share
SQLAlchemy models (`services/api/app/models/`); this folder is the
database-team-facing reference the [Recommended Repository Structure](/docs/architecture)
calls out separately.

| Sub-folder | Purpose | Executable source of truth |
|---|---|---|
| `init/` | SQL run once when the Postgres container first starts (extensions) | [`001_extensions.sql`](/database/init/001_extensions.sql) — mounted into `/docker-entrypoint-initdb.d` by [docker-compose.yml](/docker-compose.yml) |
| `migrations/` | Reference only — real migrations are Alembic revisions | [`services/api/alembic/versions`](/services/api/alembic/versions) |
| `seeds/` | Reference only — real seed script | [`services/api/scripts/seed_data.py`](/services/api/scripts/seed_data.py) |
| `schema/` | Human-readable schema documentation | [`schema/README.md`](/database/schema/README.md) |

See [docs/database/schema.md](/docs/database/schema.md) for the full table-by-table reference.
