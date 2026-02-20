# Auth Middleware — Basic Authentication for Prompt Library

import base64
import os
import logging
from fastapi import Depends, HTTPException, status, Request, APIRouter
from fastapi.security import HTTPBasic, HTTPBasicCredentials

logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "odaos2024")

security = HTTPBasic(auto_error=False)


# ============================================================================
# Auth Dependency
# ============================================================================

async def verify_admin(
    credentials: HTTPBasicCredentials = Depends(security),
) -> str:
    """Verify admin credentials via HTTP Basic Auth.
    
    Use as a dependency on protected routes:
        @router.get("/prompts", dependencies=[Depends(verify_admin)])
    
    Returns the username if valid, raises 401 if not.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Basic"},
        )

    if (
        credentials.username != ADMIN_USER
        or credentials.password != ADMIN_PASSWORD
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username


# ============================================================================
# Auth Router — Login endpoint
# ============================================================================

router = APIRouter()


@router.post("/login")
async def login(request: Request):
    """Validate credentials and return auth token for frontend storage.
    
    Expects Authorization: Basic <base64(user:pass)> header.
    Returns { authenticated: true, token: <base64>, username: <str> }
    """
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Basic "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Basic authentication required",
            headers={"WWW-Authenticate": "Basic"},
        )

    try:
        decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
        username, password = decoded.split(":", 1)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
            headers={"WWW-Authenticate": "Basic"},
        )

    if username != ADMIN_USER or password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = base64.b64encode(f"{username}:{password}".encode()).decode()

    return {
        "authenticated": True,
        "token": token,
        "username": username,
    }


@router.get("/verify")
async def verify_token(username: str = Depends(verify_admin)):
    """Verify if a stored token is still valid (frontend session check)."""
    return {"authenticated": True, "username": username}
