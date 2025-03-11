from pydantic_settings import BaseSettings


class Config(BaseSettings):
    # Basic app env vars
    APP_NAME: str = "Glad Pharmacy API"
    VERSION: str = "0.0.0"
    DEBUG: bool = False

    # CORS env vars
    ALLOWED_METHODS: list[str] = ["*"]
    ALLOWED_HEADERS: list[str] = ["*"]
    ORIGINS: list[str] = ["http://127.0.0.1:3000", "http://localhost:3000"]
    ALLOW_CREDENTIALS: bool = True


def get_config():
    return Config()
