"""
Application configuration using Pydantic Settings.
Follows Guardrail #6: Configuration Management (12-Factor App)
All config loaded from environment variables, zero hardcoded secrets.
"""

import os
from typing import List
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Defaults are provided for development, but production values
    should be set via environment variables or .env file.
    """

    # Application
    app_name: str = Field(default="SkyNet", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    environment: str = Field(default="development", description="Environment (development/staging/production)")
    debug: bool = Field(default=True, description="Debug mode")

    # API
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")

    # Database - Supabase PostgreSQL
    # Supabase provides a direct PostgreSQL connection URL
    database_url: str = Field(
        default="",
        description="Supabase PostgreSQL connection URL"
    )

    # Supabase additional settings (optional, for future features like Auth, Storage, Realtime)
    supabase_url: str = Field(default="", description="Supabase project URL")
    supabase_publishable_key: str = Field(default="", description="Supabase publishable/anon key")

    @property
    def get_database_url(self) -> str:
        """
        Get PostgreSQL URL from environment.

        Works with both Supabase and Railway deployments.
        Supabase provides DATABASE_URL directly in .env
        Railway will use the same DATABASE_URL environment variable
        """
        database_url = os.getenv("DATABASE_URL") or self.database_url

        if database_url:
            print(f"[CONFIG] Using Supabase PostgreSQL database")
            return database_url

        # Should not reach here if .env is configured properly
        raise ValueError("DATABASE_URL not configured. Please check your .env file.")

    # OpenAI API
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model_synthesis: str = Field(
        default="gpt-4-turbo-preview",
        description="OpenAI model for synthesis"
    )
    openai_model_extraction: str = Field(
        default="gpt-4-mini",
        description="OpenAI model for extraction"
    )

    # Transcription
    whisper_model: str = Field(default="whisper-1", description="Whisper model for transcription")
    soniox_api_key: str = Field(default="", description="Soniox API key (optional)")

    # Email (SMTP)
    smtp_host: str = Field(default="smtp.gmail.com", description="SMTP host")
    smtp_port: int = Field(default=587, description="SMTP port")
    smtp_user: str = Field(default="", description="SMTP username")
    smtp_password: str = Field(default="", description="SMTP password")
    smtp_from_email: str = Field(default="noreply@skynet.ai", description="From email address")
    smtp_from_name: str = Field(default="SkyNet", description="From name")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json/text)")

    # Security
    secret_key: str = Field(
        default="dev_secret_key_change_in_production_min_32_chars",
        description="Secret key for JWT/sessions"
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration in minutes"
    )

    # CORS
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        description="Allowed CORS origins (comma-separated)"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore extra fields in .env
    )

    @validator("environment")
    def validate_environment(cls, v):
        """Ensure environment is one of the allowed values."""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v

    @validator("secret_key")
    def validate_secret_key(cls, v, values):
        """Ensure secret key is strong enough in production."""
        environment = values.get("environment", "development")
        if environment == "production" and len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters in production")
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"


# Global settings instance
# This is the single source of truth for configuration
settings = Settings()
