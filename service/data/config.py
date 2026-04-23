from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str


# Pylance flags this as missing a required argument for database_url, but BaseSettings
# populates fields from environment variables at runtime — no argument needed.
settings = Settings()  # type: ignore[call-arg]
