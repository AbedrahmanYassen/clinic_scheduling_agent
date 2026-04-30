from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.v1 import chat
from app.core.config import settings
from app.services.ollama_services import OllamaService
from app.services.mock_llm_service import MockLLMService
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.middleware.sessions import SessionMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.mongodb_client = AsyncIOMotorClient(settings.MONGODB_URL)
    app.mongodb = app.mongodb_client[settings.DATABASE_NAME]
    print("Connected to MongoDB!")
    if settings.Electricity_Off:
        print("⚡ Running in DUMMY MODE (Offline)")
        app.state.llm_service = MockLLMService()
    else:
        print(f"🤖 Connecting to Ollama ({settings.OLLAMA_MODEL})")
        app.state.llm_service = OllamaService()
    
    yield
    del app.state.llm_service
    app.mongodb_client.close()

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key="SuperSecretKeyLearningFastAPI",  
    max_age=3600,                             
    same_site="lax",                          
    https_only=True                         
)

app.include_router(chat.router, prefix="/api/v1")