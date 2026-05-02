from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Clinic Scheduling Chatbot"
    Electricity_Off: bool = False
    OLLAMA_MODEL: str = "command-r7b-arabic:latest"
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "clinic_bot"
    GEMINI_MODEL_NAME: str = "gemini-2.5-flash-lite"
    MODEL_PROVIDER: str = "Ollama"
    GEMINI_API_KEY: str 

    class Config:
        env_file = ".env"

settings = Settings()