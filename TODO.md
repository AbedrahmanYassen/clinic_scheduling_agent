# 🎯 Haven Project - Improvement TODOs

**Last Updated**: 2026-05-24  
**Project**: Clinic Scheduling Chatbot (Haven)  
**Status**: 17 Improvement items identified

---

## 🚨 CRITICAL - Security & Secrets

### [ ] SEC-001: Remove Exposed API Keys from `.env`
**Severity**: CRITICAL  
**Files Affected**: `.env` (needs to be removed), `.gitignore`

**Description**:
- The `.env` file contains real, active API keys:
  - Gemini API Key
  - Langfuse Secret & Public Keys
  - Fanar API Key
- This file is committed to git and publicly exposed on GitHub
- **Action Required**: 
  - [ ] Rotate all exposed API keys immediately
  - [ ] Add `.env` to `.gitignore`
  - [ ] Remove `.env` from git history: `git rm --cached .env && git commit -m "Remove .env"`
  - [ ] Use environment variables only for secrets

**Priority**: 1

---

### [ ] SEC-002: Move Hardcoded Session Secret Key to Environment
**Severity**: HIGH  
**Files Affected**: `app/main.py` (line 33)

**Current Code**:
```python
app.add_middleware(
    SessionMiddleware,
    secret_key="SuperSecretKeyLearningFastAPI",  # ❌ HARDCODED!
)
```

**Action Required**:
- [ ] Add `SESSION_SECRET_KEY` to `.env` and `settings`
- [ ] Replace hardcoded string with `settings.SESSION_SECRET_KEY`
- [ ] Ensure it's a strong, random key (minimum 32 characters)

**Priority**: 2

---

## ⚠️ HIGH PRIORITY - Code Quality

### [ ] CLEAN-001: Remove Unused Imports
**Severity**: HIGH  
**Files Affected**: Multiple

**Unused Imports Found**:
- `app/api/v1/chat.py` (line 3): `from unittest import result`
- `app/services/scheduling_agent/nodes.py` (line 2): `from urllib import response`
- `app/services/reservation_service.py` (line 2): `from tracemalloc import start`
- `app/services/scheduling_agent/state.py`: Check imports
- Multiple datetime imports (line 1 in reservation_service.py has duplicate imports)

**Action Required**:
- [ ] Remove all unused imports
- [ ] Run linter to catch similar issues: `pylint app/` or `flake8 app/`

**Priority**: 3

---

### [ ] ARCH-001: Move Database Cleanup to Background Job
**Severity**: HIGH  
**Files Affected**: `app/services/scheduling_agent/nodes.py` (line 20)

**Current Problem**:
```python
async def intent_node(state: AgentState):
    # Called EVERY time user sends a message!
    await state.get("reservation").cleanup_old_reservations()
```

**Why It's Bad**:
- Database cleanup runs on EVERY intent classification
- Expensive operation blocking user response time
- Should be scheduled task, not per-request

**Action Required**:
- [ ] Install APScheduler: `pip install apscheduler`
- [ ] Create `app/services/background_tasks.py`
- [ ] Schedule cleanup to run every hour or daily
- [ ] Remove cleanup call from `intent_node`
- [ ] Test background job runs correctly

**Reference**: See `for_later/` folder for future ideas

**Priority**: 4

---

### [ ] ERROR-001: Implement Proper Error Handling & Logging
**Severity**: HIGH  
**Files Affected**: `app/services/scheduling_agent/nodes.py`, `app/services/agent_service.py`, multiple files

**Current Problems**:
- Generic `except Exception as e:` blocks everywhere
- Using `print()` for debugging instead of logging
- No custom exceptions
- No error context for debugging

**Action Required**:
- [ ] Create `app/core/exceptions.py` with custom exceptions:
  ```python
  class ReservationConflictError(Exception): pass
  class InvalidAppointmentError(Exception): pass
  class ExtractionError(Exception): pass
  ```
- [ ] Replace all `print()` with `logging`:
  ```python
  import logging
  logger = logging.getLogger(__name__)
  logger.info("message")  # instead of print()
  ```
- [ ] Create structured logging configuration in `app/core/logging.py`
- [ ] Replace generic `except Exception` with specific exceptions
- [ ] Add proper error context and traceback logging

**Priority**: 5

---

## 📋 MEDIUM PRIORITY - Code Quality & Architecture

### [ ] TYPO-001: Rename AppoinementInfo → AppointmentInfo
**Severity**: MEDIUM  
**Files Affected**: 
- `app/schemas/chat.py`
- `app/services/scheduling_agent/nodes.py`
- `app/services/persistent_short_memory.py`
- `app/services/reservation_service.py`
- `app/utils/date_parser.py`

