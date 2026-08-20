# Database Schema — v1 (Phase 2)

Source of truth: [`services/api/app/models/`](/services/api/app/models) (SQLAlchemy)
+ [`services/api/alembic/versions`](/services/api/alembic/versions) (Alembic migrations).

All tables use a UUID primary key (`id`) and `created_at` / `updated_at`
timestamps (see `UUIDPrimaryKeyMixin` / `TimestampMixin` in
[`app/database/base.py`](/services/api/app/database/base.py)) unless noted otherwise.

## Identity

| Table | Model | Notes |
|---|---|---|
| `users` | [`User`](/services/api/app/models/user.py) | `email` (unique), `hashed_password`, `role` (`public`/`user`/`admin`/`officer`), `is_active` |
| `sellers` | [`Seller`](/services/api/app/models/seller.py) | `display_name`, `entity_type` (`individual`/`business`), `description` |
| `seller_platforms` | [`SellerPlatform`](/services/api/app/models/seller.py) | Catalogue of channels (Facebook, Shopee, Line, ...) |
| `seller_accounts` | [`SellerAccount`](/services/api/app/models/seller.py) | A Seller's handle on a specific `SellerPlatform` |

## Evidence

| Table | Model | Notes |
|---|---|---|
| `reports` | [`Report`](/services/api/app/models/report.py) | `status` defaults to `UNVERIFIED` (never auto-interpreted as proven wrongdoing — Presumption of Innocence Rule). Full lifecycle: `UNVERIFIED → PENDING_REVIEW → VERIFIED/REJECTED`, then `VERIFIED → APPEALED → VOIDED` on a successful appeal. `reference_key` + `duplicate_of_report_id` support basic Duplicate Check. |
| `evidences` | [`Evidence`](/services/api/app/models/evidence.py) | File metadata attached to a `Report`; `file_size_bytes`, `file_type`, `file_metadata` (JSONB), optional `comment`. At least one `file_type=IMAGE` evidence is required before a Report can move to `PENDING_REVIEW` (Minimum Evidence Rule). `file_hash` (SHA-256) + `duplicate_of_evidence_id` implement the "สลิปเดียวกัน" (same file) Duplicate Check across all reports — see [`app/core/storage.py`](/services/api/app/core/storage.py) (Phase 3 local disk backend). |
| `verifications` | [`Verification`](/services/api/app/models/evidence.py) | Officer/Admin decision record on a `Report` (who, verdict, notes) |

## Credit / Discredit

Score formulas (Critical Rule — Traceability): every point is stored as a
ledger row referencing the `Factor` + optional `Report`/`Evidence`, never
just a running total.

- **Credit Score** = Σ(`credit_ledger.factor_weight` × `credit_ledger.status_factor`)
- **Discredit Score** = Σ(`discredit_ledger.factor_weight` × `discredit_ledger.verification_impact_multiplier`), excluding voided entries

| Table | Model | Notes |
|---|---|---|
| `credit_factors` / `discredit_factors` | [`CreditFactor` / `DiscreditFactor`](/services/api/app/models/credit.py) | Definable reasons points are awarded/applied, with a `default_weight` |
| `credit_ledger` | [`CreditLedger`](/services/api/app/models/credit.py) | **Immutable, traceable** entries: `factor_weight`, `status_factor`, `points` (= weight × status factor), always linked to the `Factor` + optional `Report`/`Evidence` |
| `discredit_ledger` | [`DiscreditLedger`](/services/api/app/models/credit.py) | Same shape as `credit_ledger` plus `verification_impact_multiplier` and a void trail (`is_voided`, `voided_at`, `voided_by`, `voided_reason`) — an overturned appeal flags the row instead of deleting it |
| `credit_scores` / `discredit_scores` | [`CreditScore` / `DiscreditScore`](/services/api/app/models/credit.py) | One row per Seller — current aggregate, recalculated from non-voided ledger rows on every Verify / Appeal-Overturn |

## Fraud Intelligence (Phase 5 foundation tables)

| Table | Model | Notes |
|---|---|---|
| `risk_scores` | [`RiskScore`](/services/api/app/models/risk.py) | `risk_level` (`low`/`medium`/`high`/`critical`) + `factors` (JSONB) |
| `fraud_patterns` | [`FraudPattern`](/services/api/app/models/pattern.py) | `pattern_definition` (JSONB) |
| `relationships` | [`Relationship`](/services/api/app/models/relationship.py) | Seller-to-seller link with `relationship_type` + `confidence` |
| `ai_analyses` | [`AIAnalysis`](/services/api/app/models/ai_analysis.py) | Generic `target_type`/`target_id` result container so Phase 6 AI features can plug in without schema churn |

## Governance

| Table | Model | Notes |
|---|---|---|
| `disputes` | [`Dispute`](/services/api/app/models/dispute.py) | Seller Appeal against a `VERIFIED` Report; `counter_evidence` (JSONB), `status` (`pending`/`approved`/`rejected`), `resolved_by` + `resolution_notes` for traceability |
| `audit_logs` | [`AuditLog`](/services/api/app/models/audit_log.py) | Append-only `before`/`after` (JSONB) record of every governed change (report review, dispute resolution, duplicate flags) — written by [`audit_service.log_action`](/services/api/app/services/audit_service.py) |

## AI Data

| Table | Model | Notes |
|---|---|---|
| `embeddings` | [`Embedding`](/services/api/app/models/embedding.py) | `pgvector` column (`EMBEDDING_DIMENSION`, default 1536), generic `source_type`/`source_id` |

## Enums

`user_role`, `seller_entity_type`, `report_status`, `report_visibility`,
`evidence_file_type`, `verification_status`, `risk_level`, `dispute_status`
are all native Postgres `ENUM` types (see the migrations for exact values).

`report_status` values: `UNVERIFIED`, `PENDING_REVIEW`, `VERIFIED`,
`REJECTED`, `APPEALED`, `VOIDED`.

## Extensions required

- `vector` (pgvector) — enabled by [`database/init/001_extensions.sql`](/database/init/001_extensions.sql)
- `uuid-ossp` — enabled by the same script (reserved for future server-side UUID generation)
