# Migrations

Migrations are managed with **Alembic** inside the FastAPI service so they
can import the SQLAlchemy models directly (single source of truth, no schema
drift between code and database).

- Config: [`services/api/alembic.ini`](/services/api/alembic.ini)
- Environment wiring: [`services/api/alembic/env.py`](/services/api/alembic/env.py)
- Revisions: [`services/api/alembic/versions`](/services/api/alembic/versions)

## Common commands (run from `services/api/`, or via `docker compose run --rm api ...`)

```powershell
# Create a new revision from model changes
alembic revision --autogenerate -m "describe the change"

# Apply all pending migrations
alembic upgrade head

# Roll back the last migration
alembic downgrade -1
```
