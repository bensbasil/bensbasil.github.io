from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://admin:adminpassword@localhost:5432/portfolio_db"
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    GEMINI_API_KEY: str = "your-api-key-here"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    PROMETHEUS_PORT: int = 8001
    LOG_LEVEL: str = "INFO"

    # ✅ ADD THESE
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM_NAME: str

    class Config:
        env_file = ".env"


settings = Settings()