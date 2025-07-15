# Claude Code Guide for Dreamcatcher

## Project Overview
**Dreamcatcher** is an AI-powered idea factory that captures, develops, and evolves ideas through a network of specialized AI agents. The system operates as a "digital basement" where ideas are continuously generated, refined, and improved through autonomous agent collaboration.

### Core Philosophy
- **"The basement never sleeps"** - 24/7 autonomous operation
- **Agent-driven evolution** - Self-improving AI agents that analyze and rewrite code
- **Instant idea capture** - Mobile-first PWA for capturing fleeting thoughts
- **Collaborative intelligence** - 7 specialized agents working together

## Architecture

### Tech Stack
- **Backend**: FastAPI (Python 3.11+), PostgreSQL, Redis
- **Frontend**: React + TypeScript, Vite, TailwindCSS, PWA
- **AI Integration**: Claude AI, OpenAI, ComfyUI for visual generation
- **Deployment**: Docker Compose, Nginx reverse proxy
- **Agent System**: Async message-based communication

### Key Components
1. **Agent System** (`backend/agents/`) - 7 specialized AI agents
2. **API Layer** (`backend/api/`) - RESTful endpoints + WebSocket
3. **Database** (`backend/database/`) - PostgreSQL with SQLAlchemy
4. **Frontend** (`frontend/`) - React PWA with offline support
5. **Evolution System** (`backend/services/evolution_service.py`) - Self-improvement core

## Development Setup

### Quick Start
```bash
# Clone and start
git clone <repo>
cd Dreamcatcher
./scripts/start.sh

# Or manual Docker setup
docker-compose -f docker/docker-compose.yml up -d
```

### Environment Variables
Required in `.env`:
```
ANTHROPIC_API_KEY=your_claude_key
OPENAI_API_KEY=your_openai_key
DB_PASSWORD=secure_password
SECRET_KEY=your_secret_key
COMFY_API_URL=http://localhost:8188
```

### Development Commands
```bash
# Backend
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm run dev          # Development server
npm run build        # Production build
npm run lint         # ESLint
npm run type-check   # TypeScript checking

# Docker
docker-compose -f docker/docker-compose.yml up -d    # Start all services
docker-compose -f docker/docker-compose.yml down    # Stop services
docker-compose -f docker/docker-compose.yml logs -f # View logs
```

## Agent System (Core Feature)

### The 7 Agents
1. **Idea Catalyst** - Generates and refines ideas
2. **Concept Mapper** - Creates visual mind maps
3. **Research Hound** - Gathers information and context
4. **Prototype Builder** - Creates mockups and prototypes
5. **Reality Checker** - Validates feasibility and market fit
6. **Storyteller** - Crafts compelling narratives
7. **Meta Agent** - Self-improvement and evolution (NEW)

### Agent Communication
- **Message-based**: Async queue system via Redis
- **Base class**: `backend/agents/base_agent.py`
- **Registry**: `backend/agents/agent_registry.py`
- **Performance tracking**: Built-in metrics and logging

## Self-Improvement System (Critical Feature)

### Evolution Service (`backend/services/evolution_service.py`)
- **Automated code analysis** using Claude AI
- **5 evolution strategies**: Performance, error reduction, features, quality, coordination
- **Safe backup/rollback** mechanism
- **Performance trend analysis**

### Evolution Scheduler (`backend/scheduler/evolution_scheduler.py`)
- **24/7 autonomous operation**
- **Configurable evolution intervals** (default: 4 hours)
- **Health monitoring** every 30 minutes
- **Emergency evolution** when health < 30%

### Evolution API (`backend/api/evolution.py`)
```python
GET /api/evolution/status     # Current evolution status
POST /api/evolution/trigger   # Manual evolution trigger
POST /api/evolution/rollback  # Rollback to previous version
GET /api/evolution/metrics    # Performance metrics
```

## Database Schema

### Key Tables
- `ideas` - Core idea storage with metadata
- `agents` - Agent registration and configuration
- `agent_activities` - Activity logging and performance
- `agent_messages` - Inter-agent communication
- `evolution_cycles` - Self-improvement history

### Database Access
```python
from backend.database import get_db, IdeaCRUD, AgentCRUD

with get_db() as db:
    ideas = IdeaCRUD.get_all_ideas(db)
    agents = AgentCRUD.get_all_agents(db)
```

## API Endpoints

### Core Endpoints
- `GET /` - System status and info
- `GET /api/health` - Health check
- `GET /api/ideas` - List ideas
- `POST /api/ideas` - Create new idea
- `GET /api/agents` - List agents
- `POST /api/agents/{id}/message` - Send message to agent

