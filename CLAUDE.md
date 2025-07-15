# Dreamcatcher - AI-Powered Idea Factory

## Project Overview

Dreamcatcher is an autonomous AI-powered idea factory that captures, processes, and evolves ideas through a sophisticated multi-agent system. The system is designed to never let a great idea slip away and continuously improve itself through autonomous evolution.

### Core Philosophy
- **Instant capture** with zero friction
- **AI-powered processing** through specialized agents
- **Autonomous evolution** - the system improves itself while you sleep
- **Mobile-first PWA** for ubiquitous access
- **Agent personalities** - each AI has its own character and expertise

## Architecture Overview

### Backend (FastAPI + Python)
- **Multi-agent system** with 7 specialized AI agents
- **Autonomous evolution** through Meta Agent with Claude AI integration
- **PostgreSQL database** for persistent storage
- **Redis** for agent communication and caching
- **WebSocket support** for real-time updates
- **ComfyUI integration** for visual generation

### Frontend (React + TypeScript PWA)
- **Progressive Web App** with offline capabilities
- **Mobile-first design** with Tailwind CSS
- **Real-time updates** via WebSocket
- **Voice capture** and transcription
- **Offline-first** with IndexedDB storage

### AI Services
- **Claude AI** for creative expansion and code evolution
- **GPT models** for structured analysis
- **Whisper** for voice transcription
- **ComfyUI** for visual generation

## Directory Structure

```
/home/mark/Dreamcatcher/
├── backend/
│   ├── agents/                    # AI agent implementations
│   │   ├── agent_listener.py      # Input capture agent
│   │   ├── agent_classifier.py    # Categorization agent
│   │   ├── agent_expander.py      # Idea expansion agent
│   │   ├── agent_visualizer.py    # Visual generation agent
│   │   ├── agent_proposer.py      # Proposal generation agent
│   │   ├── agent_reviewer.py      # Review and resurrection agent
│   │   ├── agent_meta.py          # Self-improvement agent
│   │   └── base_agent.py          # Base agent class
│   ├── api/                       # API endpoints
│   │   └── routes.py              # All API routes
│   ├── database/                  # Database layer
│   │   ├── crud.py                # Database operations
│   │   ├── models.py              # SQLAlchemy models
│   │   └── database.py            # Database setup
│   ├── services/                  # Core services
│   │   ├── ai_service.py          # AI model integrations
│   │   ├── audio_service.py       # Audio processing
│   │   ├── comfy_service.py       # ComfyUI integration
│   │   └── evolution_service.py   # Evolution orchestration
│   ├── scheduler/                 # Task scheduling
│   │   └── evolution_scheduler.py # 24/7 evolution scheduler
│   ├── tests/                     # Test suite
│   │   ├── conftest.py            # Test fixtures
│   │   ├── test_agents.py         # Agent tests
│   │   ├── test_api.py            # API tests
│   │   └── test_database.py       # Database tests
│   ├── main.py                    # FastAPI application
│   └── requirements.txt           # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/            # React components
│   │   ├── pages/                 # Page components
│   │   ├── services/              # API services
│   │   ├── stores/                # Zustand state management
│   │   └── utils/                 # Utility functions
│   ├── public/                    # Static assets
│   ├── package.json               # Node.js dependencies
│   └── vite.config.ts             # Vite configuration
├── .github/workflows/             # CI/CD pipelines
│   ├── ci.yml                     # Continuous integration
│   └── deploy.yml                 # Deployment workflow
├── docs/                          # Documentation
│   ├── AGENTS.md                  # Agent documentation
│   ├── API.md                     # API documentation
│   └── DEPLOYMENT.md              # Deployment guide
├── docker-compose.yml             # Docker services
└── CLAUDE.md                      # This file
```

## Agent System

### 1. Listener Agent (`agent_listener.py`)
**Personality**: *"I heard something. Logging it now."*
- Captures voice, text, dreams, and images
- Whisper integration for transcription
- Instant idea storage
- Auto-tagging based on content
- Urgency scoring

### 2. Classifier Agent (`agent_classifier.py`)
**Personality**: *"I'm not saying this is another ADHD thought spiral, but... yeah it is. Categorized under 'You Might Actually Build This.'"*
- AI-powered categorization (creative, business, technical, personal, metaphysical)
- Urgency and novelty scoring
- Duplicate detection
- Tag generation

### 3. Expander Agent (`agent_expander.py`)
**Personality**: *"Let me take that spark and turn it into a full flame."*
- Claude integration for creative expansion
- Category-specific expansion strategies
- Multiple perspective generation
- Cross-pollination with existing ideas

