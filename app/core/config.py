from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Haven"
    Electricity_Off: bool = False
    OLLAMA_MODEL: str = "command-r7b-arabic:latest"
    MONGODB_URL: str 
    DATABASE_NAME: str 
    GEMINI_MODEL_NAME: str = "gemini-2.5-flash-lite"
    MODEL_PROVIDER: str = "Fanar"  # or "Gemini"
    GEMINI_API_KEY: str 
    LANGFUSE_SECRET_KEY: str
    LANGFUSE_PUBLIC_KEY: str
    LANGFUSE_BASE_URL: str
    TIME_ZONE: str = "Asia/Gaza"
    Fanar_API_KEY: str
    SESSION_SECRET_KEY: str = "default-secret-change-in-production"


    class Config:
        env_file = ".env"
settings = Settings()