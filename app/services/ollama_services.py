from langchain_core import messages
from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from typing import List
from app.schemas.chat import ChatMessage, ChatRequest
from app.core.prompts import prompt
from app.core.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI

class OllamaService:
    def __init__(self):
        if settings.MODEL_PROVIDER == "Ollama":
            self.llm = ChatOllama(
                model=settings.OLLAMA_MODEL,
                temperature=0.8,
                validate_model_on_init=True 
            )
        elif settings.MODEL_PROVIDER == "Gemini":
                self.llm = ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL_NAME,
                temperature=0.7,
                max_tokens=None,
                timeout=None,
                max_retries=2,
                api_key=settings.GEMINI_API_KEY
            )
        else:
            raise ValueError(f"Unsupported MODEL_PROVIDER: {settings.MODEL_PROVIDER}")

    async def chat_stream(self, messages: List[ChatMessage] = [] , session_id: str = None, db_service=None):
        """Streams the response token by token."""
        current_history = await db_service.get_history(session_id)
        history = "\n".join([f"{m['role']}: {m['content']}" for m in current_history])

        user_input = messages[-1].content

        final_prompt = prompt.format_messages(
        chat_history=current_history,
        input=user_input
        )        


        
        async for chunk in self.llm.astream(final_prompt):
            yield chunk.content





