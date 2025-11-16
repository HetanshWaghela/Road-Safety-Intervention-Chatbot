"""Application configuration."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from typing import List, Optional, Any
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings."""

    # API Settings
    app_name: str = "Road Safety Intervention API"
    app_version: str = "1.0.0"
    api_prefix: str = "/api/v1"

    # Google Gemini API
    gemini_api_key: Optional[str] = None
    gemini_flash_model: str = "gemini-1.5-flash"
    gemini_pro_model: str = "gemini-1.5-pro"
    gemini_embedding_model: str = "text-embedding-004"

    # Authentication
    api_keys: Optional[str] = None  # Comma-separated API keys

    # Environment
    environment: str = "development"
    log_level: str = "info"

    # Caching
    enable_cache: bool = True
    cache_ttl: int = 3600  # 1 hour

    # Database
    database_url: str = "sqlite:///./data/processed/interventions.db"

    # Vector Store
    chroma_persist_dir: str = "./data/chroma_db"
    collection_name: str = "road_safety_interventions"

    # Search Settings
    default_search_strategy: str = "hybrid"
    max_results: int = 5
    rag_top_k: int = 10

    # Server
    port: int = 8000
    host: str = "0.0.0.0"

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent / ".env"),
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields in .env file
    )
    
    @model_validator(mode='before')
    @classmethod
    def set_defaults(cls, data: Any) -> Any:
        """Set defaults for optional fields if they're missing."""
        if isinstance(data, dict):
            if 'gemini_api_key' not in data:
                data['gemini_api_key'] = None
            if 'api_keys' not in data:
                data['api_keys'] = None
        return data

    @property
    def api_keys_list(self) -> List[str]:
        """Parse API keys from comma-separated string."""
        if not self.api_keys:
            return []
        return [key.strip() for key in self.api_keys.split(",") if key.strip()]
    
    def validate_required_settings(self) -> None:
        """Validate that required settings are present."""
        errors = []
        if not self.gemini_api_key:
            errors.append("GEMINI_API_KEY environment variable is required")
        if not self.api_keys:
            errors.append("API_KEYS environment variable is required (comma-separated list)")
        
        if errors:
            error_msg = "Missing required environment variables:\n" + "\n".join(f"  - {e}" for e in errors)
            error_msg += "\n\nPlease set these in your environment or .env file."
            raise ValueError(error_msg)

    @property
    def project_root(self) -> Path:
        """Get project root directory."""
        return Path(__file__).parent.parent.parent

    @property
    def data_dir(self) -> Path:
        """Get data directory."""
        # In Docker/deployment, data is in ./data relative to app
        # In local dev, it's in project_root/backend/data
        if Path("./data").exists():
            return Path("./data")
        return self.project_root / "backend" / "data"

    @property
    def raw_data_dir(self) -> Path:
        """Get raw data directory."""
        return self.data_dir / "raw"

    @property
    def processed_data_dir(self) -> Path:
        """Get processed data directory."""
        return self.data_dir / "processed"

    @property
    def chroma_dir(self) -> Path:
        """Get ChromaDB directory."""
        # Use data_dir which already handles Docker vs local paths
        return self.data_dir / "chroma_db"


# Global settings instance
settings = Settings()
