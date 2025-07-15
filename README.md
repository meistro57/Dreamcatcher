# Dreamcatcher

*"Catch it. Grow it. Build it. From spark to system—without losing a beat."*

An AI-powered idea factory that captures, analyzes, and evolves your thoughts into reality. Built for neurodivergent creators who think faster than they can remember.

## Why Dreamcatcher Exists

Because it took me three tries just to get this idea to the AI who's going to build it for me. And by the third try, I almost forgot it. So I built a system that never forgets, never sleeps, and thinks about my ideas harder than I do.

## Core Concept

A 24/7 basement-hosted system that:
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
- **Deployment**: Docker on unitthirty2.com

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

1. Clone the repository
2. Set up environment variables
3. Start with Docker Compose
4. Configure AI API keys
5. Begin capturing ideas

## Features

- **Instant Voice Capture**: Record ideas in seconds
- **AI-Powered Analysis**: Automatic categorization and expansion
- **Visual Generation**: Context-aware image creation
- **Self-Improvement**: System evolves based on usage
- **Project Tracking**: From idea to implementation
- **Scheduled Reviews**: Resurrect forgotten brilliance

## Status

🚧 **In Development** - Phase 1: Foundation

The creative system you never had growing up—now designed for the way your mind actually works.

---

*Built with Claude Code • Hosted in the basement • Powered by midnight inspiration*
