# Dreamcatcher Architecture

*The technical blueprint for your AI-powered idea factory*

## System Overview

Dreamcatcher is a distributed AI agent system designed to capture, process, and evolve ideas in real-time. The architecture supports instant voice capture, intelligent processing, visual generation, and continuous improvement.

## Core Components

### 1. Data Layer

**PostgreSQL Database**
- Primary storage for ideas, expansions, proposals, and metadata
- ACID compliance for data integrity
- Full-text search capabilities
- Relationship modeling between ideas and agents

**Redis Cache**
- Agent-to-agent communication
- Real-time message queuing
- Session management
- Performance optimization

**File Storage**
- Audio recordings (voice capture)
- Generated images (ComfyUI output)
- Agent logs and metrics
- Backup and archival data

### 2. Agent Network

**Base Agent Framework** (`backend/agents/base_agent.py`)
- Abstract base class for all agents
- Message routing and communication
- Performance tracking and logging
- Error handling and recovery

**Agent Pipeline:**

1. **Listener Agent** (`agent_listener.py`)
   - Voice/text/dream capture
   - Whisper integration for transcription
   - Input validation and preprocessing

2. **Classifier Agent** (`agent_classifier.py`)
   - AI-powered categorization
   - Urgency and novelty scoring
   - Tag assignment and metadata extraction

3. **Expander Agent** (`agent_expander.py`)
   - Claude/GPT integration for idea development
   - Category-specific expansion strategies
   - Multiple perspective generation

4. **Visualizer Agent** (`agent_visualizer.py`)
   - ComfyUI integration for image generation
   - Style-aware prompt engineering
   - Visual variation creation

5. **Proposer Agent** (`agent_proposer.py`)
   - Viability analysis and scoring
   - Structured proposal generation
   - Timeline and resource planning

6. **Reviewer Agent** (`agent_reviewer.py`)
   - Scheduled idea resurrection
   - Context-aware relevance scoring
   - Pattern-based recommendations

### 3. API Layer

**FastAPI Backend** (`backend/api/`)
- RESTful API endpoints
- WebSocket support for real-time updates
- Authentication and authorization
- Rate limiting and security

**Key Endpoints:**
- `/api/capture/voice` - Voice recording upload
- `/api/capture/text` - Text idea submission
- `/api/ideas` - Idea management
- `/api/proposals` - Proposal access
- `/api/agents` - Agent status and control
- `/api/health` - System health monitoring

### 4. Frontend Layer

**Mobile-First PWA** (`frontend/`)
- React/TypeScript with Vite
- Zustand for state management
- Tailwind CSS for styling
- Service Worker for offline capability

**Key Features:**
- Instant voice capture button
- Real-time idea streaming
- Offline-first architecture
- Push notifications for agent updates

## Data Flow

### Idea Capture Flow
```
User Input → Listener Agent → Classifier Agent → Expander Agent → Visualizer Agent → Proposer Agent
```

### Review Flow
```
Reviewer Agent → Assessment → Action Execution → Pipeline Re-entry
```

### Storage Flow
```
Agent Processing → Database Write → Redis Cache → Frontend Update
```

## Communication Patterns

### Agent-to-Agent Messaging
- Redis pub/sub for real-time communication
- Message queuing with retry logic
- Event-driven processing pipeline
- Asynchronous task execution

### Frontend-Backend Communication
- WebSocket for real-time updates
- REST API for CRUD operations
- Progressive Web App for offline support
- Service Worker for background sync

## Deployment Architecture

### Container Structure
```
nginx (reverse proxy)
├── frontend (React PWA)
├── backend (FastAPI)
├── scheduler (Agent coordinator)
├── postgres (Database)
└── redis (Cache/Queue)
```

### Network Configuration
- External: 443 (HTTPS), 80 (HTTP redirect)
- Internal: Docker bridge network
- SSL termination at nginx layer
- Rate limiting and security headers

## Security Model

### Authentication
- JWT-based session management
- API key authentication for agents
- Rate limiting per endpoint
- Input validation and sanitization

### Data Protection
- End-to-end encryption for sensitive data
- Local storage of all personal information
- Secure API key management
- Regular security updates

### Network Security
- HTTPS enforced for all connections
- Security headers (CSP, HSTS, etc.)
- Firewall configuration
- SSL certificate auto-renewal

## Scalability Design

### Horizontal Scaling
- Multiple backend instances
- Load balancing with nginx
- Agent distribution across containers
- Database connection pooling

### Performance Optimization
- Redis caching for frequent queries
- Async processing for long-running tasks
- Background job queuing
- Resource monitoring and alerting

### Storage Scaling
- Partitioned database tables
- File storage optimization
- Backup and archival strategies
- Metrics collection and analysis

## Monitoring and Observability

### Health Monitoring
- Application health endpoints
- Container health checks
- Database connection monitoring
- Agent performance tracking

### Logging
- Structured logging with JSON format
- Log aggregation and rotation
- Error tracking and alerting
- Performance metrics collection

### Metrics Collection
- System performance metrics
- Agent processing statistics
- User interaction analytics
- Resource utilization tracking

## AI Integration

### Claude Integration
- Anthropic API for idea expansion
- Structured prompt engineering
- Response parsing and validation
- Rate limiting and error handling

### OpenAI Integration
- GPT models for alternative perspectives
- Whisper for voice transcription
- Fallback processing capabilities
- Cost optimization strategies

### ComfyUI Integration
- Local image generation
- Workflow automation
- Style template management
- Queue processing and monitoring

## Development Patterns

### Code Organization
- Modular agent design
- Service layer abstraction
- Database access patterns
- Configuration management

### Testing Strategy
- Unit tests for agent logic
- Integration tests for API endpoints
- End-to-end tests for user flows
- Performance testing for scalability

### Deployment Strategy
- Docker containerization
- Infrastructure as Code
- Automated deployment scripts
- Health check monitoring

## Future Enhancements

### Self-Improvement System
- Claude Code integration for system evolution
- Automated code generation and testing
- Performance optimization recommendations
- Feature development suggestions

### Advanced AI Features
- Vector similarity search
- Semantic idea clustering
- Predictive idea suggestions
- Conversation memory integration

### Integration Capabilities
- Third-party service connections
- API ecosystem development
- Plugin architecture
- External tool integration

## Technical Specifications

### System Requirements
- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 20GB minimum, SSD preferred
- **Network**: Stable internet for AI APIs

### Dependencies
- **Python**: 3.9+
- **Node.js**: 18+
- **Docker**: 20.10+
- **PostgreSQL**: 15+
- **Redis**: 7+

### Environment Variables
```bash
# Core Configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/dreamcatcher
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key

# AI APIs
ANTHROPIC_API_KEY=your-claude-key
OPENAI_API_KEY=your-openai-key
COMFY_API_URL=http://localhost:8188

# Domain Setup
DOMAIN=yourdomain.com
SUBDOMAIN=dreamcatcher
SSL_EMAIL=admin@yourdomain.com
```

This architecture enables a robust, scalable, and maintainable AI idea factory that can grow with your creative needs while maintaining performance and reliability.

---

*Architecture designed for the way creative minds actually work - fast, interconnected, and always evolving.*