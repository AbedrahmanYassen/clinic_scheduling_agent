
# 🐳 Docker Guide for Haven Clinic Scheduling Chatbot

## Prerequisites

Make sure you have installed:
- **Docker**: [Download](https://www.docker.com/products/docker-desktop)
- **Docker Compose**: Usually included with Docker Desktop
- **Git**: For version control

### Verify Installation
```bash
docker --version
docker-compose --version
```

---

## 🚀 Quick Start (3 Steps)

### Step 1: Set Up Environment Variables

```bash
# Copy the example template
cp .env.example .env

# Edit .env with your actual API keys
# Important: Never commit .env to git!
```

**Required for each provider**:
- **Gemini**: Add `GEMINI_API_KEY`
- **Fanar**: Add `Fanar_API_KEY`
- **Ollama**: No keys needed (local)

### Step 2: Build and Start Containers

```bash
# Build and start all services (MongoDB + FastAPI)
docker-compose up -d

# This will:
# ✅ Build the FastAPI app image
# ✅ Start MongoDB (port 27017)
# ✅ Start FastAPI (port 8000)
# ✅ Create volumes for persistent data
```

### Step 3: Access the Application

- **Frontend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Swagger)
- **MongoDB**: mongodb://admin:admin123@localhost:27017

---

## 📋 Common Docker Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f mongodb
```

### Stop Services
```bash
# Stop without removing
docker-compose stop

# Stop and remove (keeps volumes)
docker-compose down

# Stop and remove everything (including volumes)
docker-compose down -v
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart app
```

### Execute Commands Inside Container
```bash
# Access app terminal
docker-compose exec app bash

# Run Python command
docker-compose exec app python -m pip list

# MongoDB shell
docker-compose exec mongodb mongosh -u admin -p admin123
```

### View Container Status
```bash
# List running containers
docker-compose ps

# Inspect container
docker inspect haven_app

# Check resource usage
docker stats
```

---

## 🛠️ Development Workflow

### Option 1: Hot Reload (Recommended for Development)

The `docker-compose.yml` includes volume mounts for live code reloading:

```yaml
volumes:
  - ./app:/code/app           # App code auto-reloads
  - ./static:/code/app/static # Static files
```

**To develop**:
1. Start containers: `docker-compose up -d`
2. Edit your code in your IDE
3. Changes auto-reload (FastAPI with `--reload`)
4. View logs: `docker-compose logs -f app`

### Option 2: Rebuild on Every Change

If hot reload doesn't work:
```bash
# Rebuild and restart
docker-compose up -d --build
```

### Option 3: Local Development (Without Docker)

If you prefer running locally:
```bash
# Install dependencies
pip install -r requirements.txt

# Start MongoDB via Docker only
docker-compose up -d mongodb

# Run FastAPI locally
uvicorn app.main:app --reload
```

---

## 🧠 Services Included

### MongoDB (Port 27017)
- **Image**: `mongo:7.0-alpine`
- **Container Name**: `haven_mongodb`
- **Username**: `admin`
- **Password**: `admin123` (change in production!)
- **Persistent**: Data stored in `mongodb_data` volume
- **Health Check**: Automatic availability detection

### FastAPI Application (Port 8000)
- **Image**: Built from `Dockerfile`
- **Container Name**: `haven_app`
- **Runs on**: Port 80 (mapped to 8000)
- **Restart Policy**: `unless-stopped`
- **Dependencies**: Waits for MongoDB to be healthy

### Ollama (Optional - Port 11434)
- **Image**: `ollama/ollama:latest`
- **Profile**: `ollama` (only runs with specific command)
- **Use Case**: Local LLM inference, privacy-first
- **Start with**: `docker-compose --profile ollama up -d`

---

## 📦 Using Different LLM Providers

### Option 1: Ollama (Local, Privacy-First)
```bash
# Start with Ollama
docker-compose --profile ollama up -d

# In your .env:
MODEL_PROVIDER="Ollama"
OLLAMA_MODEL="command-r7b-arabic:latest"

# Pull models inside container:
docker-compose exec ollama ollama pull command-r7b-arabic:latest
```

### Option 2: Google Gemini (Cloud)
```bash
# In your .env:
MODEL_PROVIDER="Gemini"
GEMINI_API_KEY="your_key_here"
GEMINI_MODEL_NAME="gemini-2.5-flash-lite"

# Start normally:
docker-compose up -d
```

### Option 3: Fanar API (Cloud)
```bash
# In your .env:
MODEL_PROVIDER="Fanar"
Fanar_API_KEY="your_key_here"