**Description**: Class name is misspelled "AppoinementInfo" (should be "AppointmentInfo")

**Action Required**:
- [ ] Rename class in `app/schemas/chat.py`
- [ ] Update all imports and usages across the codebase
- [ ] Run tests to ensure no breakage

**Priority**: 6

---

### [ ] CONFIG-001: Extract Hardcoded Business Logic to Configuration
**Severity**: MEDIUM  
**Files Affected**: `app/services/reservation_service.py` (lines 64-66, 69-76)

**Current Hardcoded Values**:
```python
WORK_START = time(9, 0)
WORK_END = time(17, 0)
# Friday is off (weekday == 4)
# 30-minute appointment slots
```

**Action Required**:
- [ ] Add to `app/core/config.py`:
  ```python
  WORK_START_TIME: str = "09:00"
  WORK_END_TIME: str = "17:00"
  APPOINTMENT_DURATION_MINUTES: int = 30
  DAYS_OFF: list = [4]  # Friday (0=Sunday in Python)
  ```
- [ ] Update `ReservationService` to use settings
- [ ] Add admin UI or API to manage clinic hours (future feature)

**Priority**: 7

---

### [ ] PERF-001: Disable PNG Generation in Production
**Severity**: MEDIUM  
**Files Affected**: `app/services/agent_service.py` (lines 19-22)

**Current Problem**:
```python
png_data = agent_graph_builder.get_graph().draw_mermaid_png()
with open("langgraph.png", "wb") as f:
    f.write(png_data)  # Expensive! Every request!
```

**Action Required**:
- [ ] Wrap in debug flag:
  ```python
  if settings.DEBUG:
      png_data = agent_graph_builder.get_graph().draw_mermaid_png()
      with open("langgraph.png", "wb") as f:
          f.write(png_data)
  ```
- [ ] Add `DEBUG: bool = False` to `settings`
- [ ] Test performance improvement

**Priority**: 8

---

### [ ] TYPE-001: Add Missing Type Hints
**Severity**: MEDIUM  
**Files Affected**: Multiple files

**Examples of Missing Type Hints**:
```python
# ❌ Missing return type
async def update_memory(self, session_id: str, entities):
    pass

# ❌ Missing types
def post_validation_router(state):
    pass

# ❌ Incomplete
async def create_reservation(self, appointment_info: dict) -> dict:
    # dict is too generic, should be AppointmentInfo
```

**Action Required**:
- [ ] Add return types to all async functions
- [ ] Replace generic `dict` with specific models (Pydantic)
- [ ] Run mypy for type checking: `pip install mypy && mypy app/`
- [ ] Target: 100% type hint coverage

**Priority**: 9

---

### [ ] ARCH-002: Implement Dependency Injection
**Severity**: MEDIUM  
**Files Affected**: `app/services/agent_service.py`, `app/api/v1/chat.py`

**Current Problem**:
```python
# Services create their own dependencies - tight coupling
scheduling_agent_service = SchedulingAgentService(db=request.app.mongodb, session_id=session_id)
```

**Action Required**:
- [ ] Consider using FastAPI dependency injection or a DI container
- [ ] Refactor to pass dependencies from outside
- [ ] Benefits: easier testing, configuration management

**Priority**: 10

---

### [ ] BUG-001: Fix suggest_alternatives() Logic
**Severity**: MEDIUM  
**Files Affected**: `app/services/reservation_service.py` (lines 150-157)

**Current Code**:
```python
if conflict_result["conflict"] and conflict_result["type"] == "conflict":
    suggestions += "إليك بعض المواعيد البديلة المتاحة لـ : "
if (not conflict_result["conflict"] 
    and conflict_result["type"] == "conflict"  # ❌ CONTRADICTORY!
    and self._is_within_working_hours(current, end)
):
    suggestions += current.strftime("%Y-%m-%d %H:%M") + ", "
```

**Action Required**:
- [ ] Review and fix the logic
- [ ] Add unit tests for alternative suggestions
- [ ] Ensure suggestions are actually available slots

**Priority**: 11

---

### [ ] CONFIG-002: Make https_only Environment-Based
**Severity**: MEDIUM  
**Files Affected**: `app/main.py` (line 36)

**Current Problem**:
```python
https_only=True  # ❌ Breaks local development!
```

**Action Required**:
- [ ] Add `HTTPS_ONLY: bool = False` to settings (default False for local dev)
- [ ] Update middleware:
  ```python
  https_only=settings.HTTPS_ONLY
  ```
- [ ] Set `HTTPS_ONLY=True` in production `.env`

**Priority**: 12

---

### [ ] LOGS-001: Replace All print() with Logging
**Severity**: MEDIUM  
**Files Affected**: `app/services/scheduling_agent/nodes.py` and throughout

