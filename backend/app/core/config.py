from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "OpenAI Support Intelligence"
    database_url: str | None = Field(
        default=None,
        validation_alias="DATABASE_URL",
    )
    postgres_host: str = Field(default="localhost", validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, validation_alias="POSTGRES_PORT")
    postgres_db: str = Field(default="openaisupport", validation_alias="POSTGRES_DB")
    postgres_user: str = Field(default="openaisupport", validation_alias="POSTGRES_USER")
    postgres_password: str | None = Field(default=None, validation_alias="POSTGRES_PASSWORD")
    postgres_password_file: str | None = Field(default=None, validation_alias="POSTGRES_PASSWORD_FILE")
    gemini_api_key: str | None = Field(default=None, validation_alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-1.5-flash", validation_alias="GEMINI_MODEL")
    embedding_model: str = Field(default="text-embedding-004", validation_alias="EMBEDDING_MODEL")
    github_token: str | None = Field(default=None, validation_alias="GITHUB_TOKEN")

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url:
            return self.database_url

        password = self.postgres_password
        if self.postgres_password_file:
            password = Path(self.postgres_password_file).read_text(encoding="utf-8").strip()

        auth = self.postgres_user
        if password:
            auth = f"{auth}:{password}"

        return (
            f"postgresql+psycopg://{auth}@{self.postgres_host}:"
            f"{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
