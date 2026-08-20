"""Import every model so Alembic autogenerate + Base.metadata see all tables."""
from app.database.base import Base  # noqa: F401
from app.models.user import User, UserRole  # noqa: F401
from app.models.seller import Seller, SellerAccount, SellerPlatform, SellerEntityType  # noqa: F401
from app.models.report import Report, ReportStatus, ReportVisibility  # noqa: F401
from app.models.evidence import (  # noqa: F401
    Evidence,
    EvidenceFileType,
    Verification,
    VerificationStatus,
)
from app.models.credit import (  # noqa: F401
    CreditFactor,
    DiscreditFactor,
    CreditLedger,
    DiscreditLedger,
    CreditScore,
    DiscreditScore,
)
from app.models.risk import RiskScore, RiskLevel  # noqa: F401
from app.models.pattern import FraudPattern  # noqa: F401
from app.models.relationship import Relationship  # noqa: F401
from app.models.ai_analysis import AIAnalysis  # noqa: F401
from app.models.dispute import Dispute, DisputeStatus  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.embedding import Embedding  # noqa: F401

__all__ = [
    "Base",
    "User",
    "UserRole",
    "Seller",
    "SellerAccount",
    "SellerPlatform",
    "SellerEntityType",
    "Report",
    "ReportStatus",
    "ReportVisibility",
    "Evidence",
    "EvidenceFileType",
    "Verification",
    "VerificationStatus",
    "CreditFactor",
    "DiscreditFactor",
    "CreditLedger",
    "DiscreditLedger",
    "CreditScore",
    "DiscreditScore",
    "RiskScore",
    "RiskLevel",
    "FraudPattern",
    "Relationship",
    "AIAnalysis",
    "Dispute",
    "DisputeStatus",
    "AuditLog",
    "Embedding",
]
