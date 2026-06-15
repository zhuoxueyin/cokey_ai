from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional


class Settings(BaseSettings):
    app_name: str = "AIGC创作平台"
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "aigc_platform"

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    secret_key: str = "your-secret-key-change-in-production"
    encryption_key: str = "your-encryption-key-32bytes-min"

    github_token: str = ""
    github_username: str = ""
    github_repo: str = ""
    github_branch: str = "main"

    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    rate_limit_requests_per_minute: int = 60
    rate_limit_window_seconds: int = 60

    task_timeout_seconds: int = 300
    task_retry_max: int = 3
    task_retry_delay: int = 5

    poll_interval: int = 1000

    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.cors_origins, str):
            if self.cors_origins.startswith("[") and self.cors_origins.endswith("]"):
                try:
                    import json
                    return json.loads(self.cors_origins)
                except Exception:
                    pass
            return [item.strip() for item in self.cors_origins.split(",") if item.strip()]
        return list(self.cors_origins) if isinstance(self.cors_origins, list) else []

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


settings = Settings()
