from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from app.core.config import settings

class SummaryService:
    def __init__(self,):
        self.llm = ChatOpenAI(
                    base_url="https://api.fanar.qa/v1",
                    api_key=settings.Fanar_API_KEY,
                    model="Fanar",
                )

    async def summarize_history(self, history_text: str) -> str:
        prompt = f"""
You are a medical appointment conversation summarizer.

Your task is to summarize ONLY the information explicitly mentioned in the conversation.

Rules:
- Do NOT invent, assume, infer, or hallucinate information.
- If information is missing, do not create it.
- If the conversation is empty or contains no useful information, return exactly:
"No summary available."

Extract only:
- Patient name
- Symptoms
- Doctor/service requested
- User intent or need

Keep the summary:
- factual
- concise
- under 80 words
- based strictly on the conversation

Conversation:
{history_text}

Output format example:
Name: John Doe | Symptoms: Fever, cough | Appointment: 2026-05-10 10:00 AM | Need: Book appointment with dentist

If a field is missing, omit it completely.

Summary:
"""
        
        response = await self.llm.ainvoke([SystemMessage(content=prompt)])
        return response.content