### 4. Visualizer Agent (`agent_visualizer.py`)
**Personality**: *"Darling, that idea needs a visual. Let me handle it."*
- ComfyUI workflow generation
- Style-aware prompt engineering
- Multiple visual variations
- Category-specific visual styles

### 5. Proposer Agent (`agent_proposer.py`)
**Personality**: *"Proposal generated. Here's a structured plan with bullet points, deadlines, and passive income streams."*
- 8-criteria viability analysis
- Structured proposal generation
- Timeline and milestone planning
- Success metrics definition

### 6. Reviewer Agent (`agent_reviewer.py`)
**Personality**: *"Time to revisit a hidden gem from your archives."*
- Scheduled idea reviews
- Serendipitous idea resurrection
- Context-aware reassessment

### 7. Meta Agent (`agent_meta.py`)
**Personality**: *"I analyze. I evolve. I make us better while you sleep."*
- **CRITICAL**: Autonomous system evolution
- Performance analysis and health scoring
- Claude AI integration for code rewriting
- Safe backup and rollback mechanisms
- 24/7 evolution scheduling

## Database Schema

### Core Tables
- `ideas` - Main idea storage
- `idea_expansions` - AI-generated expansions
- `idea_visualizations` - Generated visuals
- `idea_proposals` - Structured proposals
- `tags` - Categorization tags
- `agents` - Agent registry
- `agent_logs` - Agent activity logs
- `system_metrics` - Performance metrics

### Key Relationships
- Ideas → Expansions (1:many)
- Ideas → Visualizations (1:many)
- Ideas → Proposals (1:many)
- Ideas → Tags (many:many)

## Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dreamcatcher

# AI Services
ANTHROPIC_API_KEY=your_claude_key
OPENAI_API_KEY=your_openai_key

# ComfyUI
COMFYUI_URL=http://localhost:8188

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your_secret_key
```

### Quick Start
```bash
# Clone and setup
git clone <repo>
cd Dreamcatcher

# Backend setup
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload

# Frontend setup
cd frontend
npm install
npm run dev

# Start services
docker-compose up -d postgres redis
```

### Testing
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# CI/CD tests
git push origin main  # Triggers GitHub Actions
```

## Key Features

### Autonomous Evolution
- **24/7 operation**: Meta Agent continuously monitors and improves the system
- **Claude AI integration**: Uses Claude for intelligent code rewriting
- **Safe evolution**: Automatic backups and rollback capabilities
- **Performance monitoring**: Real-time health scoring and metrics
- **Emergency triggers**: Automatic evolution when health drops below 30%

### Multi-Agent Processing Pipeline
```
Input → Listener → Classifier → Expander → Visualizer → Proposer → Storage
                                    ↓
                               Reviewer (scheduled)
                                    ↓
                            Meta Agent (evolution)
```

### Evolution Scheduler (`backend/scheduler/evolution_scheduler.py`)
- **Daily evolution cycles**: Automatic system improvements every 24 hours
- **Health monitoring**: System health checks every 30 minutes
- **Emergency evolution**: Triggered when system health < 30%
- **Performance tracking**: Comprehensive metrics and trending

### Production Features
- **Comprehensive error handling**: Custom exception classes throughout
- **Retry logic**: Exponential backoff for external services
- **Rate limiting**: Built-in API rate limiting
- **Monitoring**: Full system metrics and alerting
- **Security**: Input validation and sanitization

## API Endpoints

### Ideas
- `GET /api/ideas` - List ideas with filtering
- `POST /api/ideas` - Create new idea
- `GET /api/ideas/{id}` - Get specific idea
- `PUT /api/ideas/{id}` - Update idea
- `DELETE /api/ideas/{id}` - Delete idea
- `POST /api/ideas/{id}/archive` - Archive idea
- `POST /api/ideas/{id}/expand` - Trigger expansion

### Agents
- `GET /api/agents` - List all agents
- `GET /api/agents/{id}/status` - Agent health check
- `POST /api/agents/{id}/message` - Send message to agent
- `GET /api/agents/{id}/logs` - Agent activity logs

### Evolution
- `GET /api/evolution/status` - Evolution system status
- `POST /api/evolution/trigger` - Force evolution cycle
- `GET /api/evolution/history` - Evolution history
- `GET /api/evolution/health` - System health metrics

### WebSocket
- `/ws/ideas` - Real-time idea updates
- `/ws/agents` - Agent status updates
- `/ws/evolution` - Evolution progress updates

