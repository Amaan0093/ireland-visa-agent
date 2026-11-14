from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Ireland Visa Agent"
    environment: str = "local"
    
    database_url: str = "postgresql://visa:visa@localhost:5432/visa"
    ollama_host: str = "http://localhost:11434"
    embed_model: str = "nomic-embed-text"
    embed_dim: int = 768

settings = Settings()
