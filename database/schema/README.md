# Schema Reference

The authoritative schema is defined by the SQLAlchemy models in
[`services/api/app/models/`](/services/api/app/models) and versioned as Alembic
migrations in [`services/api/alembic/versions`](/services/api/alembic/versions).

This folder exists per the Recommended Repository Structure to hold
human-readable schema documentation for the Database/Backend team. See
[docs/database/schema.md](/docs/database/schema.md) for the full table-by-table
description grouped by domain (Identity, Evidence, Credit / Discredit,
Fraud Intelligence, Governance, AI Data), matching the KuRuTan V2 Phase Plan.
