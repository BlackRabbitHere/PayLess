import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    app_env: str = "development"
    log_level: str = "INFO"
    scraper_user_agent: str = "PaymentRouteOptimizer/0.1 (+public-offer-collection)"
    http_connect_timeout: float = Field(default=5, gt=0, le=60)
    http_read_timeout: float = Field(default=25, gt=0, le=120)
    max_redirects: int = Field(default=3, ge=0, le=10)
    max_response_bytes: int = Field(default=5_000_000, gt=0)
    max_retries: int = Field(default=0, ge=0, le=2)
    max_retry_wait_seconds: float = Field(default=30, gt=0, le=60)
    default_rate_limit_seconds: float = Field(default=3, ge=0, le=60)
    cache_ttl_seconds: int = Field(default=300, ge=0)
    cache_max_entries: int = Field(default=32, gt=0, le=256)
    robots_cache_seconds: int = Field(default=3600, ge=0)
    save_raw_html: bool = True
    raw_html_retention_days: int = Field(default=7, ge=1)
    snapshot_max_files: int = Field(default=200, ge=1)
    data_dir: Path = Path("data")
    playwright_enabled: bool = True
    provider_yatra_enabled: bool = True
    provider_gyftr_enabled: bool = True
    provider_easemytrip_enabled: bool = True
    browser_selector_timeout_ms: int = Field(default=8000, gt=0, le=30000)
    browser_navigation_timeout_ms: int = Field(default=30000, gt=0)
    browser_max_requests: int = Field(default=40, gt=0, le=100)
    terms_reviewed_providers: str = ""
    fixture_dir: Path | None = None

    @model_validator(mode="after")
    def safe_configuration(self):
        if self.fixture_dir and self.app_env.lower() == "production":
            raise ValueError("Fixture mode cannot be enabled in production.")
        if "\n" in self.scraper_user_agent or "\r" in self.scraper_user_agent:
            raise ValueError("Invalid User-Agent.")
        return self

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv(override=False)
        values = {name: os.environ[name.upper()] for name in cls.model_fields if name.upper() in os.environ}
        if values.get("fixture_dir") == "":
            values.pop("fixture_dir")
        return cls.model_validate(values)
