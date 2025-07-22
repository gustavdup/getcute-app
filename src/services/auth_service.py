"""
Authentication service for SSO and portal access.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
import jwt
from src.config.settings import settings
from src.models.database import User

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication and SSO token generation."""
    
    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = "HS256"
        self.token_expire_hours = 24
    
    def generate_portal_token(self, user: User, redirect_path: str = "/") -> str:
        """Generate a JWT token for portal access."""
        try:
            if not user.id:
                raise ValueError("User ID is required")
            
            # Create payload
            payload = {
                "user_id": str(user.id),
                "phone_number": user.phone_number,
                "redirect_path": redirect_path,
                "exp": datetime.now(timezone.utc) + timedelta(hours=self.token_expire_hours),
                "iat": datetime.now(timezone.utc),
                "type": "portal_access"
            }
            
            # Generate token
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            logger.info(f"Generated portal token for user {user.id}")
            return token
            
        except Exception as e:
            logger.error(f"Error generating portal token: {e}")
            raise
    
    def verify_portal_token(self, token: str) -> Optional[dict]:
        """Verify and decode a portal access token."""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            
            # Check token type
            if payload.get("type") != "portal_access":
                logger.warning("Invalid token type")
                return None
            
            logger.info(f"Verified portal token for user {payload.get('user_id')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Portal token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid portal token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying portal token: {e}")
            return None
    
    def create_portal_url(self, user: User, base_url: str, path: str = "/") -> str:
        """Create an authenticated portal URL."""
        try:
            token = self.generate_portal_token(user, path)
            return f"{base_url.rstrip('/')}/portal{path}?token={token}"
            
        except Exception as e:
            logger.error(f"Error creating portal URL: {e}")
            raise
    
    def refresh_token(self, token: str) -> Optional[str]:
        """Refresh an existing token if it's valid and not expired."""
        try:
            payload = self.verify_portal_token(token)
            if not payload:
                return None
            
            # Create new token with same data but fresh expiration
            user_data = {
                "id": payload["user_id"],
                "phone_number": payload["phone_number"]
            }
            
            # Create a mock user object for token generation
            user = User(**user_data)
            return self.generate_portal_token(user, payload.get("redirect_path", "/"))
            
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return None
