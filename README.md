# Dreamcatcher

*"Catch it. Grow it. Build it. From spark to system—without losing a beat."*

An AI-powered idea factory that captures, analyzes, and evolves your thoughts into reality. Built for neurodivergent creators who think faster than they can remember.

## Why Dreamcatcher Exists

Because it took me three tries just to get this idea to the AI who's going to build it for me. And by the third try, I almost forgot it. So I built a system that never forgets, never sleeps, and thinks about my ideas harder than I do.

## Core Concept

A 24/7 self-hosted system that:
- Captures raw creative energy the moment it strikes
- Uses AI agents to refine, connect, and expand ideas
- Generates visuals through ComfyUI integration
- Writes proposals and builds prototypes automatically
- Continuously improves itself using Claude Code

## Architecture Overview

### Data Layer
- PostgreSQL for idea storage and relationships
- Redis for real-time agent communication
- Vector database for semantic search
- File storage for audio/images

### Agent Network
- **Capture Agents**: Voice, text, dream input processing
- **Analysis Agents**: Classification, tagging, scoring
- **Expansion Agents**: Claude/GPT idea development
- **Visual Agents**: ComfyUI prompt generation
- **Project Agents**: Proposal writing, task creation
- **Review Agents**: Scheduled idea resurrection
- **Meta Agents**: Self-improvement and optimization

### Tech Stack
- **Backend**: FastAPI with WebSocket support
- **Frontend**: Mobile-first PWA (React/Vue)
- **AI Integration**: Claude, GPT, local models
- **Voice**: Whisper for transcription
- **Images**: ComfyUI for visual generation
- **Deployment**: Docker containerized deployment

## Project Structure

```
dreamcatcher/
├── backend/
│   ├── agents/
│   ├── api/
│   ├── database/
│   ├── services/
│   └── utils/
├── frontend/
│   ├── src/
│   ├── public/
│   └── dist/
├── docker/
├── docs/
└── tests/
```

## Getting Started

### Quick Deploy

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/dreamcatcher.git
   cd dreamcatcher
   ```

2. **Set your domain**
   ```bash
   export DOMAIN="yourdomain.com"
   export SUBDOMAIN="dreamcatcher"
   export EMAIL="admin@yourdomain.com"
   ```

3. **Deploy with one command**
   ```bash
   sudo ./deploy.sh
   ```

4. **Configure API keys**
   ```bash
   nano .env
   # Add your ANTHROPIC_API_KEY and OPENAI_API_KEY
   ```

5. **Start capturing ideas**
   - Visit `https://dreamcatcher.yourdomain.com`
   - Hit the voice button and speak your idea
   - Watch the AI agents process it in real-time

### Manual Setup

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed setup instructions.

## Features

- **Instant Voice Capture**: Record ideas in seconds
- **AI-Powered Analysis**: Automatic categorization and expansion
- **Visual Generation**: Context-aware image creation
- **Self-Improvement**: System evolves based on usage
- **Project Tracking**: From idea to implementation
- **Scheduled Reviews**: Resurrect forgotten brilliance

## Documentation

- **[Architecture](docs/ARCHITECTURE.md)** - Technical system design
- **[API Reference](docs/API.md)** - Complete API documentation
- **[Agent System](docs/AGENTS.md)** - AI personalities and capabilities
- **[Deployment Guide](DEPLOYMENT.md)** - Setup and configuration

## Status

✅ **Ready for Deployment** - Full system implementation complete

The creative system you never had growing up—now designed for the way your mind actually works.

---

*Built with Claude Code • Self-hosted anywhere • Powered by midnight inspiration*
