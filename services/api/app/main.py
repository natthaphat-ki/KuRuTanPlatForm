from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import (
    admin,
    auth,
    credits,
    discredits,
    disputes,
    evidence,
    patterns,
    relationships,
    reports,
    risk,
    sellers,
)

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "KuRuTan V2 — Credit / Discredit Digital Trust & Fraud Intelligence. "
        "Phase 2: Database & Backend Foundation."
    ),
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT}


api_v1 = settings.API_V1_PREFIX
app.include_router(auth.router, prefix=api_v1)
app.include_router(sellers.router, prefix=api_v1)
app.include_router(reports.router, prefix=api_v1)
app.include_router(evidence.router, prefix=api_v1)
app.include_router(credits.router, prefix=api_v1)
app.include_router(discredits.router, prefix=api_v1)
app.include_router(risk.router, prefix=api_v1)
app.include_router(patterns.router, prefix=api_v1)
app.include_router(relationships.router, prefix=api_v1)
app.include_router(disputes.router, prefix=api_v1)
app.include_router(admin.router, prefix=api_v1)
