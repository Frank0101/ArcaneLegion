from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    github_token: str | None = None
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    worker_poll_interval: float = 5.0
    workspace_base_path: str = ".workspaces"


# Pylance flags this as missing a required argument for database_url, but BaseSettings
# populates fields from environment variables at runtime — no argument needed.
settings = Settings()  # type: ignore[call-arg]
