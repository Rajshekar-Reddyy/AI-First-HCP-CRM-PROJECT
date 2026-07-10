from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(default="mysql+pymysql://crm_user:crm_password@localhost:3306/hcp_crm")
    groq_api_key: str = Field(default="")
    groq_model: str = Field(default="gemma2-9b-it")
    groq_temperature: float = Field(default=0.2)
    groq_max_tokens: int = Field(default=1200)
    backend_cors_origins: str = Field(default="http://localhost:5173,http://127.0.0.1:5173")
    log_level: str = Field(default="INFO")
    create_tables_on_startup: bool = Field(default=False)

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
