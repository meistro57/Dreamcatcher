# Dreamcatcher Backend

The AI-powered engine that never sleeps, never forgets, and thinks about your ideas harder than you do.

## Quick Start

```bash
# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Install dependencies
pip install -r requirements.txt

# Start the backend
python main.py
```

## Architecture

### Core Components

- **FastAPI Server**: RESTful API and WebSocket endpoints
- **Agent System**: Autonomous AI workers for idea processing
- **Database Layer**: PostgreSQL for persistence, Redis for real-time
- **AI Integration**: Claude, GPT, and local model connections

### Agent Network

Each agent is a specialized worker focused on one aspect of idea processing:

- `agent_listener.py` - Captures and logs raw input
- `agent_classifier.py` - Tags and categorizes ideas
- `agent_expander.py` - Uses Claude/GPT to develop concepts
- `agent_visualizer.py` - Generates ComfyUI prompts
- `agent_proposer.py` - Creates project proposals
- `agent_reviewer.py` - Scheduled idea resurrection
- `agent_meta.py` - Self-improvement and optimization

### API Endpoints

```
POST /api/capture/voice    - Upload voice recording
POST /api/capture/text     - Submit text idea
GET  /api/ideas           - Retrieve ideas with filters
GET  /api/proposals       - Get generated proposals
WS   /api/ws              - Real-time updates
```

## Environment Variables

```env
# AI API Keys
ANTHROPIC_API_KEY=your_claude_key
OPENAI_API_KEY=your_gpt_key

# Database
DATABASE_URL=postgresql://user:pass@localhost/dreamcatcher
REDIS_URL=redis://localhost:6379

# ComfyUI
COMFY_API_URL=http://localhost:8188

# Security
SECRET_KEY=your_secret_key
```

## Development

### Running Tests
```bash
pytest tests/
```

### Adding New Agents
1. Create agent in `agents/` directory
2. Inherit from `BaseAgent`
3. Implement `process()` method
4. Register in `agent_registry.py`

### Database Migrations
```bash
alembic upgrade head
```

## Status

🚧 **Phase 1**: Core infrastructure and basic capture
📋 **Next**: AI integration and agent communication

---

*The basement never sleeps. Neither does this code.*