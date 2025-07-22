"""
Database connection and configuration for Supabase.
"""
import logging
from typing import Optional
from supabase import create_client, Client
from config.settings import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages Supabase database connections and operations."""
    
    def __init__(self):
        self._client: Optional[Client] = None
        self._admin_client: Optional[Client] = None
    
    @property
    def client(self) -> Client:
        """Get the standard Supabase client (anon key)."""
        if self._client is None:
            self._client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
            logger.info("Supabase client initialized")
        return self._client
    
    @property
    def admin_client(self) -> Client:
        """Get the admin Supabase client (service role key)."""
        if self._admin_client is None:
            self._admin_client = create_client(
                settings.supabase_url,
                settings.supabase_service_key
            )
            logger.info("Supabase admin client initialized")
        return self._admin_client
    
    async def health_check(self) -> bool:
        """Check if database connection is healthy."""
        try:
            # Simple query to test connection
            result = self.client.table("users").select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def setup_database(self):
        """Setup database schema and extensions if needed."""
        try:
            # Enable pgvector extension
            self.admin_client.rpc('enable_pgvector').execute()
            logger.info("Database setup completed")
        except Exception as e:
            logger.warning(f"Database setup warning: {e}")


# Global database manager instance
db_manager = DatabaseManager()

# Convenience functions
def get_db_client() -> Client:
    """Get the standard database client."""
    return db_manager.client

def get_admin_client() -> Client:
    """Get the admin database client."""
    return db_manager.admin_client
