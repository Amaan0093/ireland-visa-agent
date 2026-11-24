from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Ireland Visa Agent"
    environment: str = "local"
    
    database_url: str = "postgresql://visa:visa@localhost:5432/visa"
    ollama_host: str = "http://localhost:11434"
    embed_model: str = "nomic-embed-text"
    embed_dim: int = 768

    chat_model: str = "llama3.1:8b"
    retrieval_k: int = 5
    judge_model: str = "qwen2.5:7b"

settings = Settings()
