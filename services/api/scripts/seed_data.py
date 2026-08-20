"""Seed Data — Phase 2 foundation.

Populates a minimal, idempotent baseline so Phase 3+ development and demos
have something to work against: an admin user, credit/discredit factor
definitions, seller platforms, and one sample seller.

Run inside the api container:
    docker compose exec api python -m scripts.seed_data
"""
from sqlalchemy import select

from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models.credit import CreditFactor, DiscreditFactor
from app.models.seller import Seller, SellerEntityType, SellerPlatform
from app.models.user import User, UserRole


def get_or_create(db, model, defaults: dict | None = None, **filters):
    instance = db.execute(select(model).filter_by(**filters)).scalar_one_or_none()
    if instance is not None:
        return instance, False
    instance = model(**filters, **(defaults or {}))
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance, True


def seed() -> None:
    db = SessionLocal()
    try:
        admin, created = get_or_create(
            db,
            User,
            email="admin@kurutan.dev",
            defaults={
                "full_name": "KuRuTan Admin",
                "hashed_password": hash_password("ChangeMe123!"),
                "role": UserRole.ADMIN,
            },
        )
        print(f"Admin user {'created' if created else 'already exists'}: {admin.email}")

        officer, created = get_or_create(
            db,
            User,
            email="officer@kurutan.dev",
            defaults={
                "full_name": "KuRuTan Officer",
                "hashed_password": hash_password("ChangeMe123!"),
                "role": UserRole.OFFICER,
            },
        )
        print(f"Officer user {'created' if created else 'already exists'}: {officer.email}")

        credit_factors = [
            ("ON_TIME_DELIVERY", "On-time Delivery", 1.0),
            ("ACCURATE_PRODUCT_DESCRIPTION", "Accurate Product Description", 1.0),
            ("POSITIVE_VERIFIED_REVIEW", "Positive Verified Review", 0.5),
        ]
        for code, name, weight in credit_factors:
            _, created = get_or_create(
                db, CreditFactor, code=code, defaults={"name": name, "default_weight": weight}
            )
            print(f"CreditFactor {code} {'created' if created else 'already exists'}")

        discredit_factors = [
            ("NON_DELIVERY", "Non-delivery of Goods", 5.0),
            ("COUNTERFEIT_PRODUCT", "Counterfeit / Fake Product", 4.0),
            ("MISLEADING_DESCRIPTION", "Misleading Product Description", 2.0),
        ]
        for code, name, weight in discredit_factors:
            _, created = get_or_create(
                db,
                DiscreditFactor,
                code=code,
                defaults={"name": name, "default_weight": weight},
            )
            print(f"DiscreditFactor {code} {'created' if created else 'already exists'}")

        platforms = [
            ("FACEBOOK", "Facebook"),
            ("SHOPEE", "Shopee"),
            ("LINE", "Line"),
        ]
        for code, name in platforms:
            _, created = get_or_create(
                db, SellerPlatform, code=code, defaults={"name": name}
            )
            print(f"SellerPlatform {code} {'created' if created else 'already exists'}")

        sample_seller, created = get_or_create(
            db,
            Seller,
            display_name="Sample Demo Shop",
            defaults={
                "entity_type": SellerEntityType.BUSINESS,
                "description": "Seed data sample seller for local development/demo.",
            },
        )
        print(f"Seller 'Sample Demo Shop' {'created' if created else 'already exists'}")

        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
