# app/services/llm_service.py

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from app.core.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langfuse import Langfuse, get_client
from langfuse.langchain import CallbackHandler
from langchain_core.prompts import ChatPromptTemplate

class LLMService:
    def __init__(self):
        
        Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_BASE_URL  # Optional: defaults to https://cloud.langfuse.com
        )

        self.langfuse = get_client()

        self.langfuse_handler = CallbackHandler()



        if not settings.Electricity_Off:
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
        else : 
            self.llm = None  
        self.langfuse.flush()


    async def classify_intent(self, message: str) -> str:
        prompt = [
            SystemMessage(content='''
أنت مصنف نوايا لمساعد حجز مواعيد في عيادة.

مهمتك هي قراءة رسالة المستخدم باللغة العربية وإرجاع كلمة واحدة فقط من القائمة التالية:

- book
- cancel
- reschedule
- question
- info

التصنيفات:
- book → إذا كان المستخدم يريد حجز موعد جديد.
- cancel → إذا كان المستخدم يريد إلغاء موعد.
- reschedule → إذا كان المستخدم يريد تغيير أو تأجيل أو إعادة جدولة موعد.
- question → إذا كان المستخدم يسأل سؤالاً عاماً.
- info → إذا كان المستخدم يرسل معلومات فقط مثل الاسم أو التاريخ أو الوقت بدون طلب واضح.

قواعد مهمة:
- أرجع كلمة واحدة فقط.
- لا تشرح.
- لا تضف علامات ترقيم.
- إذا لم يكن الطلب واضحاً اعتبره question.

أمثلة:

المستخدم: أريد حجز موعد
book

المستخدم: لو سمحت ألغِ موعدي
cancel

المستخدم: بدي أغير موعدي للساعة 5
reschedule

المستخدم: ما هي ساعات الدوام؟
question

المستخدم: اسمي أحمد وموعدي الثلاثاء
info

الرسالة:
{text}
'''.format(text=message)),               
            HumanMessage(content=message)
        ]
        res = await self.llm.ainvoke(
            prompt,
            config={"callbacks": [self.langfuse_handler]}
        )
        # res = await self.llm.ainvoke(prompt, callbacks=[self.langfuse_handler])
        return res.content.strip().lower()

    async def extract_entities(self, message: str) -> dict:
        system_prompt = '''
Extract structured appointment information from the user message.

Return ONLY valid JSON. Do not include any explanation or text outside JSON.

-----------------------
FIELDS
-----------------------
- name: string or null
- service: string or null

- date: MUST be in ISO format YYYY-MM-DD (e.g., 2026-05-10)
- time: MUST be in 24-hour format HH:MM (e.g., 14:30)

-----------------------
NORMALIZATION RULES
-----------------------

- If date or time is missing or unclear, return null

- If multiple options are mentioned, choose the most likely one

-----------------------
IMPORTANT
-----------------------
- Do NOT return natural language dates like "tomorrow"
- Do NOT return "3pm" — always convert to HH:MM
- Do NOT guess missing information

-----------------------
MESSAGE:
{text}

-----------------------
OUTPUT FORMAT:
{{
    "name": "...",
    "date": "YYYY-MM-DD or null",
    "time": "HH:MM or null",
    "service": "..."
}}
'''
        prompt = [
            SystemMessage(content=system_prompt.format(text=message)),
            HumanMessage(content=message)
        ]
        res = await self.llm.ainvoke(
        prompt,
        config={"callbacks": [self.langfuse_handler]}
        )

        # res = await self.llm.ainvoke(prompt, callbacks=[self.langfuse_handler])
        return res.content  

    async def generate_response(self, context: str) -> str:
        res = await self.llm.ainvoke(
            [HumanMessage(content=context)],
            config={"callbacks": [self.langfuse_handler]}
        )
        return res.content