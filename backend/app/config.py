from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    summarization_model: str = "sshleifer/distilbart-cnn-12-6"

    chunk_size: int = 1000
    chunk_overlap: int = 150
    top_k: int = 5

    data_dir: str = "../data"

    @property
    def data_path(self) -> Path:
        p = Path(self.data_dir).resolve()
        (p / "uploads").mkdir(parents=True, exist_ok=True)
        (p / "index").mkdir(parents=True, exist_ok=True)
        return p

    @property
    def uploads_path(self) -> Path:
        return self.data_path / "uploads"

    @property
    def index_path(self) -> Path:
        return self.data_path / "index"

    @property
    def db_url(self) -> str:
        return f"sqlite:///{self.data_path / 'studymate.db'}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
