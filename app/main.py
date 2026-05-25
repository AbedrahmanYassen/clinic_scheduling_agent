from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.v1 import chat
from app.core.config import settings
from app.services.llm_not_agent_services import NotAgentLLMService
from app.services.mock_llm_service import MockLLMService
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.middleware.sessions import SessionMiddleware
from app.services.llm_service import LLMService
from fastapi.middleware.cors import CORSMiddleware
import certifi


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.mongodb_client = AsyncIOMotorClient(
        settings.MONGODB_URL, tlsCAFile=certifi.where()
    )
    app.mongodb = app.mongodb_client[settings.DATABASE_NAME]
    print("Connected to MongoDB!")
    try:
        if settings.Electricity_Off:
            print("⚡ Running in DUMMY MODE (Offline)")
            app.state.llm_service = MockLLMService()
        else:
            print(f"🤖 Connecting to AI model from ({settings.MODEL_PROVIDER})")
            app.state.llm_service = LLMService()
    except Exception as e:
        print("Error initializing LLM service:", e)
    yield
    del app.state.llm_service
    app.mongodb_client.close()


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
    max_age=3600,
    same_site="lax",
    https_only=True,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specify your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/v1")
