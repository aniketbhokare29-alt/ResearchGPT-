from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "ResearchGPT"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    frontend_origin: str = "http://localhost:5173"
    database_url: str = "postgresql+psycopg://researchgpt:researchgpt@localhost:5432/researchgpt"
    jwt_secret_key: str = ""
    access_token_minutes: int = Field(default=60, ge=5, le=1440)
    max_pdf_size_mb: int = Field(default=25, gt=0, le=100)
    upload_directory: Path = REPOSITORY_ROOT / "data" / "uploads"
    vector_index_directory: Path = REPOSITORY_ROOT / "data" / "indexes"
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    summary_model_name: str = "sshleifer/distilbart-cnn-12-6"
    model_device: str = "auto"
    embedding_batch_size: int = Field(default=24, ge=1, le=128)
    chunk_size_words: int = Field(default=140, ge=40, le=1000)
    chunk_overlap_words: int = Field(default=28, ge=0, le=500)
    summary_max_input_tokens: int = Field(default=850, ge=128, le=2048)
    summary_max_output_tokens: int = Field(default=120, ge=40, le=512)

    @property
    def frontend_origins(self) -> list[str]:
        """Allow the usual loopback aliases without opening CORS to other hosts."""
        parts = urlsplit(self.frontend_origin)
        origins = {self.frontend_origin.rstrip("/")}
        if parts.hostname == "localhost":
            netloc = parts.netloc.replace("localhost", "127.0.0.1", 1)
            origins.add(urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment)).rstrip("/"))
        elif parts.hostname == "127.0.0.1":
            netloc = parts.netloc.replace("127.0.0.1", "localhost", 1)
            origins.add(urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment)).rstrip("/"))
        return sorted(origins)

    model_config = SettingsConfigDict(env_file=REPOSITORY_ROOT / ".env", extra="ignore")


settings = Settings()

