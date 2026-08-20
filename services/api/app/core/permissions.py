"""Role-Based Authorization Foundation.

Defines the canonical roles from the Domain (Phase 1):
Public / User / Admin / Officer, and a reusable FastAPI dependency
factory to guard routes by role.
"""
from enum import Enum
from typing import Iterable

from fastapi import Depends, HTTPException, status

from app.core.deps import get_current_user
from app.models.user import User


class Role(str, Enum):
    PUBLIC = "public"
    USER = "user"
    ADMIN = "admin"
    OFFICER = "officer"


def require_roles(*allowed_roles: Iterable[Role]):
    """Dependency factory: raise 403 unless current_user.role is allowed.

    Usage: `current_user: User = Depends(require_roles(Role.ADMIN, Role.OFFICER))`
    """

    allowed = {r.value if isinstance(r, Role) else r for r in allowed_roles}

    def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return current_user

    return _checker


def effective_role(user: User | None) -> Role:
    """The role to enforce for a request: the user's role if logged in, or
    Public for an anonymous/unauthenticated visitor.
    """
    if user is None:
        return Role.PUBLIC
    return Role(user.role.value)
