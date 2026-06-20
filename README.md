# 🌿 Haven: Your Intelligent Clinic Scheduling Assistant

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-2D333B?style=for-the-badge&logo=langchain)](https://github.com/langchain-ai/langgraph)
[![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)




https://github.com/user-attachments/assets/bc0cdbcd-dad1-4f23-bd48-50e1af90f857


**Haven** is a sophisticated, AI-driven scheduling chatbot designed to streamline patient-clinic interactions. Built with state-of-the-art orchestration via **LangGraph**, Haven handles the complexities of booking, rescheduling, and canceling appointments with an empathetic and professional touch.

---

## ✨ Key Features

- 🗓️ **Seamless Booking**: Intelligent extraction of patient names, dates, and times for frictionless scheduling.
- 🔄 **Smart Rescheduling & Cancellation**: Effortlessly manage existing appointments through natural conversation.
- 🤖 **Multi-Provider LLM Support**: Flexible backend supporting **Google Gemini**, **Ollama** (for local privacy), or a **Mock Mode** for offline development.
- 🗺️ **Stateful Graph Orchestration**: Powered by LangGraph for robust intent routing and data validation.
- 📅 **Google Calendar Integration**: Ready-to-use hooks for syncing clinic schedules with Google Calendar.
- 💾 **Persistent Memory**: Uses **MongoDB** to track conversation history and appointment states reliably.

---

## 🏗️ Architecture & Workflow

Haven uses a directed graph to manage conversation state, ensuring that every patient interaction is validated and processed accurately.

### The Graph Logic:
1.  **Intent Detection**: Identifies if the patient wants to book, cancel, reschedule, or ask a general question.
2.  **Extraction**: Pulls entities (Name, Date, Time) from the conversation.
3.  **Validation**: Ensures all required data is present and valid before committing to a booking.
4.  **Action**: Interacts with the database and calendar services.
5.  **Response**: Generates a professional, context-aware reply.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.13, FastAPI
- **Agent Framework**: LangGraph, LangChain
- **AI Models**: Google Gemini (Flash 2.5), Ollama (Local)
- **Database**: MongoDB (Motor)
- **Observability**: LangFuse
- **Environment**: Pydantic Settings
- **Frontend**: HTML/CSS/JS (Static)

---

## 🚀 Getting Started

### Prerequisites
- Python 3.13+
- MongoDB instance (Local or Atlas)
- (Optional) Ollama installed for local LLM support

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/clinic-scheduling-chatbot.git
   cd clinic-scheduling-chatbot
   ```

2. **Set up virtual environment**:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   uv sync
   ```

4. **Configure Environment Variables**:
   Create a `.env` file in the root directory:
   ```env
   PROJECT_NAME="Haven"
   MODEL_PROVIDER="Ollama"  # Or "Gemini"
   GEMINI_API_KEY="your_key_here"
   GEMINI_MODEL_NAME="gemini-2.5-flash-lite"
   MONGODB_URL="mongodb://localhost:27017"
   DATABASE_NAME="haven_db"
   LANGFUSE_PUBLIC_KEY="pk-..."
   LANGFUSE_SECRET_KEY="sk-..."
   LANGFUSE_BASE_URL="https://cloud.langfuse.com"
   Electricity_Off=False  # Set to True for dummy mode
   ```

### Running the Application

Start the FastAPI server:
```bash
uvicorn app.main:app --reload
```
Open your browser and navigate to `http://localhost:8000` to start chatting with Haven!

---

## 📸 Screenshots (Coming Soon)
*(Placeholder for UI screenshots)*

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
*Developed with ❤️ to make healthcare scheduling human-centric.*
