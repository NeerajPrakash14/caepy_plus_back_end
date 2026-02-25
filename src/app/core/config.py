"""Application Configuration Module.

Implements 12-factor app configuration using pydantic-settings.
All configuration is loaded from environment variables with sensible defaults.

Environment file loading priority:
1. If APP_ENV is set, loads .env.{APP_ENV} (e.g., .env.dev, .env.prod)
2. Falls back to .env if specific file doesn't exist
3. Environment variables always override file values
"""
import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _get_env_file() -> str | tuple[str, ...]:
    """
    Determine which .env file(s) to load based on APP_ENV.
    
    Priority (later files override earlier):
    1. .env (base defaults)
    2. .env.{APP_ENV} (environment-specific overrides)
    
    Returns:
        Tuple of env file paths to load (in order of priority)
    """
    # Get APP_ENV from environment (not from file yet)
    app_env = os.getenv("APP_ENV", "").lower()

    # Map environment values to file suffixes
    env_to_file = {
        "dev": "dev",
        "development": "dev",
        "prod": "prod",
        "production": "prod",
        "staging": "staging",
        "test": "test",
    }

    file_suffix = env_to_file.get(app_env, app_env)

    # Build list of env files (order: base first, then specific - later overrides earlier)
    env_files: list[str] = []

    # Base .env first (lowest priority)
    if Path(".env").exists():
        env_files.append(".env")

    # Environment-specific file second (overrides base)
    if file_suffix:
        env_specific = f".env.{file_suffix}"
        if Path(env_specific).exists():
            env_files.append(env_specific)

    # Return tuple for pydantic-settings
    if env_files:
        return tuple(env_files)
    return ".env"  # Default even if doesn't exist

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Follows the 12-factor app methodology for configuration management.
    All settings can be overridden via environment variables.
    
    Environment file loading:
    - Set APP_ENV=dev to load .env.dev
    - Set APP_ENV=prod to load .env.prod
    - Falls back to .env if specific file doesn't exist
    """

    model_config = SettingsConfigDict(
        env_file=_get_env_file(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ========================================
    # Application Settings
    # ========================================
    APP_NAME: str = Field(
        default="doctor-onboarding-service",
        description="Application name used in logging and metrics"
    )
    APP_VERSION: str = Field(
        default="2.0.0",
        description="Semantic version of the application"
    )
    APP_ENV: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Deployment environment"
    )
    DEBUG: bool = Field(
        default=False,
        description="Enable debug mode (never enable in production)"
    )

    # ========================================
    # Server Configuration
    # ========================================
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, ge=1, le=65535, description="Server port")
    WORKERS: int = Field(default=1, ge=1, description="Number of worker processes")
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )

    # ========================================
    # Database Configuration (PostgreSQL)
    # ========================================

    DATABASE_URL: str = Field(
        default="",
        description="PostgreSQL database connection URL (SQLAlchemy asyncpg format). Required in production."
    )

    DATABASE_POOL_SIZE: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Database connection pool size"
    )
    DATABASE_MAX_OVERFLOW: int = Field(
        default=10,
        ge=0,
        description="Max overflow connections beyond pool size"
    )
    DATABASE_POOL_TIMEOUT: int = Field(
        default=30,
        ge=1,
        description="Timeout for getting connection from pool (seconds)"
    )
    DATABASE_ECHO: bool = Field(
        default=False,
        description="Echo SQL statements to logs"
    )

    # ========================================
    # Google Gemini AI Configuration
    # ========================================

    GOOGLE_API_KEY: str = Field(
        default="",
        description="Google AI Studio API key for Gemini"
    )
    GEMINI_MODEL: str = Field(
        default="gemini-2.5-flash",
        description="Gemini model to use for AI operations"
    )
    GEMINI_MAX_RETRIES: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts for Gemini API calls"
    )
    GEMINI_RETRY_DELAY: float = Field(
        default=1.0,
        ge=0.1,
        description="Initial delay between retries (seconds)"
    )
    GEMINI_TIMEOUT: int = Field(
        default=60,
        ge=5,
        description="Timeout for Gemini API requests (seconds)"
    )
    GEMINI_TEMPERATURE: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Temperature for AI generation (lower = more deterministic)"
    )
    GEMINI_MAX_TOKENS: int = Field(
        default=4096,
        ge=100,
        description="Maximum tokens in AI response"
    )

    # ========================================
    # Security Configuration
    # ========================================
    SECRET_KEY: str = Field(
        default="change-me-in-production-use-strong-random-key",
        min_length=32,
        description="Secret key for JWT signing"
    )
    ALGORITHM: str = Field(
        default="HS256",
        description="JWT signing algorithm"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        ge=1,
        description="JWT access token expiration time (minutes)"
    )

    # ========================================
    # CORS Configuration
    # ========================================
    CORS_ORIGINS: str = Field(
        default="*",
        description="Comma-separated list of allowed CORS origins"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(
        default=True,
        description="Allow credentials in CORS requests"
    )
    CORS_ALLOW_METHODS: str = Field(
        default="GET,POST,PUT,DELETE,OPTIONS,PATCH",
        description="Comma-separated list of allowed HTTP methods"
    )
    CORS_ALLOW_HEADERS: str = Field(
        default="*",
        description="Comma-separated list of allowed headers"
    )

    # ========================================
    # File Upload Settings
    # ========================================
    MAX_FILE_SIZE_MB: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum upload file size in MB"
    )
    ALLOWED_EXTENSIONS: str = Field(
        default="pdf,png,jpg,jpeg",
        description="Comma-separated list of allowed file extensions"
    )

    # ========================================
    # Rate Limiting
    # ========================================
    RATE_LIMIT_REQUESTS: int = Field(
        default=100,
        ge=1,
        description="Maximum requests per window"
    )
    RATE_LIMIT_WINDOW_SECONDS: int = Field(
        default=60,
        ge=1,
        description="Rate limit window in seconds"
    )


    # ========================================
    # Blob Storage Configuration
    # ========================================
    STORAGE_BACKEND: Literal["local", "s3"] = Field(
        default="local",
        description="Storage backend to use: 'local' for filesystem, 's3' for AWS S3"
    )

    # Local Storage Settings
    BLOB_STORAGE_PATH: str = Field(
        default="./blob_storage",
        description="Local filesystem path for blob storage"
    )
    BLOB_BASE_URL: str = Field(
        default="/api/v1/blobs",
        description="Base URL for serving blobs (local storage)"
    )

    # AWS S3 Settings
    AWS_ACCESS_KEY_ID: str = Field(
        default="",
        description="AWS access key ID for S3"
    )
    AWS_SECRET_ACCESS_KEY: str = Field(
        default="",
        description="AWS secret access key for S3"
    )
    AWS_REGION: str = Field(
        default="us-east-1",
        description="AWS region for S3 bucket"
    )
    AWS_S3_BUCKET: str = Field(
        default="",
        description="S3 bucket name for blob storage"
    )
    AWS_S3_PREFIX: str = Field(
        default="doctors",
        description="Prefix for S3 object keys (e.g., 'doctors' -> doctors/123/photo.jpg)"
    )
    AWS_S3_USE_SIGNED_URLS: bool = Field(
        default=False,
        description="Use signed URLs for S3 objects (True) or public URLs (False)"
    )
    AWS_S3_SIGNED_URL_EXPIRY: int = Field(
        default=3600,
        ge=60,
        le=604800,
        description="Signed URL expiry time in seconds (default 1 hour)"
    )
    # ========================================
    # LinQMD Integration Configuration
    # ========================================
    LINQMD_API_URL: str = Field(
        default="https://dev.linqmd.com/api/user/create",
        description="LinQMD API endpoint for user creation"
    )
    LINQMD_AUTH_TOKEN: str = Field(
        default="",
        description="LinQMD API Basic Auth token (required for LinQMD sync)"
    )
    LINQMD_COOKIE: str = Field(
        default="",
        description="LinQMD API session cookie (required for LinQMD sync)"
    )

    LINQMD_SYNC_ENABLED: bool = Field(
        default=False,
        description="Enable automatic sync to LinQMD after onboarding"
    )
    LINQMD_DEFAULT_PASSWORD: str = Field(
        default="",
        description="Default password for new LinQMD users (should be changed by user)"
    )
    LINQMD_API_TIMEOUT: int = Field(
        default=30,
        ge=5,
        le=120,
        description="Timeout for LinQMD API requests (seconds)"
    )

    # ========================================
    # SMS/OTP Configuration (onlysms.co.in)
    # ========================================

    SMS_API_BASE_URL: str = Field(
        default="https://onlysms.co.in/api/otp.aspx",
        description="SMS API base URL"
    )
    SMS_USER_ID: str = Field(
        default="",
        description="SMS API user ID (required for SMS functionality)"
    )
    SMS_USER_PASS: str = Field(
        default="",
        description="SMS API user password (required for SMS functionality)"
    )
    SMS_GSM_ID: str = Field(
        default="linQMD",
        description="SMS sender ID (GSM ID)"
    )
    SMS_PE_ID: str = Field(
        default="1701171921100574462",
        description="SMS Principal Entity ID (DLT registered)"
    )
    SMS_TEMPLATE_ID: str = Field(
        default="1707172361651556820",
        description="SMS Template ID (DLT registered)"
    )

    SMS_OTP_MESSAGE_TEMPLATE: str = Field(
        default=(
            "Hi! OTP for booking an appointment with LinQMD is: {otp}. "
            "Please do not share it with anyone. linQMD."
        ),
        description=(
            "SMS OTP message template. Must match DLT registered template "
            "exactly. Use {otp} as placeholder for the OTP value."
        ),
    )

    # OTP Settings
    OTP_LENGTH: int = Field(
        default=6,
        ge=4,
        le=8,
        description="Length of generated OTP"
    )
    OTP_EXPIRY_SECONDS: int = Field(
        default=300,
        ge=60,
        le=600,
        description="OTP validity period in seconds (default 5 minutes)"
    )
    OTP_MAX_ATTEMPTS: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Maximum OTP verification attempts before expiry"
    )


    # ========================================
    # Redis Configuration (for OTP storage)
    # ========================================
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL (format: redis://[:password@]host:port/db)"
    )
    REDIS_OTP_PREFIX: str = Field(
        default="otp:",
        description="Key prefix for OTP storage in Redis"
    )
    REDIS_ENABLED: bool = Field(
        default=True,
        description="Enable Redis for OTP storage (fallback to in-memory if False or unavailable)"
    )


    # Computed Properties
    # ========================================
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def cors_methods_list(self) -> list[str]:
        """Parse CORS methods from comma-separated string."""
        return [method.strip() for method in self.CORS_ALLOW_METHODS.split(",")]

    @property
    def allowed_extensions_list(self) -> list[str]:
        """Parse allowed file extensions from comma-separated string."""
        return [ext.strip().lower() for ext in self.ALLOWED_EXTENSIONS.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        """Convert MB to bytes."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.APP_ENV == "development"

    @property
    def env_file_loaded(self) -> str:
        """Return which env file(s) were loaded."""
        env_file = _get_env_file()
        if isinstance(env_file, tuple):
            return ", ".join(env_file)
        return env_file


    # ========================================
    # Validators
    # ========================================
    @field_validator("GOOGLE_API_KEY")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Warn if API key is not set."""
        if not v:
            import warnings
            warnings.warn(
                "GOOGLE_API_KEY is not set. AI features will not work.",
                UserWarning,
                stacklevel=2
            )
        return v


    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Warn if DATABASE_URL is not set."""
        if not v:
            import warnings
            warnings.warn(
                "DATABASE_URL is not set. Using default for development.",
                UserWarning,
                stacklevel=2
            )
            # Return a development default
            return "postgresql+asyncpg://linqdev:linqdev123@localhost:5432/doctor_onboarding"
        return v

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Validate settings for production environment."""
        if self.is_production:
            if self.DEBUG:
                raise ValueError("DEBUG must be False in production")
            if "change-me" in self.SECRET_KEY.lower():
                raise ValueError("SECRET_KEY must be changed in production")
            if not self.GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY is required in production")
            if not self.DATABASE_URL or "localhost" in self.DATABASE_URL:
                raise ValueError("DATABASE_URL must be set to a production database")
            # Validate SMS credentials for OTP functionality
            if not self.SMS_USER_ID or not self.SMS_USER_PASS:
                raise ValueError("SMS_USER_ID and SMS_USER_PASS are required in production for OTP functionality")
        return self

@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to ensure settings are only loaded once.
    This is the recommended way to access settings throughout the application.
    
    Returns:
        Settings instance loaded from environment
    """
    return Settings()

# Convenience alias for direct import
settings = get_settings()
