# app/services/llm_service.py

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from app.core.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langfuse import Langfuse, get_client
from langfuse.langchain import CallbackHandler
from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime
from langchain_openai import ChatOpenAI

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
            elif settings.MODEL_PROVIDER == "Fanar":
                self.llm = ChatOpenAI(
                    base_url="https://api.fanar.qa/v1",
                    api_key=settings.Fanar_API_KEY,
                    model="Fanar",
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
        now = datetime.now()
        current_year = now.year
        current_month = now.month
        current_month_name = now.strftime("%B")

        system_prompt = f'''
Extract structured appointment information from the user message.

Return ONLY valid JSON. Do not include any explanation or text outside JSON.

-----------------------
FIELDS
-----------------------
- name: string or null
- service: string or null
- date: MUST be in ISO format YYYY-MM-DD  or null if missing or unclear
- time: MUST be in 24-hour format HH:MM (e.g., 14:30) or null if missing or unclear

-----------------------
NORMALIZATION RULES
-----------------------

- If date or time is missing or unclear, return null
- If the year is missing, use the current year: {current_year}
- If the month is missing, use the current month: {current_month} ({current_month_name})
- If multiple options are mentioned, choose the most likely one

-----------------------
IMPORTANT
-----------------------
- Do NOT return natural language dates like "tomorrow"
- Do NOT return "3pm" — always convert to HH:MM
- Do NOT guess missing information
- Never assume anything that is not explicitly mentioned in the message
-----------------------
MESSAGE:
{message}

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
            SystemMessage(content=system_prompt),
            HumanMessage(content=message)
        ]
        res = await self.llm.ainvoke(
        prompt,
        config={"callbacks": [self.langfuse_handler]}
        )

        # res = await self.llm.ainvoke(prompt, callbacks=[self.langfuse_handler])
        return res.content  

    async def generate_response(self, context: str, summary: str = "") -> str:
        
        res = await self.llm.ainvoke(
            context,
            config={"callbacks": [self.langfuse_handler]}
        )
        return res.content
    
    
    async def others_llm(self, message: str, summary: str = "") -> str:
        handle_others_prompt = """
You are a polite and friendly clinic appointment assistant.

Your role is ONLY:
- booking appointments
- canceling appointments
- rescheduling appointments
- answering appointment-related questions

The user sent a message outside the assistant scope.

Use the conversation history summary to make the reply feel personalized and natural.

Conversation history summary:
{history_summary}

Current user message:
{user_message}

Instructions:
- Politely explain that this chat is only for appointment management.
- If the user provides any relevant information in their message (like their name or appointment details), acknowledge it warmly and say you will try to record it, but still clarify that you can only assist with appointment-related tasks.
- Mention supported actions naturally:
  - booking appointments
  - canceling appointments
  - rescheduling appointments

- Keep the response short and conversational.
- Sound human and warm.
- If possible, personalize the response using the history summary.
- Do not sound robotic or repetitive.
- Do not mention "AI", "language model", or "system".
- Respond in the same language as the user.

Example tone:
"أقدر سؤالك 😊 لكن هذه المحادثة مخصصة فقط لإدارة المواعيد، مثل الحجز أو الإلغاء أو تغيير الموعد. إذا حاب، أقدر أساعدك بحجز موعد أو تعديل موعدك الحالي."

Return ONLY the response message.
"""
        res = await self.llm.ainvoke(
            [SystemMessage(content=handle_others_prompt.format(history_summary=summary, user_message=message)),HumanMessage(content=message)], 
            config={"callbacks": [self.langfuse_handler]}
        )
        return res.content