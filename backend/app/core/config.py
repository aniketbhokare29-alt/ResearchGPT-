from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "ResearchGPT"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    frontend_origin: str = "http://localhost:5173"
    database_url: str = "postgresql+psycopg://researchgpt:researchgpt@localhost:5432/researchgpt"

    model_config = SettingsConfigDict(env_file=REPOSITORY_ROOT / ".env", extra="ignore")


settings = Settings()

