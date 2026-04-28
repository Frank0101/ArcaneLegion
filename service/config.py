from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    worker_poll_interval: float = 5.0


# Pylance flags this as missing a required argument for database_url, but BaseSettings
# populates fields from environment variables at runtime — no argument needed.
settings = Settings()  # type: ignore[call-arg]
