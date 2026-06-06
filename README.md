# 🏥 Haven - Clinic Scheduling Chatbot

Haven is an AI-powered clinic scheduling assistant built with **FastAPI** and **LangGraph**. It helps patients book, reschedule, and cancel appointments through a natural language interface, supporting multiple LLM providers including Google Gemini, Ollama, and Fanar.

![Haven LangGraph](langgraph.png)

## ✨ Features

- **🤖 Intelligent Scheduling**: Automated booking, rescheduling, and cancellation of clinic appointments.
- **🧠 Multi-Agent Logic**: Powered by **LangGraph** for robust state management and intent routing.
- **🌍 Multi-LLM Support**: Seamlessly switch between **Google Gemini**, **Ollama** (local), and **Fanar API**.
- **📅 Smart Availability**: Automatically suggests alternative time slots when requested appointments conflict.
- **💾 Persistent Memory**: Uses **MongoDB** to store chat history, session state, and reservation data.
- **🔍 Observability**: Integrated with **Langfuse** for tracing and performance monitoring.
- **🇸🇦 Arabic Support**: Optimized for Arabic natural language processing and clinic workflows.
- **🐳 Docker Ready**: Full containerization for easy deployment and local development.

## 🛠️ Tech Stack

- **Backend**: [FastAPI](https://fastapi.tiangolo.com/)
- **Agent Orchestration**: [LangGraph](https://langchain-ai.github.io/langgraph/) / [LangChain](https://www.langchain.com/)
- **Database**: [MongoDB](https://www.mongodb.com/) (Async Motor driver)
- **LLM Providers**: Google Gemini, Ollama, Fanar
- **Observability**: [Langfuse](https://langfuse.com/)
- **Package Management**: [uv](https://github.com/astral-sh/uv)
- **Deployment**: Docker & Docker Compose

## 🚀 Getting Started

### Prerequisites

- Python 3.13+
- MongoDB (Local or Atlas)
- Docker (Optional)

### Local Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd clinic-scheduling-chatbot
   ```

2. **Set up the environment**:
   ```bash
   # Using uv (recommended)
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv sync
   
   # Or using pip
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and fill in your keys:
   ```bash
   cp .env.example .env
   ```

4. **Run the application**:
   ```bash
   uvicorn app.main:app --reload
   ```
   The API will be available at `http://localhost:8000`.

### Running with Docker

1. **Quick Start**:
   ```bash
   docker-compose up -d
   ```
2. **Access the Application**:
   - Frontend: `http://localhost:8000`
   - API Docs (Swagger): `http://localhost:8000/docs`

For detailed Docker instructions, see [DOCKER_GUIDE.md](DOCKER_GUIDE.md).

## ⚙️ Configuration

The application is configured via environment variables in the `.env` file. Key settings include:

| Variable | Description | Default |
|----------|-------------|---------|
| `PROJECT_NAME` | Name of the clinic | `Haven` |
| `MODEL_PROVIDER` | AI Provider (`Gemini`, `Ollama`, `Fanar`) | `Fanar` |
| `MONGODB_URI` | MongoDB Connection String | Required |
| `GEMINI_API_KEY` | API Key for Google Gemini | Required for Gemini |
| `TIME_ZONE` | Clinic timezone | `Asia/Gaza` |

## 🤖 LLM Providers

### Google Gemini
Set `MODEL_PROVIDER=Gemini` and provide `GEMINI_API_KEY`. It uses the `gemini-2.5-flash-lite` model by default.

### Ollama (Local)
Set `MODEL_PROVIDER=Ollama` and `OLLAMA_MODEL`. Ensure Ollama is running locally or via Docker.
```bash
docker-compose --profile ollama up -d
```

### Fanar API
Set `MODEL_PROVIDER=Fanar` and provide `Fanar_API_KEY`.

## 📂 Project Structure

```text
clinic_scheduling_chatbot/
├── app/
│   ├── api/v1/         # API Endpoints (Chat, Test)
│   ├── core/           # Configuration and Prompts
│   ├── schemas/        # Pydantic Models
│   ├── services/       # Business Logic & Agent Graph
│   │   ├── scheduling_agent/ # LangGraph Definition
│   │   └── tools/      # Agent Tools
│   ├── static/         # Web Frontend
│   └── utils/          # Date parsers and Helpers
├── docker-compose.yml  # Docker Orchestration
├── Dockerfile          # Container Definition
└── pyproject.toml      # Dependency Management
```

## 📝 Roadmap

See [TODO.md](TODO.md) for a detailed list of planned improvements, including:
- [ ] Move database cleanup to background jobs.
- [ ] Implement robust error handling and logging.
- [ ] Add unit and integration tests.
- [ ] Implement rate limiting and CORS security.

---

**Developed with ❤️ for better healthcare accessibility.**
