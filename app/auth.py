"""
Optional JWT authentication with JWKS support.

This module provides flexible authentication that can be:
- Completely disabled (default)
- Enabled with Supabase JWKS
- Extended for other JWT providers

Usage:
    # Optional auth (returns None if disabled)
    user = Depends(get_current_user_optional)
    
    # Required auth (raises 401 if disabled or invalid)
    user = Depends(require_auth)
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from jwcrypto import jwk, jwt as jwcrypto_jwt
from jwcrypto.jwk import JWKSet
import requests

from app.config import get_settings

logger = logging.getLogger(__name__)

# Security scheme (only used if auth is enabled)
security = HTTPBearer(auto_error=False)


class JWTAuthenticator:
    """JWT authenticator with JWKS support."""

    def __init__(self):
        self.jwks: Optional[dict] = None
        settings = get_settings()
        self.enabled = settings.auth_enabled

        if self.enabled and settings.jwks_url:
            try:
                # Fetch JWKS keys
                response = requests.get(settings.jwks_url, timeout=10)
                response.raise_for_status()
                self.jwks = response.json()
                logger.info(f"JWT authentication enabled with JWKS URL: {settings.jwks_url}")
            except Exception as e:
                logger.error(f"Failed to fetch JWKS: {e}")
                self.enabled = False
        elif self.enabled:
            logger.warning("AUTH_ENABLED is true but JWKS_URL is not set. Authentication disabled.")
            self.enabled = False
        else:
            logger.info("JWT authentication is disabled")

    def decode_token(self, token: str) -> dict:
        """Decode and validate JWT token."""
        if not self.enabled or not self.jwks:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication not configured",
            )

        try:
            # Get the unverified header to extract the key ID (kid)
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            # Find the matching key from JWKS
            key = None
            for jwk_key in self.jwks.get("keys", []):
                if jwk_key.get("kid") == kid:
                    key = jwk_key
                    break

            if not key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: Signing key not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Decode and validate token
            settings = get_settings()
            payload = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=settings.jwt_audience,
                options={"verify_exp": True},
            )

            return payload

        except JWTError as e:
            if "expired" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
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
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
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
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
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
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
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
