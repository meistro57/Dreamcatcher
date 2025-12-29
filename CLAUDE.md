# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Local Development Setup
```bash
# Quick start with Docker (recommended)
./start-local.sh

# Native development (Python + Node.js)
./start-native.sh

# Reset local environment
./reset-local.sh

# Set up Python virtual environment
./setup-venv.sh
```

### Backend Development
```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Run server with hot reload
uvicorn main:app --reload

# Run tests
pytest
pytest backend/tests/test_semantic_search.py::TestEmbeddingService::test_generate_embedding  # Single test

# Run database migrations
python database/run_migrations.py

# Semantic search CLI
python cli/semantic_cli.py health
python cli/semantic_cli.py generate --batch-size 50
python cli/semantic_cli.py search "mobile app" --user-id user123
```

### Frontend Development
```bash
# Install dependencies
cd frontend
npm install

# Run development server
npm run dev

# Run tests
npm test

# Type checking
npm run type-check

# Linting
npm run lint
npm run lint:fix

# Build for production
npm run build
```

### Docker Development
```bash
# Start all services
docker-compose -f docker-compose.local.yml up -d

# View logs
docker-compose -f docker-compose.local.yml logs -f
docker-compose -f docker-compose.local.yml logs -f backend

# Stop services
docker-compose -f docker-compose.local.yml down

# Rebuild services
docker-compose -f docker-compose.local.yml build
```

## Architecture Overview

### Multi-Agent System
Dreamcatcher uses a sophisticated multi-agent architecture where each agent has a specific role and personality:

- **BaseAgent** (`backend/agents/base_agent.py`): All agents inherit from this class, providing message queue, logging, and database registration
- **Agent Registry** (`backend/agents/__init__.py`): Manages agent lifecycle and communication
- **Agent Communication**: Uses `AgentMessage` dataclass for structured inter-agent communication

### Database Architecture
- **SQLAlchemy ORM** with PostgreSQL backend
- **pgvector extension** for semantic search vector storage
- **Migration system** with `run_migrations.py` for schema changes
- **Connection pooling** with pre-ping for reliability

### Frontend State Management
- **Zustand** for global state management with persistence
- **Custom hooks** for WebSocket integration and notifications
- **API client** (`frontend/src/utils/api.ts`) with axios interceptors for auth

### Key Integration Points
- **WebSocket Manager** (`backend/api/websocket_manager.py`): Real-time communication
- **Agent-API Integration**: API endpoints trigger agent processing via message queues
- **Background Tasks**: Embedding generation and system health monitoring run continuously

## Important System Behaviors

### Agent Lifecycle
1. Agents auto-register with the system on initialization
2. Each agent has a message queue for async processing
3. Agent health is monitored via `/api/agents/{id}/status`
4. Agent communication uses correlation IDs for tracking

### Semantic Search System
- **Embedding Generation**: Uses sentence-transformers (`all-MiniLM-L6-v2`) for 384-dimensional vectors
- **Vector Storage**: pgvector extension with cosine similarity indexing
- **Background Processing**: `EmbeddingTaskManager` runs continuously to generate embeddings
- **Search Performance**: IVFFlat index on vector column for fast approximate search

### Authentication Flow
- **JWT-based authentication** with refresh tokens
- **Role-based access control** via `user_roles` table
- **Session management** with `UserSession` model for device tracking
- **API interceptors** automatically handle token refresh

### Evolution System (Critical)
- **Meta Agent** continuously monitors and improves the system
- **Never disable the Meta Agent** - it's responsible for autonomous evolution
- **Health scoring** triggers automatic improvements when health < 30%
- **Backup and rollback** mechanisms protect against failed evolution attempts

## Development Patterns

### Adding New Agents
1. Inherit from `BaseAgent` and implement required methods
2. Define agent personality and capabilities
3. Register with agent registry in `__init__.py`
4. Add appropriate API endpoints in `routes.py`

### Database Changes
1. Update SQLAlchemy models in `database/models.py`
2. Create migration SQL in `database/migrations/`
3. Run migrations with `python database/run_migrations.py`
4. Update corresponding API endpoints and tests

### Frontend Component Structure
- Use TypeScript for all components
- Implement proper error boundaries
- Use Zustand stores for state management
- Include loading states and error handling

## Testing Strategy

### Backend Tests
- **Unit tests**: Individual agent and service testing
- **Integration tests**: API endpoint testing with test database
- **Semantic search tests**: Embedding generation and similarity testing
- **Mock dependencies**: Use `conftest.py` fixtures for consistent mocking

### Frontend Tests
- **Component tests**: Use vitest for React component testing
- **Store tests**: Test Zustand state management
- **API tests**: Mock API responses for consistent testing

## Critical System Notes

### Never Modify
- **Meta Agent functionality** - handles system evolution
- **Base agent message queue system** - critical for agent communication
- **Database connection pooling** - optimized for production load

### Environment Variables
All required environment variables are documented in `.env.example` template:
- **AI Service API Keys** (at least one required):
  - `ANTHROPIC_API_KEY` - Direct access to Claude models
  - `OPENAI_API_KEY` - Direct access to OpenAI GPT models
  - `OPENROUTER_API_KEY` - Unified access to multiple LLM providers (Claude, GPT, Llama, Gemini, Mistral, etc.)
- `DATABASE_URL` and `REDIS_URL` for data persistence
- `SECRET_KEY` for JWT token signing

### Performance Considerations
- **Async/await patterns** used throughout for non-blocking operations
- **Connection pooling** configured for database efficiency
- **Vector indexing** optimized for semantic search performance
- **Background tasks** run continuously for system maintenance

## Troubleshooting

### Common Issues
- **Agent not responding**: Check logs and agent health status via API
- **Semantic search slow**: Monitor embedding coverage and batch processing
- **Database connection issues**: Verify PostgreSQL service and connection string
- **WebSocket disconnections**: Check WebSocket manager and Redis connectivity

### Debug Commands
```bash
# Check system health
curl http://localhost:8000/api/evolution/health

# Agent status
curl http://localhost:8000/api/agents/semantic/status

# Embedding statistics
curl http://localhost:8000/api/embeddings/stats

# Test semantic search
python backend/cli/semantic_cli.py test "fitness app" "health tracking"
```

---

*This system represents a living, breathing AI collective that continuously evolves to better serve the creative process.*