# app/services/llm_service.py

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from app.core.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI


class LLMService:
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

    async def classify_intent(self, message: str) -> str:
        prompt = [
            SystemMessage(content="Classify intent: book, cancel, reschedule, question, info"),
            HumanMessage(content=message)
        ]

        res = await self.llm.ainvoke(prompt)
        return res.content.strip().lower()

    async def extract_entities(self, message: str) -> dict:
        system_prompt = '''
        Extract the following information from the user message.

        Return ONLY valid JSON.

        Fields:
        - name
        - date
        - time
        - doctor
        - service

        Message:
        {text}

        Expected output:
        {{
            "name": "...",
            "date": "...",
            "time": "...",
            "doctor": "...",
            "service": "..."
        }}
        '''
        prompt = [
            SystemMessage(content=system_prompt.format(text=message)),
            HumanMessage(content=message)
        ]

        res = await self.llm.ainvoke(prompt)
        return res.content  

    async def generate_response(self, context: str) -> str:
        res = await self.llm.ainvoke([HumanMessage(content=context)])
        return res.content