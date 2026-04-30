import asyncio
import random

class MockLLMService:
    def __init__(self):
        self.dummy_response = (
            "I'm currently running in offline dummy mode because the power is out. "
            "I can't access Ollama right now, but your FastAPI structure is working perfectly!"
        )

    async def chat_stream(self):
        """Simulates a model generating text word by word."""
        words = self.dummy_response.split(" ")
        
        for word in words:
            await asyncio.sleep(random.uniform(0.05, 0.15))
            yield word + " "