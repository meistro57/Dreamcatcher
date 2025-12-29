# Dreamcatcher - Quick Start Guide

## 🏃‍♂️ Just Want to Run It?

### Option 1: Docker (Recommended)
```bash
git clone https://github.com/meistro57/Dreamcatcher.git
cd dreamcatcher
./start-local.sh
```

### Option 2: Native (Python + Node.js)
```bash
git clone https://github.com/meistro57/Dreamcatcher.git
cd dreamcatcher
./start-native.sh
```

### Option 3: Manual Setup
```bash
git clone https://github.com/meistro57/Dreamcatcher.git
cd dreamcatcher

# Set up Python virtual environment (recommended)
./setup-venv.sh

# Backend
cd backend
source venv/bin/activate
uvicorn main:app --reload &

# Frontend
cd ../frontend
npm install
npm run dev &

# Access at http://localhost:3000
```

## 🔑 API Keys Required

You'll need API keys from:
- **Anthropic**: https://console.anthropic.com/
- **OpenAI**: https://platform.openai.com/api-keys

Add them to `.env` file:
```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

## 🌐 Access Points

Once running:
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🚀 First Steps

1. **Open** http://localhost:3000
2. **Register** a new account
3. **Click the voice button** and speak an idea
4. **Watch** the AI agents process it in real-time
5. **Explore** the dashboard, notifications, and search

## 🔧 Troubleshooting

### Nothing works?
```bash
./reset-local.sh
./start-local.sh
```

### Still broken?
Check [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md) for detailed troubleshooting.

## 📚 More Information

- **[LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md)** - Detailed local setup
- **[README.md](README.md)** - Full project overview
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment

---

*Start capturing ideas in under 5 minutes! 🧠✨*