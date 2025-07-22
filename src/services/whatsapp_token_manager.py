"""
WhatsApp token management service for handling access token expiration and renewal.
"""
import logging
import httpx
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from config.settings import settings

logger = logging.getLogger(__name__)


class WhatsAppTokenManager:
    """Manages WhatsApp access tokens including validation and renewal."""
    
    def __init__(self):
        self.current_token = settings.whatsapp_access_token
        self.token_expires_at: Optional[datetime] = None
        # Handle case where Facebook credentials might not be configured
        self.app_id = getattr(settings, 'facebook_app_id', '') or None
        self.app_secret = getattr(settings, 'facebook_app_secret', '') or None
        
    async def validate_token(self) -> Dict[str, Any]:
        """Validate the current access token and get its details."""
        try:
            # Use Facebook's debug_token endpoint to check token validity
            url = "https://graph.facebook.com/debug_token"
            params = {
                "input_token": self.current_token,
                "access_token": self.current_token  # Can also use app_token
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    token_data = data.get("data", {})
                    
                    if token_data.get("is_valid", False):
                        # Extract expiration time if available
                        expires_at = token_data.get("expires_at")
                        if expires_at:
                            self.token_expires_at = datetime.fromtimestamp(expires_at)
                        
                        logger.info(f"Token is valid. Expires at: {self.token_expires_at}")
                        return {
                            "valid": True,
                            "expires_at": self.token_expires_at,
                            "scopes": token_data.get("scopes", []),
                            "app_id": token_data.get("app_id"),
                            "user_id": token_data.get("user_id")
                        }
                    else:
                        logger.error("Token is invalid")
                        return {"valid": False, "error": "Token is invalid"}
                else:
                    logger.error(f"Failed to validate token: {response.text}")
                    return {"valid": False, "error": response.text}
                    
        except Exception as e:
            logger.error(f"Error validating token: {e}")
            return {"valid": False, "error": str(e)}
    
    async def is_token_expired(self) -> bool:
        """Check if the current token is expired or will expire soon."""
        if not self.token_expires_at:
            # If we don't know expiration, validate to check
            validation = await self.validate_token()
            if not validation.get("valid", False):
                return True
        
        # Check if token expires within next 30 minutes
        if self.token_expires_at:
            return datetime.now() + timedelta(minutes=30) >= self.token_expires_at
            
        return False
    
    async def get_long_lived_token(self) -> Optional[str]:
        """
        Exchange a short-lived token for a long-lived one.
        Note: This requires app_id and app_secret to be configured.
        """
        if not self.app_id or not self.app_secret:
            logger.warning("App ID and App Secret not configured for token renewal")
            return None
            
        try:
            url = "https://graph.facebook.com/oauth/access_token"
            params = {
                "grant_type": "fb_exchange_token",
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "fb_exchange_token": self.current_token
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    new_token = data.get("access_token")
                    expires_in = data.get("expires_in")
                    
                    if new_token:
                        self.current_token = new_token
                        if expires_in:
                            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                        
                        logger.info(f"Successfully renewed token. New expiration: {self.token_expires_at}")
                        return new_token
                else:
                    logger.error(f"Failed to renew token: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error renewing token: {e}")
            return None
    
    async def ensure_valid_token(self) -> str:
        """Ensure we have a valid token, refreshing if necessary."""
        # Check if current token is expired
        if await self.is_token_expired():
            logger.warning("Token is expired or expiring soon, attempting renewal...")
            
            # Try to get a long-lived token
            new_token = await self.get_long_lived_token()
            if new_token:
                return new_token
            else:
                logger.error("Failed to renew token automatically")
                raise Exception("WhatsApp access token expired and could not be renewed")
        
        return self.current_token
    
    def get_token_status(self) -> Dict[str, Any]:
        """Get current token status for monitoring."""
        return {
            "has_token": bool(self.current_token),
            "expires_at": self.token_expires_at.isoformat() if self.token_expires_at else None,
            "is_expired": self.token_expires_at and datetime.now() >= self.token_expires_at if self.token_expires_at else False,
            "expires_soon": self.token_expires_at and datetime.now() + timedelta(hours=1) >= self.token_expires_at if self.token_expires_at else False
        }


# Global token manager instance
token_manager = WhatsAppTokenManager()