**Examples**:
```python
print("[Intent Node] State before processing:")
print("|")
print("|")
```

**Action Required**:
- [ ] Replace all `print()` with `logging.debug()`, `logging.info()`, etc.
- [ ] Remove debug-only print statements
- [ ] Implement in conjunction with ERROR-001

**Priority**: 13

---

### [ ] API-001: Add CORS Configuration
**Severity**: MEDIUM  
**Files Affected**: `app/main.py`

**Description**: No CORS middleware configured, may cause issues with frontend integration

**Action Required**:
- [ ] Add CORSMiddleware:
  ```python
  from fastapi.middleware.cors import CORSMiddleware
  
  app.add_middleware(
      CORSMiddleware,
      allow_origins=settings.ALLOWED_ORIGINS.split(","),
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```
- [ ] Add `ALLOWED_ORIGINS` to settings
- [ ] Test with frontend

**Priority**: 14

---

## 🧪 TESTING - Critical Gap

### [ ] TEST-001: Implement Unit Tests
**Severity**: MEDIUM  
**Files Affected**: Entire project

**Current Status**: 
- No tests exist
- Test endpoints in `app/api/v1/chat.py` are incomplete

**Action Required**:
- [ ] Create `tests/` directory structure:
  ```
  tests/
    __init__.py
    conftest.py
    unit/
      test_reservation_service.py
      test_llm_service.py
      test_agent_service.py
    integration/
      test_chat_endpoint.py
  ```
- [ ] Write tests for core services
- [ ] Set up pytest configuration
- [ ] Target: 80%+ code coverage
- [ ] Add CI/CD to run tests on push

**Priority**: 15

---

## 📚 DOCUMENTATION - Low Priority

### [ ] DOCS-001: Add Docstrings to All Functions
**Severity**: LOW  
**Files Affected**: Multiple files

**Example**:
```python
# ❌ Current (no docstring)
async def classify_intent(self, message: str) -> str:
    prompt = [...]

# ✅ Should be
async def classify_intent(self, message: str) -> str:
    """Classify the user's intent from their message.
    
    Args:
        message: The user's message in Arabic
        
    Returns:
        The classified intent (book, cancel, reschedule, info, booking_info)
        
    Raises:
        ValueError: If LLM service is not initialized
    """
```

**Action Required**:
- [ ] Add docstrings to all public functions
- [ ] Use Google or NumPy docstring format consistently
- [ ] Generate documentation with Sphinx (optional)

**Priority**: 16

---

### [ ] RATE-001: Add Rate Limiting
**Severity**: LOW  
**Files Affected**: `app/api/v1/chat.py`

**Description**: No rate limiting on chat endpoint - vulnerable to abuse

**Action Required**:
- [ ] Add `slowapi` or `fastapi-limiter`:
  ```bash
  pip install slowapi
  ```
- [ ] Limit requests per session/IP
- [ ] Document rate limits

**Priority**: 17

---

## 📊 Summary

| Priority | Category | Count | Status |
|----------|----------|-------|--------|
| 1-2 | 🔴 CRITICAL/SECURITY | 2 | ⚠️ DO FIRST |
| 3-5 | 🟠 HIGH | 3 | ⚠️ IMPORTANT |
| 6-17 | 🟡 MEDIUM/LOW | 12 | 📋 BACKLOG |

---

## ✅ Suggested Order of Implementation

1. **DAY 1 (CRITICAL)**:
   - [ ] SEC-001: Remove exposed API keys & rotate secrets
   - [ ] SEC-002: Move session secret to environment

2. **DAY 2-3 (HIGH)**:
   - [ ] CLEAN-001: Remove unused imports
   - [ ] ARCH-001: Move DB cleanup to background job
   - [ ] ERROR-001: Implement logging & custom exceptions

3. **DAY 4-5 (MEDIUM - Quick Wins)**:
   - [ ] TYPO-001: Rename AppoinementInfo
   - [ ] CONFIG-001: Extract hardcoded business logic
   - [ ] PERF-001: Disable PNG generation in prod
   - [ ] LOGS-001: Replace print() with logging

4. **DAY 6+ (MEDIUM - Larger Tasks)**:
   - [ ] TYPE-001: Add type hints
   - [ ] ARCH-002: Implement dependency injection
   - [ ] TEST-001: Write unit tests
   - [ ] API-001: Add CORS
   - [ ] BUG-001: Fix suggest_alternatives logic

5. **FUTURE (LOW)**:
   - [ ] DOCS-001: Add docstrings
   - [ ] RATE-001: Add rate limiting

---

**Generated**: 2026-05-24 10:57 UTC+3
