from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="FRAUD_",
        env_file=".env",
        extra="forbid",
    )

    model_path: Path = Field(
        Path("models/fraud_xgb_v3.joblib"),
        description="Path to the joblib model bundle",
    )
    block_threshold: float = Field(
        0.85,
        ge=0.5,
        le=0.99,
    )
    log_level: str = "INFO"
    git_sha: str = "dev"
    registry_token: SecretStr | None = None

    @field_validator("model_path")
    @classmethod
    def model_file_must_exist(cls, value: Path) -> Path:
        if not value.exists():
            raise ValueError(f"artefact not found: {value}")
        return value
