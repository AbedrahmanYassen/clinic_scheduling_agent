# app/services/llm_service.py

from langchain_core.messages import HumanMessage, SystemMessage
from app.core.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langfuse import Langfuse, get_client
from langfuse.langchain import CallbackHandler
from langchain_openai import ChatOpenAI
from app.utils.date_parser import parse_arabic_date
import json
import re

class LLMService:
    def __init__(self):
        
        Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_BASE_URL  # Optional: defaults to https://cloud.langfuse.com
        )

        self.langfuse = get_client()

        self.langfuse_handler = CallbackHandler()



        if settings.MODEL_PROVIDER == "Gemini":
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
        self.langfuse.flush()


    async def classify_intent(self, message: str , history: str) -> str:
        prompt = [
            SystemMessage(content='''
أنت مصنف نوايا لمساعد حجز مواعيد في عيادة.

مهمتك هي قراءة رسالة المستخدم باللغة العربية وإرجاع كلمة واحدة فقط من القائمة التالية:

و عليك قراءة أخر تلات رسائل المستخدم في المحادثة لأخذ فكرة عن سياق الحديث و لتقديم تصنيف أدق للنوايا، لكن لا تذكر هذه الرسائل في التصنيف، فقط استخدمها كخلفية لفهم أفضل.
- book
- cancel
- reschedule
- appointment_info
- info

التصنيفات:
- book → إذا كان المستخدم يريد حجز موعد جديد.
- cancel → إذا كان المستخدم يريد إلغاء موعد، أو أعرب عن عدم رضاه عن الموعد الحالي أو أنه لا يناسبه.
- reschedule → إذا كان المستخدم يريد تغيير أو تأجيل أو إعادة جدولة موعد.
- appointment_info → إذا أراد المستخدم أن يرى معلومات عن موعده الحالي أو السابق.
- info → إذا كان المستخدم يرسل معلومات فقط مثل الاسم أو التاريخ أو الوقت بدون طلب واضح.

قواعد مهمة:
- أرجع كلمة واحدة فقط.
- لا تشرح.
- لا تضف علامات ترقيم.
- إذا أعرب المستخدم عن رفض الموعد أو عدم ملاءمته دون ذكر موعد بديل، صنّفه cancel.
- إذا أعرب عن رفض الموعد وذكر وقتاً أو يوماً بديلاً، صنّفه reschedule.

أمثلة:

المستخدم: أريد حجز موعد
book

المستخدم: لو سمحت ألغِ موعدي
cancel

المستخدم: بدي أغير موعدي للساعة 5
reschedule

المستخدم: اسمي أحمد وموعدي الثلاثاء
info

المستخدم: هذا الموعد ما يناسبني
cancel

المستخدم: ما أبغى هذا الموعد
cancel

المستخدم: هذا الوقت ما يصلح معي
cancel

متى موعدي الحالي؟
appointment_info
المستخدم: لا يناسبني هذا الوقت، ممكن الخميس بدل كذا؟
reschedule
                          
بدي أغير اسمي في الحجز  
reschedule             
                                       
أخر 3 رسائل من المستخدم:
{history}
الرسالة:
{text}'''.format(text=message , history=history)),               
            HumanMessage(content=message)
        ]
        res = await self.llm.ainvoke(
            prompt,
            config={"callbacks": [self.langfuse_handler]}
        )
        # res = await self.llm.ainvoke(prompt, callbacks=[self.langfuse_handler])
        return res.content.strip().lower()

    async def extract_entities(self, message: str) -> dict:
    
        system_prompt = f'''
    Extract structured appointment information from the user message.

    Return ONLY valid JSON. Do not include any explanation or text outside JSON.

    -----------------------
    FIELDS
    -----------------------
    - name: string or null
    - service: string or null : any symptopm or pain the user mentioned.
    - date: Return in ISO format YYYY-MM-DD if you're confident, 
            OR return the date expression in natural Arabic (e.g. "بكرة", "الخميس الجاي", "نهاية الأسبوع") if unclear.
            Return null ONLY if no date was mentioned at all.
    - time: MUST be in 24-hour format HH:MM (e.g., 14:30) or null if missing or unclear

    -----------------------
    TIME INFERENCE RULES
    -----------------------
    - If the user says صباحاً / الصبح / morning         → assume 09:00 if no specific hour given
    - If the user says الظهر / ظهراً / noon              → assume 12:00
    - If the user says بعد الظهر / afternoon             → assume 14:00
    - If the user says العصر / mid-afternoon             → assume 15:00  
    - If the user says المسا / مساءً / evening           → assume 18:00
    - If the user says الليل / ليلاً / night             → assume 20:00

    - If the user gives BOTH a specific hour AND a period (e.g. "3 المسا"), 
    convert the hour using the period as context:
        · صباح  → hour as-is if 6–11, else add 0   (e.g. 9 الصبح  → 09:00)
        · مسا   → add 12 if hour is 1–6             (e.g. 3 المسا  → 15:00)
        · ليل   → add 12 if hour is 7–11            (e.g. 9 الليل  → 21:00)

    -----------------------
    IMPORTANT
    -----------------------
    - Do NOT return "3pm" — always convert time to HH:MM
    - Do NOT guess missing information
    - Do NOT return null for date if the user mentioned any date expression

    -----------------------
    MESSAGE:
    {message}

    -----------------------
    OUTPUT FORMAT:
    {{
        "name": "...",
        "date": "YYYY-MM-DD or natural Arabic expression or null",
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

        try:
            llm_data = json.loads(res.content)
        except json.JSONDecodeError:
            cleaned = re.sub(r"```json|```", "", res.content).strip()
            llm_data = json.loads(cleaned)

        raw_date = llm_data.get("date")
        resolved_date = None

        if raw_date:
            is_iso = re.fullmatch(r'\d{4}-\d{2}-\d{2}', str(raw_date).strip())
            if is_iso:
                resolved_date = raw_date
            else:
                parsed = parse_arabic_date(raw_date)
                resolved_date = parsed.strftime('%Y-%m-%d') if parsed else None
        print("Resolved date" , resolved_date)

        # If we got a valid date, check the year
        if resolved_date:
            year = int(resolved_date[:4])  # extract year from "YYYY-MM-DD"
            if year < 2026:
                resolved_date = '2026' + resolved_date[4:] 
        llm_data["date"] = resolved_date

        return {"llm_response": llm_data, "dateParser": resolved_date}
    async def generate_response(self, context: str, summary: str = "") -> str:
        
        res = await self.llm.ainvoke(
            context,
            config={"callbacks": [self.langfuse_handler]}
        )
        return res.content
    
    
    async def others_llm(self, message: str) -> str:
        handle_others_prompt = """
You are a polite and friendly clinic appointment assistant.

Your role is ONLY:
- booking appointments
- canceling appointments
- rescheduling appointments
- answering appointment-related questions

The user sent a message outside the assistant scope.

Use the conversation history summary to make the reply feel personalized and natural.

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
"شكرا لتزويدنا بهذه المعلومة سنسخدمها لتقديم خدمة أفضل لك في المستقبل ان شاء الله"
Return ONLY the response message.
"""
        res = await self.llm.ainvoke(
            [SystemMessage(content=handle_others_prompt.format( user_message=message)),HumanMessage(content=message)], 
            config={"callbacks": [self.langfuse_handler]}
        )
        return res.content
    

    def generate_missing_info_response(self, entities: dict) -> str:
        missing_fields = [field for field, value in entities.items() if value is None]
        if not missing_fields:
            return ""
        
        field_names = {
            "name": "الاسم",
            "date": "التاريخ",
            "time": "الوقت",
            "service": "الخدمة"
        }
        missing_arabic = [field_names.get(field, field) for field in missing_fields]
        if len(missing_arabic) == 1:
            return f" من فضلك زودني ب{missing_arabic[0]}."
        else:
            all_but_last = ", ".join(missing_arabic[:-1])
            last = missing_arabic[-1]
            return f" من فضلك زودني ب{all_but_last} و {last}."