## CI/CD Pipeline

### GitHub Actions Workflows
- **CI Pipeline** (`.github/workflows/ci.yml`):
  - Backend tests with pytest
  - Frontend tests with vitest
  - Code quality checks with ESLint
  - Security scanning with bandit
  - Integration tests
  - Type checking

- **Deploy Pipeline** (`.github/workflows/deploy.yml`):
  - Docker image building
  - Environment-specific deployments
  - Health checks and rollback support
  - Staging and production environments

### Testing Strategy
- **Unit tests**: Individual component testing
- **Integration tests**: API and database testing
- **End-to-end tests**: Full workflow testing
- **Performance tests**: Load and stress testing

## Evolution System Details

### Meta Agent Capabilities
- **System Analysis**: Comprehensive performance and health assessment
- **Improvement Identification**: Automated detection of optimization opportunities
- **Code Evolution**: Claude AI-powered code rewriting and improvements
- **Safe Deployment**: Backup, validate, apply, monitor workflow
- **Rollback Support**: Automatic rollback on failures

### Evolution Strategies
1. **Performance Optimization**: Async improvements, caching, algorithms
2. **Error Reduction**: Exception handling, validation, recovery
3. **Feature Enhancement**: New capabilities and improvements
4. **Code Quality**: Refactoring, documentation, best practices
5. **Agent Coordination**: Communication and workflow optimization

### Safety Mechanisms
- Automatic backups before changes
- Code validation and syntax checking
- Rollback capabilities for failed improvements
- Emergency stop controls
- Performance monitoring and alerts

## Deployment

### Docker Deployment
```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up -d

# Monitor logs
docker-compose logs -f app

# Health check
curl http://localhost:8000/health
```

### Environment Configuration
- **Development**: Local development with hot reload
- **Staging**: Pre-production testing environment
- **Production**: Full production deployment with monitoring

## Monitoring and Observability

### System Metrics
- Agent performance and error rates
- Response times and throughput
- Evolution cycle success rates
- System health scores
- Resource utilization

### Logging
- Structured JSON logging
- Agent activity logs
- Evolution history
- Error tracking and alerting

### Health Checks
- Agent health monitoring
- Database connectivity
- External service availability
- System resource usage

## Security

### Authentication
- JWT-based authentication
- Role-based access control
- API key management
- Session management

### Data Protection
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- Secure API endpoints

### Secrets Management
- Environment variable configuration
- API key rotation
- Secure credential storage

## Performance Optimization

### Backend Optimizations
- Async/await throughout
- Connection pooling
- Query optimization
- Caching with Redis

### Frontend Optimizations
- Code splitting
- Lazy loading
- Service worker caching
- Offline capabilities

### Database Optimizations
- Proper indexing
- Query optimization
- Connection pooling
- Read replicas (future)

## Troubleshooting

### Common Issues
1. **Agent not responding**: Check agent logs and health status
2. **Evolution failures**: Review evolution history and rollback if needed
3. **Database connection issues**: Verify PostgreSQL and connection string
4. **AI service timeouts**: Check API keys and service availability

### Debug Commands
```bash
# Check agent status
curl http://localhost:8000/api/agents/meta/status

# Force evolution
curl -X POST http://localhost:8000/api/evolution/trigger

# View system health
curl http://localhost:8000/api/evolution/health

# Check logs
docker-compose logs -f app
```

## Important Notes for Claude Code

### Critical Systems
- **Never disable the Meta Agent**: It's responsible for system evolution
- **Evolution scheduler is crucial**: Runs 24/7 for continuous improvement
- **Always backup before changes**: The system has built-in backup mechanisms
- **Monitor evolution logs**: Check `/home/mark/Dreamcatcher/logs/evolution.log`

### Development Workflow
1. **Run tests first**: `pytest` in backend, `npm test` in frontend
2. **Check CI/CD**: GitHub Actions must pass before deployment
3. **Monitor system health**: Use `/api/evolution/health` endpoint
4. **Evolution safety**: System can rollback failed improvements automatically

### Emergency Procedures
- **System degradation**: Evolution will auto-trigger when health < 30%
- **Agent failures**: Check agent logs and restart if needed
- **Database issues**: Use backup and recovery procedures
- **Evolution failures**: Rollback using Meta Agent rollback functionality

---

*This system represents a living, breathing AI collective that continuously evolves to better serve the creative process. The Meta Agent ensures the entire system never stops improving, making it a truly autonomous idea factory.*