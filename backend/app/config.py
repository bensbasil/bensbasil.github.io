from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://admin:adminpassword@localhost:5432/portfolio_db"
    MILVUS_DB_PATH: str = "./chroma_db"
    GEMINI_API_KEY: str = "your-api-key-here"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # LLM Provider settings
    LLM_PROVIDER: str = "gemini" # options: gemini, ollama, huggingface
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    HF_API_KEY: Optional[str] = None
    HF_MODEL: str = "mistralai/Mistral-7B-Instruct-v0.2"

    PROMETHEUS_PORT: int = 8001
    LOG_LEVEL: str = "INFO"

    # Mail settings
    MAIL_USERNAME: Optional[str] = None
    MAIL_PASSWORD: Optional[str] = None
    MAIL_FROM: Optional[str] = None
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_FROM_NAME: str = "Portfolio Contact Form"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()