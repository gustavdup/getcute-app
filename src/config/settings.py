"""
Application settings and environment configuration.
"""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application Configuration
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    environment: str = Field(default="production", description="Environment (local/production)")
    secret_key: str = Field(default="dev-secret-key-change-in-production", description="Secret key for JWT tokens")
    api_host: str = Field(default="localhost", description="API host")
    api_port: int = Field(default=8000, description="API port")
    webhook_url: str = Field(default="http://localhost:8000/webhook", description="Public webhook URL")
    
    # Supabase Configuration
    supabase_url: str = Field(default="", description="Supabase project URL")
    supabase_key: str = Field(default="", description="Supabase anon key")
    supabase_service_key: str = Field(default="", description="Supabase service role key")
    
    # OpenAI Configuration
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o-mini", description="Default OpenAI model to use")
    openai_model_vtt: str = Field(default="whisper-1", description="OpenAI model for voice transcription")
    openai_model_image_recognition: str = Field(default="gpt-4o", description="OpenAI model for image recognition")
    
    # WhatsApp Business API
    whatsapp_access_token: str = Field(default="", description="WhatsApp access token")
    whatsapp_phone_number_id: str = Field(default="", description="WhatsApp phone number ID")
    whatsapp_webhook_verify_token: str = Field(default="dev-verify-token", description="WhatsApp webhook verify token")
    
    # Facebook App Credentials (for token renewal)
    facebook_app_id: str = Field(default="", description="Facebook App ID")
    facebook_app_secret: str = Field(default="", description="Facebook App Secret")
    
    # Admin Panel
    admin_username: str = Field(default="admin", description="Admin panel username")
    admin_password: str = Field(default="admin123", description="Admin panel password")
    
    # Session Configuration
    brain_dump_timeout_minutes: int = Field(default=3, description="Brain dump session timeout")
    tag_response_timeout_minutes: int = Field(default=2, description="Tag response timeout")
    
    # Vector Search Configuration
    vector_dimensions: int = Field(default=1536, description="Vector embedding dimensions")
    search_results_limit: int = Field(default=10, description="Maximum search results")
    
    # Media Configuration
    max_file_size_mb: int = Field(default=10, description="Maximum file size in MB")
    supported_image_formats: str = Field(
        default="jpg,jpeg,png,gif,webp", 
        description="Supported image formats"
    )
    supported_audio_formats: str = Field(
        default="mp3,wav,ogg,m4a", 
        description="Supported audio formats"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @property
    def image_formats_list(self) -> list[str]:
        """Get supported image formats as a list."""
        return [fmt.strip() for fmt in self.supported_image_formats.split(",")]
    
    @property
    def audio_formats_list(self) -> list[str]:
        """Get supported audio formats as a list."""
        return [fmt.strip() for fmt in self.supported_audio_formats.split(",")]


# Global settings instance
settings = Settings()
