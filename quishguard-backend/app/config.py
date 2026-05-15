from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-me-in-production"

    # Database
    DATABASE_URL: str = "sqlite:///./quishguard.db"

    # Google / Gmail
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/callback"
    # Path to downloaded credentials.json from Google Cloud Console
    GMAIL_CREDENTIALS_FILE: str = "credentials.json"
    # Path where token.json is stored after first OAuth flow
    GMAIL_TOKEN_FILE: str = "token.json"

    # VirusTotal
    VIRUSTOTAL_API_KEY: str = ""

    # OpenAI (used by CrewAI)
    OPENAI_API_KEY: str = ""

    # Sandbox
    # Max seconds Playwright waits for a page to load
    SANDBOX_TIMEOUT_MS: int = 10000
    # Directory where screenshots are saved
    SCREENSHOT_DIR: str = "./screenshots"

    # Threat scoring thresholds
    RISK_SCORE_BLOCK_THRESHOLD: int = 70  # auto-block above this score

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()