"""
backend/app/core/security.py
Coursewright — Authentication & Authorization

Provides four things to the rest of the backend:
    1. get_password_hash(password)          → str
    2. verify_password(plain, hashed)       → bool
    3. create_access_token(subject, delta)  → JWT string
    4. get_current_user                     → FastAPI dependency → User ORM object
    5. require_role(*roles)                 → FastAPI dependency factory → User ORM object

Usage examples:

    # Hash a password before storing:
    from app.core.security import get_password_hash
    user.hashed_password = get_password_hash(plain_password)

    # Verify a login attempt:
    from app.core.security import verify_password
    if not verify_password(plain, user.hashed_password):
        raise HTTPException(401)

    # Issue a token after successful login:
    from app.core.security import create_access_token
    token = create_access_token(subject=str(user.id))

    # Protect any endpoint — returns the authenticated User:
    from app.core.security import get_current_user
    @router.get("/me")
    def read_me(current_user=Depends(get_current_user)):
        return current_user

    # Protect an admin-only endpoint:
    from app.core.security import require_role
    @router.get("/admin/reviews")
    def list_reviews(current_user=Depends(require_role("admin", "reviewer"))):
        return ...
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db   # backend teammate's file

# ---------------------------------------------------------------------------
# PASSWORD HASHING
# CryptContext manages the hashing algorithm and its settings.
# schemes=["bcrypt"]: use bcrypt — the standard for password storage.
#     bcrypt is intentionally slow and includes a random salt automatically.
#     Never use MD5 or plain SHA for passwords.
# deprecated="auto": if a password was hashed with an older/weaker scheme,
#     passlib will flag it so it can be re-hashed on next login.
# ---------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------------------------
# TOKEN EXTRACTION
# OAuth2PasswordBearer does two things:
#   1. Tells FastAPI: "extract the Bearer token from the Authorization header"
#   2. Marks every route that uses get_current_user as requiring authentication
#      in the OpenAPI schema — the /docs Swagger UI shows the Authorize button.
# tokenUrl: the endpoint the frontend calls to get a token (login route).
#   This must match the route your backend teammate builds in auth.py.
# ---------------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ---------------------------------------------------------------------------
# PASSWORD UTILITIES
# ---------------------------------------------------------------------------

def get_password_hash(password: str) -> str:
    """
    Hash a plain-text password using bcrypt.
    Call this before storing a new user's password in the database.
    The returned string includes the salt and cost factor — store it as-is.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check a login attempt.
    Returns True if the plain password matches the stored hash.
    Returns False if it does not match.
    Never compare plain passwords directly — always use this function.
    """
    return pwd_context.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# JWT TOKEN CREATION
# ---------------------------------------------------------------------------

def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        subject:      The user's ID as a string. Stored as the JWT 'sub' claim.
                      Must be a string — the JWT spec requires 'sub' to be a string.
        expires_delta: How long the token is valid. Defaults to
                      ACCESS_TOKEN_EXPIRE_MINUTES from settings (60 min).

    Returns:
        A signed JWT string. Send this to the client in the login response.
        The client sends it back in every request as:
            Authorization: Bearer <token>
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    # timezone.utc makes the datetime timezone-aware.
    # Without it, JWT expiry comparisons can silently fail in production.

    payload = {
        "sub": subject,   # 'sub' (subject) is the standard JWT claim for user identity
        "exp": expire,    # 'exp' (expiry) tells python-jose when to reject the token
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,    # signs the token — keep this secret
        algorithm=settings.ALGORITHM,  # HS256: symmetric signing (one key for sign + verify)
    )


# ---------------------------------------------------------------------------
# FASTAPI DEPENDENCY: get_current_user
# ---------------------------------------------------------------------------

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    FastAPI dependency. Validates the Bearer token and returns the User object.

    What it does, in order:
        1. oauth2_scheme extracts the token from the Authorization header.
        2. jwt.decode() verifies the signature and checks expiry.
        3. We extract the user ID from the 'sub' claim.
        4. We query the database for that user.
        5. We check that the user is active (not banned/deleted).
        6. We return the full User ORM object to the route handler.

    If any step fails, we raise HTTP 401 Unauthorized.
    We always return the same generic error message — never tell the caller
    whether the token was invalid vs the user doesn't exist vs the user is banned.
    (Specific error messages help attackers probe the system.)

    Usage:
        @router.get("/roadmap")
        def get_roadmap(current_user=Depends(get_current_user)):
            return current_user.roadmap
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
        # WWW-Authenticate header is required by the OAuth2 spec
        # when returning 401. It tells the client the auth scheme to use.
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            # algorithms takes a list — python-jose rejects tokens signed
            # with any algorithm not in this list. This prevents algorithm
            # confusion attacks (e.g. someone sending a 'none' algorithm token).
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        user_id = UUID(user_id)


    except JWTError:
        # Catches: expired tokens, invalid signatures, malformed tokens
        raise credentials_exception

    # Import User here, NOT at the top of this file.
    # Reason: models/user.py may import from core/security.py.
    # Importing at the top would create a circular import and crash startup.
    # Importing inside the function body is safe — by the time this function
    # runs, all modules are fully loaded.
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        # A JWT token remains cryptographically valid for its full lifetime
        # even if an admin deactivates the user account.
        # This check ensures deactivated users are rejected on every request.
        raise credentials_exception

    return user


# ---------------------------------------------------------------------------
# FASTAPI DEPENDENCY FACTORY: require_role
# ---------------------------------------------------------------------------

def require_role(*allowed_roles: str):
    """
    Factory that returns a FastAPI dependency enforcing role-based access.
    Used to protect admin and reviewer endpoints.

    How it works:
        require_role("admin") returns a function called 'checker'.
        FastAPI calls checker on each request.
        checker itself depends on get_current_user, so:
            request → get_current_user (401 if no valid token)
                     → checker (403 if wrong role)
                     → route handler (runs with the verified user)

    Usage:

        # Only admins:
        @router.post("/admin/reviews/{id}/approve")
        def approve(id: str, current_user=Depends(require_role("admin"))):
            ...

        # Admins OR reviewers:
        @router.get("/admin/reviews")
        def list_reviews(current_user=Depends(require_role("admin", "reviewer"))):
            ...

    Args:
        *allowed_roles: One or more role strings. The user must have ANY ONE
                        of these roles to pass. (OR logic, not AND.)

    Returns:
        The authenticated User ORM object if the role check passes.
        HTTP 403 Forbidden if the user's role is not in allowed_roles.
        HTTP 401 Unauthorized if the token is invalid (from get_current_user).
    """
    def checker(current_user=Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {' or '.join(allowed_roles)}",
            )
        return current_user

    return checker