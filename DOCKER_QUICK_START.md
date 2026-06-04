# 🚀 Docker Quick Reference - Haven Clinic Bot

## ⚡ Super Quick Start (Copy-Paste)

```bash
# 1. Set up .env
cp .env.example .env
# Edit .env with your API keys

# 2. Start Docker
docker-compose up -d

# 3. Wait 10 seconds for MongoDB to initialize, then access:
# - App: http://localhost:8000
# - Docs: http://localhost:8000/docs
# - MongoDB: mongosh -u admin -p admin123
```

---

## 📋 Most Common Commands

| Task | Command |
|------|---------|
| **Start everything** | `docker-compose up -d` |
| **Stop everything** | `docker-compose down` |
| **View logs** | `docker-compose logs -f` |
| **Restart app** | `docker-compose restart app` |
| **Execute bash in app** | `docker-compose exec app bash` |
| **View running containers** | `docker-compose ps` |
| **Rebuild (code changed)** | `docker-compose up -d --build` |

---

## 🆚 Run Locally vs Docker

### LOCAL (No Docker)
```bash
# Install dependencies
pip install -r requirements.txt

# Start MongoDB via Docker
docker-compose up -d mongodb

# Run app locally
uvicorn app.main:app --reload
```

### DOCKER (Full containerized)
```bash
# Everything in Docker
docker-compose up -d

# App runs in container, auto-reloads with volume mounts
```

---

## 🐳 What Gets Created

| Service | Image | Port | Data Persists? |
|---------|-------|------|---|
| **FastAPI** | `clinic-scheduling-chatbot:latest` | 8000 | No (rebuild-safe) |
| **MongoDB** | `mongo:7.0-alpine` | 27017 | ✅ Yes (`mongodb_data` volume) |
| **Ollama** | `ollama/ollama` | 11434 | ✅ Yes (optional, use `--profile ollama`) |

---

## 🔑 Before First Run: Setup .env

```bash
cp .env.example .env
```

**Fill in these based on your setup**:
```env
# If using Gemini
GEMINI_API_KEY="your_key_from_google_cloud"

# If using Fanar
Fanar_API_KEY="your_key_from_fanar"

# Session secret (generate with: openssl rand -base64 32)
SESSION_SECRET_KEY="generated_random_string_here"

# Everything else has sensible defaults
```

---

## 🛠️ Development Tips

### Change Port
Edit `docker-compose.yml`:
```yaml
ports:
  - "8080:80"  # Use 8080 instead of 8000
```
Then: `docker-compose up -d`

### Code Changes Auto-Reload
Thanks to volume mounts in `docker-compose.yml`, changes to `./app` automatically reload. Just save your file and refresh the browser.

### Check if Services are Ready
```bash
# Wait for MongoDB to be healthy
docker-compose exec mongodb mongosh -u admin -p admin123 -c "db.adminCommand('ping')"

# The app waits for MongoDB automatically
```

### Debug: Access App Shell
```bash
docker-compose exec app bash

# Inside container:
python -c "import app; print('All good')"
pip list
```

---

## 🆘 Common Issues & Fixes

### "Connection refused" on Port 8000
```bash
# Port might be in use, change in docker-compose.yml or kill process:
# Windows:
netstat -ano | findstr :8000
taskkill /PID <number> /F

# Linux/Mac:
lsof -i :8000 | awk 'NR!=1 {print $2}' | xargs kill -9
```

### "MongoDB connection failed"
```bash
# MongoDB might still be initializing, wait 10 seconds
docker-compose logs mongodb

# If stuck, restart:
docker-compose restart mongodb
```

### "ModuleNotFoundError" in app
```bash
# Rebuild with new dependencies:
docker-compose up -d --build
```

### "Permission denied" (Linux)
```bash
sudo usermod -aG docker $USER
newgrp docker
```

---

## 📦 Using Different LLM Providers

### Local (Ollama) - Privacy First
```bash
# Start with Ollama service
docker-compose --profile ollama up -d

# In .env:
MODEL_PROVIDER="Ollama"

# Pull a model (first time only):
docker-compose exec ollama ollama pull command-r7b-arabic:latest
```

### Google Gemini - Easy Setup
```bash
# In .env:
MODEL_PROVIDER="Gemini"
GEMINI_API_KEY="your_key"

# Just start normally:
docker-compose up -d
```

### Fanar - Arabic-Optimized
```bash
# In .env:
MODEL_PROVIDER="Fanar"
Fanar_API_KEY="your_key"

# Start normally:
docker-compose up -d
```

---

## ✅ Verify Everything Works

```bash
# 1. Check containers are running
docker-compose ps

# 2. Open app
curl http://localhost:8000

# 3. Check MongoDB
docker-compose exec mongodb mongosh -u admin -p admin123 -c "db.adminCommand('ping')"

# 4. Check FastAPI health
curl http://localhost:8000/docs
```

---

## 🧹 Cleanup

```bash
# Stop services (keep data)
docker-compose down

# Stop and delete everything (including data!)
docker-compose down -v

# Free up disk space
docker system prune -a
```

---

## 📊 Monitor Running Services

```bash
# Real-time resource usage
docker stats

# Follow logs from all services
docker-compose logs -f

# Follow logs from specific service
docker-compose logs -f app
docker-compose logs -f mongodb
```

---

## 🚀 Next Steps

1. **Create `.env`** from `.env.example`
2. **Start**: `docker-compose up -d`
3. **Access**: http://localhost:8000
4. **Celebrate**: 🎉

---

For more details, see `DOCKER_GUIDE.md`
