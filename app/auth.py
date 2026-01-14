"""
Optional JWT authentication with JWKS support.

This module provides flexible authentication that can be:
- Completely disabled (default)
- Enabled with Supabase JWKS
- Extended for other JWT providers

Usage:
    # Optional auth (returns None if disabled)
    user = Depends(get_current_user)
    
    # Required auth (raises 401 if disabled or invalid)
    user = Depends(require_auth)
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.security.utils import get_authorization_scheme_param
from starlette.requests import Request
from jose import JWTError, jwt
from jwt import PyJWKClient

from app.config import get_settings

logger = logging.getLogger(__name__)

# Security scheme (only used if auth is enabled)
security = HTTPBearer(auto_error=False)


class JWTAuthenticator:
    """JWT authenticator with JWKS support for Supabase and other providers."""

    def __init__(self):
        self.jwks_client: Optional[PyJWKClient] = None
        settings = get_settings()
        self.enabled = settings.auth_enabled

        if self.enabled and settings.jwks_url:
            try:
                # Initialize PyJWKClient for JWKS
                self.jwks_client = PyJWKClient(settings.jwks_url)
                logger.info(f"JWT authentication enabled with JWKS URL: {settings.jwks_url}")
            except Exception as e:
                logger.error(f"Failed to initialize JWKS client: {e}")
                self.enabled = False
        elif self.enabled:
            logger.warning("AUTH_ENABLED is true but JWKS_URL is not set. Authentication disabled.")
            self.enabled = False
        else:
            logger.info("JWT authentication is disabled")

    def decode_token(self, token: str) -> dict:
        """Decode and validate JWT token using JWKS."""
        if not self.enabled or not self.jwks_client:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication not configured",
            )

        settings = get_settings()

        try:
            # Get the signing key from JWKS
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)

            # Decode and validate token with RS256
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "ES256"],
                audience=settings.jwt_audience,
                issuer=settings.jwt_issuer,
                options={"verify_exp": True},
            )

            return payload

        except JWTError as e:
            error_msg = str(e).lower()
            if "expired" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            elif "audience" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token audience",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )


# Global authenticator instance
authenticator = JWTAuthenticator()


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """
    Get current user from JWT token (optional).
    
    Returns:
        User payload if auth is enabled and token is valid
        None if auth is disabled or no token provided
    
    Does not raise errors - suitable for optional authentication.
    """
    if not authenticator.enabled:
        return None

    if not credentials:
        return None

    try:
        token = credentials.credentials
        payload = authenticator.decode_token(token)
        return payload
    except HTTPException:
        # Don't raise for optional auth
        return None


async def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """
    Require valid JWT authentication.
    
    Returns:
        User payload from validated token
    
    Raises:
        HTTPException 401 if auth is disabled, no token, or invalid token
    """
    if not authenticator.enabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is not enabled on this server",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = authenticator.decode_token(token)
    return payload


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """
    Get current user (enforces auth if enabled, allows anonymous if disabled).
    
    This is the recommended dependency for most routes:
    - If auth is enabled: requires valid token (raises 401 if missing/invalid)
    - If auth is disabled: always returns None (no authentication required)
    
    Returns:
        User payload if authenticated, None if auth disabled
    """
    if not authenticator.enabled:
        return None

    # If auth is enabled, require valid credentials
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = authenticator.decode_token(token)
    return payload
