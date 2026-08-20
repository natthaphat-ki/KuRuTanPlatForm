# KuRuTan V2 — FastAPI Backend (services/api)

## Structure

```
app/
├── main.py            # FastAPI app + router wiring
├── core/              # config, security (JWT/password hashing), permissions, deps
├── database/          # engine/session (session.py), declarative base + mixins (base.py)
├── models/            # SQLAlchemy ORM models (one module per domain group)
├── schemas/           # Pydantic request/response schemas
├── routers/           # API endpoints
└── services/          # business logic used by routers
alembic/               # migrations (env.py wired to app settings + models)
scripts/seed_data.py   # idempotent baseline seed data
tests/                 # pytest suite (TestClient + real DB)
```

## Local development (without Docker)

Requires Python 3.12+ and a reachable Postgres with the `vector` extension.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
$env:DATABASE_URL = "postgresql+psycopg://kurutan:kurutan@localhost:5432/kurutan"
alembic upgrade head
uvicorn app.main:app --reload
```

## Via Docker Compose (recommended)

From the repository root:

```powershell
docker compose up -d
docker compose exec api python -m scripts.seed_data
```

## Migrations

```powershell
# create a new revision after changing app/models/*
docker compose run --rm api alembic revision --autogenerate -m "describe change"
docker compose run --rm api alembic upgrade head
```

## Tests

```powershell
docker compose run --rm api sh -c "pip install -q -r requirements-dev.txt && pytest -q"
```
