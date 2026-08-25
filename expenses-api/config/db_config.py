from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = ""
    ALEMBIC_URL: str = ""

    AUTH_JWKS_URI: str = ""
    AUTH_ISSUER: str = ""
    AUTH_AUDIENCE: str = "expenses-api"
    AUTH_REQUIRED: bool = True

    DEBUG: bool = False


app_settings = AppSettings()
