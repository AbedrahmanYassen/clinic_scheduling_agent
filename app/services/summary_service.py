from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from app.core.config import settings

class SummaryService:
    def __init__(self,):
        self.llm = ChatOllama(model=settings.OLLAMA_MODEL, temperature=0.8, validate_model_on_init=True)

    async def summarize_history(self, history_text: str) -> str:
        prompt = f"""
        Summarize the following chat conversation between a medical clinic chatbot and a patient. 
        Focus on symptoms, appointment details, and patient needs. 
        Keep it concise (under 100 words).
        
        CONVERSATION:
        {history_text}
        
        SUMMARY:"""
        
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        return response.content