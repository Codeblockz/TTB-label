from pathlib import Path

from pydantic_settings import BaseSettings

# Resolve .env from project root (two levels up from this file: app/config.py -> backend -> project root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    azure_vision_key: str = ""
    azure_vision_endpoint: str = ""
    azure_openai_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_deployment: str = "gpt-4o-mini"
    azure_openai_api_version: str = "2024-12-01-preview"
    database_url: str = "sqlite+aiosqlite:///./labelcheck.db"
    upload_dir: str = "./uploads"
    use_mock_services: bool = True
    log_level: str = "info"

    model_config = {"env_file": str(_ENV_FILE), "env_file_encoding": "utf-8"}


settings = Settings()
