from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Haven"
    Electricity_Off: bool = False
    OLLAMA_MODEL: str = "command-r7b-arabic:latest"
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "clinic_bot"
    GEMINI_MODEL_NAME: str = "gemini-2.5-flash-lite"
    MODEL_PROVIDER: str = "Ollama"  # or "Gemini"
    GEMINI_API_KEY: str 
    LANGFUSE_SECRET_KEY: str
    LANGFUSE_PUBLIC_KEY: str
    LANGFUSE_BASE_URL: str
    TIME_ZONE: str = "Asia/Jerusalem"

    class Config:
        env_file = ".env"
settings = Settings()