# Start normally:
docker-compose up -d
```

---

## 🔐 Production Deployment

### Important Security Steps

1. **Rotate All Secrets**:
   ```bash
   # Generate strong random keys
   openssl rand -base64 32  # For SESSION_SECRET_KEY
   ```

2. **Update Production .env**:
   ```env
   DEBUG=False
   HTTPS_ONLY=True
   MONGODB_URL="mongodb://username:strong_password@mongodb:27017/haven_db?authSource=admin"
   # ... other secure values
   ```

3. **Use Docker Secrets** (for production orchestration):
   ```yaml
   secrets:
     db_password:
       file: ./secrets/db_password.txt
   ```

4. **Enable SSL/TLS**:
   - Use Nginx reverse proxy with Let's Encrypt
   - Set `HTTPS_ONLY=True`

5. **Database Hardening**:
   - Change MongoDB credentials
   - Enable authentication
   - Use strong passwords
   - Restrict network access

### Example Production docker-compose.yml Snippet
```yaml
environment:
  DEBUG=False
  HTTPS_ONLY=True
  MONGODB_URL=mongodb://username:${MONGO_PASSWORD}@mongodb:27017/haven_db?authSource=admin
```

---

## 🐛 Troubleshooting

### Issue: MongoDB Connection Error
```bash
# Check MongoDB is healthy
docker-compose ps

# View MongoDB logs
docker-compose logs mongodb

# Restart MongoDB
docker-compose restart mongodb
```

### Issue: Port Already in Use
```bash
# If port 8000 is taken, edit docker-compose.yml:
ports:
  - "8080:80"  # Use 8080 instead

# Or kill the process using the port
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux:
lsof -i :8000
kill -9 <PID>
```

### Issue: App Exits Immediately
```bash
# Check logs
docker-compose logs app

# Common causes:
# - Missing .env variables
# - MongoDB not ready yet
# - Python import errors
```

### Issue: Permission Denied (Linux)
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Or prefix commands with sudo:
sudo docker-compose up
```

### Issue: Out of Disk Space
```bash
# Clean up unused Docker resources
docker system prune -a

# Remove unused volumes
docker volume prune
```

---

## 📊 Monitoring

### View Real-Time Stats
```bash
docker stats

# Output: CPU %, Memory usage, Network I/O, Block I/O
```

### Check Service Health
```bash
# MongoDB health
docker-compose exec mongodb mongosh -u admin -p admin123 -c "db.adminCommand('ping')"

# App health (if endpoint exists)
curl http://localhost:8000/health
```

### Access Application Logs
```bash
# Real-time logs with color
docker-compose logs -f --tail 50

# Logs with timestamps
docker-compose logs --timestamps -f
```

---

## 🔄 Updating & Rebuilding

### Update Application Code
```bash
# If you modified app code, rebuild:
docker-compose up -d --build

# This will:
# ✅ Rebuild the image
# ✅ Keep MongoDB data intact
# ✅ Restart the app
```

### Update Dependencies
```bash
# If you modified requirements.txt:
docker-compose up -d --build

# Or manually:
docker-compose exec app pip install -r requirements.txt
docker-compose restart app
```

### Clean Rebuild (Remove Everything)
```bash
# Stop and remove all (keeps .env and code)
docker-compose down -v

# Rebuild from scratch
docker-compose up -d --build
```

---

## 📁 Docker File Structure

```
clinic_scheduling_chatbot/
├── Dockerfile              # App container definition
├── docker-compose.yml      # Multi-container orchestration
├── .env                    # ❌ NEVER commit (secrets)
├── .env.example           # ✅ Safe template
├── requirements.txt       # Python dependencies
├── app/
│   ├── main.py
│   ├── api/
│   ├── core/
│   ├── services/
│   ├── schemas/
│   ├── utils/
│   └── static/
└── README.md
```

---

## ✅ Checklist

Before deploying with Docker:

- [ ] Copy `.env.example` to `.env`
- [ ] Fill in all required API keys in `.env`
- [ ] Add `.env` to `.gitignore` (if not already)
- [ ] Test locally with `docker-compose up -d`
- [ ] Verify app at `http://localhost:8000`
- [ ] Verify API docs at `http://localhost:8000/docs`
- [ ] Check MongoDB connection: `docker-compose exec mongodb mongosh -u admin -p admin123`
- [ ] View logs: `docker-compose logs -f`
- [ ] For production: Update credentials and security settings

---

## 📚 Useful Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [MongoDB Docker Documentation](https://hub.docker.com/_/mongo)
- [FastAPI with Docker](https://fastapi.tiangolo.com/deployment/docker/)

---

**Last Updated**: 2026-05-24  
**Docker Compose Version**: 3.8  
**Docker Image**: Python 3.14, MongoDB 7.0, Ollama Latest
