"""Runtime configuration.

Values come from environment variables so the same image runs unchanged under
Docker Compose, raw Kubernetes manifests and the Helm chart:

* ``DATABASE_URL`` wins if it is set (used by tests and local runs).
* Otherwise the URL is assembled from ``DB_HOST``/``DB_PORT``/``DB_NAME`` (non-secret,
  from a ConfigMap) and ``DB_USER``/``DB_PASSWORD`` (from a Secret).
"""

from functools import cached_property
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "ClinicDesk API"
    app_version: str = "1.0.0"
    environment: str = "local"
    clinic_timezone: str = "Asia/Kolkata"
    log_level: str = "INFO"
    cors_origins: str = "*"

    database_url: str | None = None
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "clinicdesk"
    db_user: str = "clinicdesk"
    db_password: str = ""

    @cached_property
    def sqlalchemy_url(self) -> str:
        if self.database_url:
            return self.database_url
        user = quote_plus(self.db_user)
        password = quote_plus(self.db_password)
        return f"postgresql+psycopg://{user}:{password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