### WebSocket (`/ws`)
- Real-time updates for frontend
- Agent activity notifications
- Evolution progress updates

## Frontend Architecture

### Key Components
- `src/components/IdeaCapture.tsx` - Main idea input
- `src/components/AgentStatus.tsx` - Agent monitoring
- `src/components/Navbar.tsx` - Navigation with logo
- `src/pages/HomePage.tsx` - Main dashboard

### State Management
- **Zustand** for global state
- **Offline support** with IndexedDB
- **Real-time updates** via WebSocket

### PWA Features
- **Service Worker** for offline functionality
- **App manifest** for mobile installation
- **Push notifications** for agent updates

## Common Development Patterns

### Adding New Agents
1. Extend `BaseAgent` class
2. Implement `process()` method
3. Register in `agent_registry`
4. Add to database migrations

### Creating API Endpoints
1. Add to `backend/api/` directory
2. Include router in `main.py`
3. Add CRUD operations in `database/`
4. Update OpenAPI documentation

### Frontend Development
1. Use TypeScript for all components
2. Follow existing component patterns
3. Implement responsive design with Tailwind
4. Add proper error boundaries

## Testing

### Backend Tests
```bash
cd backend
python -m pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm run test
```

### Integration Tests
- API endpoint testing with FastAPI TestClient
- Agent communication testing
- Database integration testing

## Deployment

### Production Setup
```bash
# Build and deploy
docker-compose -f docker/docker-compose.yml up -d

# Check services
curl http://localhost:8000/api/health
curl http://localhost:3000
```

### Monitoring
- **Logs**: `docker-compose logs -f`
- **Metrics**: `/api/evolution/metrics`
- **Health**: `/api/health`

## Key Files to Understand

### Backend Core
- `backend/main.py` - FastAPI application setup
- `backend/database/models.py` - Database models
- `backend/agents/base_agent.py` - Agent base class
- `backend/services/evolution_service.py` - Self-improvement logic

### Frontend Core
- `frontend/src/App.tsx` - Main React app
- `frontend/src/stores/` - State management
- `frontend/vite.config.ts` - Build configuration

### Configuration
- `docker/docker-compose.yml` - Service orchestration
- `backend/requirements.txt` - Python dependencies
- `frontend/package.json` - Node.js dependencies

## Security Considerations

### API Security
- **CORS** configured for development
- **Input validation** on all endpoints
- **Secret management** via environment variables
- **Rate limiting** on critical endpoints

### Agent Security
- **Sandboxed execution** for code generation
- **Safe backup mechanism** for evolution
- **Error handling** prevents system crashes
- **Logging** for audit trails

## Performance Optimization

### Backend
- **Async processing** for all agents
- **Database connection pooling**
- **Redis caching** for frequent queries
- **Background tasks** for heavy operations

### Frontend
- **Code splitting** with Vite
- **Lazy loading** for components
- **Service Worker** for caching
- **Optimized bundle size**

## Troubleshooting

### Common Issues
1. **Agent not starting**: Check Redis connection
2. **Database errors**: Verify PostgreSQL is running
3. **API timeouts**: Check Claude AI API limits
4. **Frontend build fails**: Clear node_modules and reinstall

### Debug Commands
```bash
# View service logs
docker-compose -f docker/docker-compose.yml logs backend
docker-compose -f docker/docker-compose.yml logs frontend

# Check service health
curl http://localhost:8000/api/health
curl http://localhost:8000/api/agents

# Database connection
docker exec -it dreamcatcher-db psql -U dreamcatcher -d dreamcatcher
```

## Next Steps for Development

### High Priority
1. **Agent coordination improvements**
2. **Evolution strategy optimization**
3. **Real-time collaboration features**
4. **Mobile app optimization**

### Future Enhancements
1. **Multi-user support**
2. **Advanced AI model integration**
3. **Export/import functionality**
4. **Analytics dashboard**

## Important Notes

### Code Style
- **Python**: PEP 8 compliance, type hints
- **TypeScript**: Strict mode, proper interfaces
- **No comments** unless absolutely necessary
- **Consistent naming**: snake_case (Python), camelCase (TS)

### Development Workflow
1. **Always read existing code** before making changes
2. **Follow established patterns** in the codebase
3. **Test thoroughly** before committing
4. **Use the TodoWrite tool** for task management
5. **Check linting** before final commit

### Self-Improvement System
- **Monitor evolution cycles** regularly
- **Review performance metrics** after changes
- **Use rollback** if issues arise
- **Document evolution strategies** for future reference

This guide should help you quickly understand and contribute to the Dreamcatcher project. The system is designed to be self-improving, so expect continuous evolution and enhancement of capabilities.