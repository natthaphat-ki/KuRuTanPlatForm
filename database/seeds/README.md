# Seed Data

The executable seed script lives at
[`services/api/scripts/seed_data.py`](/services/api/scripts/seed_data.py). It is
idempotent (safe to re-run) and creates:

- An **Admin** (`admin@kurutan.dev`) and **Officer** (`officer@kurutan.dev`)
  account — password for both: `ChangeMe123!` (change before any shared/staging use).
- Baseline `CreditFactor` / `DiscreditFactor` definitions.
- Baseline `SellerPlatform` definitions (Facebook, Shopee, Line).
- One sample `Seller` ("Sample Demo Shop") for local development/demo.

## Run it

```powershell
docker compose exec api python -m scripts.seed_data
```
