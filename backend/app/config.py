import os

from pydantic_settings import BaseSettings

# Resolve the .env file – look in backend/ first, then the project root
_this_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
_root_dir = os.path.dirname(_this_dir)  # project root
_env_file = os.path.join(_this_dir, ".env") if os.path.exists(os.path.join(_this_dir, ".env")) else os.path.join(_root_dir, ".env")


class Settings(BaseSettings):
    # MongoDB
    MONGODB_URL: str

    # API Keys
    OPENAI_API_KEY: str = ""
    COMTRADE_PRIMARY_KEY: str = ""
    COMTRADE_SECONDARY_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440

    # App
    APP_LANGUAGE: str = "fr"
    LOG_LEVEL: str = "INFO"

    # Scheduler
    SCHEDULER_ENABLED: bool = True
    SCHEDULER_DAILY_HOUR: int = 2       # 02:00 UTC daily
    SCHEDULER_DAILY_MINUTE: int = 0

    # Mail API
    MAIL_API_URL: str = "https://aic-mail-server.vercel.app/api/send-email"
    MAIL_API_FALLBACK_URL: str = "https://mail-api-mounsef.vercel.app/api/send-email"

    # External API base URLs
    EUROSTAT_COMEXT_BASE_URL: str = "https://ec.europa.eu/eurostat/api/comext/dissemination"
    COMTRADE_BASE_URL: str = "https://comtradeapi.un.org/data/v1/get"
    FEDERAL_REGISTER_BASE_URL: str = "https://www.federalregister.gov/api/v1"

    class Config:
        env_file = _env_file
        extra = "ignore"


settings = Settings()
