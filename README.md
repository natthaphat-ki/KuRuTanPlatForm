# KuRuTan V2

Credit / Discredit Digital Trust & Fraud Intelligence.

This repository follows the [KuRuTan V2 Phase Plan](/docs) — see
`docs/` for the full phase breakdown. **Phase 2 — Database & Backend
Foundation** is implemented: PostgreSQL + pgvector, Alembic migrations,
seed data, and the FastAPI Core (models / schemas / services / routers,
JWT auth, and role-based authorization).

## Repository structure

```
KuRuTan/
├── apps/
│   ├── mobile/        # Flutter User App (Phase 8)
│   └── admin/         # React Admin Web (Phase 9)
├── services/
│   ├── api/           # FastAPI Backend — Phase 2
│   └── ai/            # AI / NLP / RAG Service (Phase 6)
├── database/
│   ├── init/          # SQL run once when Postgres first starts (extensions)
│   ├── migrations/     # Reference — real migrations are Alembic (services/api/alembic)
│   ├── seeds/          # Reference — real seed script (services/api/scripts/seed_data.py)
│   └── schema/         # Human-readable schema documentation
├── docs/
│   ├── database/       # Schema reference
│   └── api/            # API reference (Swagger/ReDoc pointers)
├── .env.example
├── docker-compose.yml
└── README.md
```

## Quick start (Phase 2 — local development)

Requires Docker Desktop.

```powershell
# 1. Copy environment defaults
Copy-Item .env.example .env

# 2. Start Postgres (pgvector) + FastAPI (auto-runs `alembic upgrade head` on boot)
docker compose up -d

# 3. Seed baseline data (admin/officer accounts, factors, platforms, sample seller)
docker compose exec api python -m scripts.seed_data
```

Then open:

- API docs (Swagger): http://localhost:8000/docs
- Health check: http://localhost:8000/health

Seeded accounts (change the password before any shared/staging use):

| Email | Password | Role |
|---|---|---|
| `admin@kurutan.dev` | `ChangeMe123!` | admin |
| `officer@kurutan.dev` | `ChangeMe123!` | officer |

## Development

See [`services/api/README.md`](/services/api/README.md) for backend-specific
commands (migrations, tests).

## Critical Rules (from the Phase Plan)

- Credit / Discredit is the **Core Domain**, not a side feature.
- Every Credit/Discredit point must be traceable back to its Factor and
  Evidence/Report — never store only the final score.
- An un-verified Report must never be auto-interpreted as proven wrongdoing.
- Dispute / Appeal is part of the architecture from the start.
- LLM does not decide scores directly; it only explains using RAG-retrieved context (Phase 6).
- ThaiID / external integration is out of current scope (Phase 12).
