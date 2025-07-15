# Dreamcatcher Local Development Setup

This guide helps you run Dreamcatcher locally without any domain configuration or complex deployment requirements.

## Prerequisites

- **Docker** and **Docker Compose** installed
- **Git** for cloning the repository
- **API Keys** from Anthropic and OpenAI (required for AI features)

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/dreamcatcher.git
cd dreamcatcher
```

### 2. Make Scripts Executable
```bash
chmod +x start-local.sh reset-local.sh
```

### 3. Start Dreamcatcher
```bash
./start-local.sh
```

The script will:
- Create a `.env` file from the template
- Ask you to add your API keys
- Start all required services with Docker Compose
- Show you the access URLs

### 4. Add Your API Keys

Edit the `.env` file and add your API keys:
```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

You can get these from:
- **Anthropic**: https://console.anthropic.com/
- **OpenAI**: https://platform.openai.com/api-keys

### 5. Access Dreamcatcher

Once started, you can access:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Manual Setup (Alternative)

If you prefer to run services manually:

### 1. Set Up Environment
```bash
cp .env.local .env
# Edit .env with your API keys
```

### 2. Set Up Python Virtual Environment (Recommended)
```bash
# Option A: Use our script
./setup-venv.sh

# Option B: Manual setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Start Services
```bash
# Start databases (if not using local PostgreSQL/Redis)
docker-compose -f docker-compose.local.yml up -d postgres redis

# Start backend (in one terminal)
cd backend
source venv/bin/activate  # if using venv
uvicorn main:app --reload

# Start frontend (in another terminal)
cd frontend
npm install
npm run dev
```

## Service Details

### PostgreSQL Database
- **Host**: localhost:5432
- **Database**: dreamcatcher
- **User**: dreamcatcher
- **Password**: dreamcatcher_password

### Redis Cache
- **Host**: localhost:6379
- **No password required**

### Backend API
- **URL**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

### Frontend
- **URL**: http://localhost:3000
- **Mobile responsive**
- **PWA installable**

## Common Commands

### Monitor Logs
```bash
# All services
docker-compose -f docker-compose.local.yml logs -f

# Specific service
docker-compose -f docker-compose.local.yml logs -f backend
docker-compose -f docker-compose.local.yml logs -f frontend
```

### Stop Services
```bash
docker-compose -f docker-compose.local.yml down
```

### Reset Everything
```bash
./reset-local.sh
```

### Rebuild Services
```bash
docker-compose -f docker-compose.local.yml build
docker-compose -f docker-compose.local.yml up -d
```

## Troubleshooting

### Services Won't Start
1. Check if Docker is running: `docker info`
2. Check if ports are free: `lsof -i :3000,8000,5432,6379`
3. Reset everything: `./reset-local.sh`

### Database Connection Issues
```bash
# Check database health
docker-compose -f docker-compose.local.yml exec postgres pg_isready -U dreamcatcher

# Connect to database
docker-compose -f docker-compose.local.yml exec postgres psql -U dreamcatcher -d dreamcatcher
```

### Backend API Errors
```bash
# Check backend logs
docker-compose -f docker-compose.local.yml logs backend

# Check health endpoint
curl http://localhost:8000/health
```

### Virtual Environment Issues
```bash
# Reset virtual environment
rm -rf backend/venv
./setup-venv.sh

# If venv creation fails, install python3-venv
sudo apt-get install python3-venv  # Ubuntu/Debian
brew install python3  # macOS

# If still having issues, try with virtualenv
pip install --user virtualenv
cd backend
python3 -m virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend Build Issues
```bash
# Check frontend logs
docker-compose -f docker-compose.local.yml logs frontend

# Rebuild frontend
docker-compose -f docker-compose.local.yml build frontend
```

## Development Workflow

### Hot Reload
Both frontend and backend support hot reload:
- **Frontend**: Changes to `frontend/src/*` automatically reload
- **Backend**: Changes to `backend/*.py` automatically reload

### Database Changes
If you modify database models:
```bash
# Restart backend to apply migrations
docker-compose -f docker-compose.local.yml restart backend
```

### Environment Changes
After modifying `.env`:
```bash
# Restart all services
docker-compose -f docker-compose.local.yml down
docker-compose -f docker-compose.local.yml up -d
```

## Optional: ComfyUI Integration

To enable visual generation:

1. Install ComfyUI locally on port 8188
2. Set `COMFYUI_ENABLED=true` in `.env`
3. Restart backend

## Features Available in Local Mode

### ✅ Fully Functional
- Idea capture (text and voice)
- AI-powered analysis and expansion
- Real-time notifications
- Advanced search and filtering
- User authentication
- WebSocket updates
- Bulk operations

### ⚠️ Limited Functionality
- **Voice capture**: Works in modern browsers with microphone permissions
- **Desktop notifications**: Requires user permission
- **ComfyUI visuals**: Requires separate ComfyUI installation

### ❌ Not Available
- SSL/HTTPS (not needed for local development)
- Domain-based features
- Production monitoring
- Email notifications

## Security Notes

### Local Development Security
- Default passwords are used (change for production)
- CORS is configured for localhost
- JWT tokens expire in 30 minutes
- Debug mode is enabled

### Production Considerations
- Change all default passwords
- Use environment-specific secrets
- Enable SSL/HTTPS
- Configure proper CORS origins
- Disable debug mode

## Next Steps

Once you have Dreamcatcher running locally:

1. **Create your first idea** - Use the voice button or text input
2. **Explore the dashboard** - See real-time stats and agent status
3. **Configure notifications** - Set up desktop alerts in Settings
4. **Try advanced search** - Use filters to find specific ideas
5. **Review proposals** - Check the AI-generated project proposals

## Getting Help

If you encounter issues:

1. Check the [troubleshooting section](#troubleshooting)
2. Review the logs: `docker-compose -f docker-compose.local.yml logs`
3. Reset everything: `./reset-local.sh`
4. Check the main [README.md](README.md) for more details

---

*Happy idea capturing! 🧠✨*