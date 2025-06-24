"""
Application configuration settings.
"""
import os
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, validator, MongoDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    class Config:
        extra = 'allow'  # Allow extra fields to be set on the model
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = True
    
    # Application Settings
    PROJECT_NAME: str = "BizFindr"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-me-in-production")
    
    # Flask Settings
    FLASK_APP: str = os.getenv("FLASK_APP", "app")
    FLASK_ENV: str = os.getenv("FLASK_ENV", "development")
    
    # MongoDB Settings
    MONGO_HOST: str = os.getenv("MONGO_HOST", "mongo")
    MONGO_PORT: int = int(os.getenv("MONGO_PORT", "27017"))
    MONGO_USER: Optional[str] = os.getenv("MONGO_USER")
    MONGO_PASSWORD: Optional[str] = os.getenv("MONGO_PASSWORD")
    MONGO_DB: str = os.getenv("MONGO_DB", "bizfindr")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "bizfindr")
    MONGO_AUTH_SOURCE: Optional[str] = os.getenv("MONGO_AUTH_SOURCE")
    MONGO_URI: Optional[MongoDsn] = None
    
    # Redis Settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    REDIS_CACHE_TTL: int = int(os.getenv("REDIS_CACHE_TTL", "300"))
    
    # Background task settings will go here in the future
    
    # Flower Settings
    FLOWER_BASIC_AUTH: str = os.getenv("FLOWER_BASIC_AUTH", "admin:admin")
    
    # Frontend Settings
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Logging
    LOG_FILE: str = os.getenv("LOG_FILE", "/var/log/bizfindr/app.log")
    
    # Support
    SUPPORT_EMAIL: str = os.getenv("SUPPORT_EMAIL", "support@bizfindr.example.com")
    
    # API
    API_BASE_URL: str = os.getenv("API_BASE_URL", "https://data.ct.gov/resource/n7gp-d28j.json")
    
    # Cache
    CACHE_TYPE: str = os.getenv("CACHE_TYPE", "RedisCache")
    CACHE_REDIS_URL: str = os.getenv("CACHE_REDIS_URL", "redis://redis:6379/0")
    CACHE_DEFAULT_TIMEOUT: int = int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300"))
    
    # CORS Settings
    BACKEND_CORS_ORIGINS: List[Union[str, AnyHttpUrl]] = ["*"]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # MongoDB Settings
    MONGO_HOST: str = os.getenv("MONGO_HOST", "localhost")
    MONGO_PORT: int = int(os.getenv("MONGO_PORT", "27017"))
    MONGO_USER: Optional[str] = os.getenv("MONGO_USER")
    MONGO_PASSWORD: Optional[str] = os.getenv("MONGO_PASSWORD")
    MONGO_DB: str = os.getenv("MONGO_DB", "bizfindr")
    MONGO_AUTH_SOURCE: Optional[str] = os.getenv("MONGO_AUTH_SOURCE")
    MONGO_URI: Optional[MongoDsn] = None
    
    @validator("MONGO_URI", pre=True)
    def assemble_mongo_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        
        # If MONGO_URI is not provided, construct it from components
        user_pass = ""
        if values.get("MONGO_USER") and values.get("MONGO_PASSWORD"):
            user_pass = f"{values['MONGO_USER']}:{values['MONGO_PASSWORD']}@"
        
        auth_source = ""
        if values.get("MONGO_AUTH_SOURCE"):
            auth_source = f"?authSource={values['MONGO_AUTH_SOURCE']}"
        
        return f"mongodb://{user_pass}{values['MONGO_HOST']}:{values['MONGO_PORT']}/{values['MONGO_DB']}{auth_source}"
    
    # Redis Settings
    MONGO_HOST: str = os.getenv("MONGO_HOST", "mongo")
    MONGO_PORT: int = int(os.getenv("MONGO_PORT", "27017"))
    MONGO_USER: str = os.getenv("MONGO_USER", "")
    MONGO_PASSWORD: str = os.getenv("MONGO_PASSWORD", "")
    MONGO_DB: str = os.getenv("MONGO_DB", "bizfindr")
    MONGO_AUTH_SOURCE: str = os.getenv("MONGO_AUTH_SOURCE", "admin")
    MONGO_URI: Optional[str] = os.getenv("MONGO_URI")
    
    # Construct MongoDB URI if not provided directly
    @validator("MONGO_URI", pre=True)
    def assemble_mongo_connection(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        if isinstance(v, str):
            return v
        
        # Build connection string from components
        if values.get("MONGO_USER") and values.get("MONGO_PASSWORD"):
            return f"mongodb://{values.get('MONGO_USER')}:{values.get('MONGO_PASSWORD')}@{values.get('MONGO_HOST')}:{values.get('MONGO_PORT')}/{values.get('MONGO_DB')}?authSource={values.get('MONGO_AUTH_SOURCE')}"
        return f"mongodb://{values.get('MONGO_HOST')}:{values.get('MONGO_PORT')}/{values.get('MONGO_DB')}"
    
    # Additional MongoDB settings
    MONGO_MAX_POOL_SIZE: int = int(os.getenv("MONGO_MAX_POOL_SIZE", "100"))
    MONGO_MIN_POOL_SIZE: int = int(os.getenv("MONGO_MIN_POOL_SIZE", "10"))
    MONGO_MAX_IDLE_TIME_MS: int = int(os.getenv("MONGO_MAX_IDLE_TIME_MS", "30000"))
    MONGO_SERVER_SELECTION_TIMEOUT_MS: int = int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "5000"))
    MONGO_SOCKET_TIMEOUT_MS: int = int(os.getenv("MONGO_SOCKET_TIMEOUT_MS", "30000"))
    MONGO_CONNECT_TIMEOUT_MS: int = int(os.getenv("MONGO_CONNECT_TIMEOUT_MS", "10000"))
    MONGO_RETRY_WRITES: bool = os.getenv("MONGO_RETRY_WRITES", "true").lower() == "true"
    MONGO_RETRY_READS: bool = os.getenv("MONGO_RETRY_READS", "true").lower() == "true"
    
    # Redis Settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    REDIS_CACHE_TTL: int = int(os.getenv("REDIS_CACHE_TTL", "300"))  # 5 minutes default
    
    # API Settings
    API_PREFIX: str = "/api"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Security
    SECURITY_BCRYPT_ROUNDS: int = 12
    SECURITY_PASSWORD_SALT: str = os.getenv("SECURITY_PASSWORD_SALT", "dev-salt-change-me")
    
    # JWT Settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-change-me")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Rate Limiting
    RATE_LIMIT_DEFAULT: str = "1000 per day"
    RATE_LIMIT_STORAGE_URL: str = REDIS_URL
    
    # Caching
    CACHE_DEFAULT_TIMEOUT: int = 300  # 5 minutes
    CACHE_KEY_PREFIX: str = "bizfindr_"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # External Services
    CT_API_KEY: str = os.getenv("CT_API_KEY", "")
    CT_API_BASE_URL: str = os.getenv("CT_API_BASE_URL", "https://api.ct.gov/CTBTT/")
    
    # Scheduler Settings
    SCHEDULER_API_ENABLED: bool = False
    
    # CORS Settings
    CORS_ORIGINS: List[str] = ["*"]
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


# Create settings instance
settings = Settings()
