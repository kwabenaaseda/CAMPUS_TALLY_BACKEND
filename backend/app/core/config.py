from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "Campus Tally"

    # If the variable name matches the .env key, you only need Field(...)
    POSTGRES_USERNAME: str = Field(default="") 
    POSTGRES_PASSWORD: str = Field(default="")
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_DB: str = Field(default="")
    
    SECRET_KEY: str = Field(default="")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    DATABASE_URL: str = Field(default="")
    
    # Error in your original code: ADMIN_USERNAME: str = Field(..., env="")
    ADMIN_USERNAME: str = Field(default="")
    ADMIN_PASSWORD: str = Field(default="")
    ADMIN_ID_CODE: str = Field(default="")
    ENVIRONMENT: str = Field(default="development")  # "development" or "production"

    # In v2, it is recommended to use SettingsConfigDict
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore" # Good practice: ignore extra env vars
    )

settings = Settings()