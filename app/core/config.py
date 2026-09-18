from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ENT AI Assistant"
    environment: str = "development"

    lm_base_url: str = "http://localhost:1234/v1"
    lm_api_key: str = "lm-studio"
    lm_model: str = "your-local-model"

    chroma_dir: str = "./data/chroma"
    documents_dir: str = "./data/documents"
    top_k: int = 4

    ent_api_mode: str = "mock"
    ent_api_url: str = "http://localhost:8000/api"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
