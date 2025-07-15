<div align="center">
  <img src="../Dreamcatcher_logo.png" alt="Dreamcatcher Logo" width="150" />
</div>

# Dreamcatcher API Documentation

*RESTful API for your AI-powered idea factory*

## Base URL

```
https://dreamcatcher.yourdomain.com/api
```

## Authentication

Most endpoints require authentication via JWT tokens:

```bash
Authorization: Bearer <your-jwt-token>
```

## Response Format

All responses follow this structure:

```json
{
  "success": true,
  "data": { ... },
  "message": "Optional message",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

Error responses:
```json
{
  "success": false,
  "error": "Error description",
  "code": "ERROR_CODE",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Endpoints

### Health Check

#### GET `/health`
Check system health and status.

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "database": "connected",
    "redis": "connected",
    "agents": {
      "listener": "active",
      "classifier": "active",
      "expander": "active",
      "visualizer": "active",
      "proposer": "active",
      "reviewer": "active"
    },
    "version": "1.0.0"
  }
}
```

### Idea Capture

#### POST `/capture/voice`
Submit voice recording for transcription and processing.

**Request:**
- Content-Type: `multipart/form-data`
- Body: Audio file (wav, mp3, m4a)

```bash
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -F "audio=@recording.wav" \
  https://dreamcatcher.yourdomain.com/api/capture/voice
```

**Response:**
```json
{
  "success": true,
  "data": {
    "idea_id": "uuid-here",
    "transcription": "Your transcribed text",
    "processing_status": "queued",
    "estimated_processing_time": "30s"
  }
}
```

#### POST `/capture/text`
Submit text idea directly.

**Request:**
```json
{
  "content": "Your idea text here",
  "source": "manual",
  "metadata": {
    "tags": ["optional", "tags"],
    "priority": "medium"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "idea_id": "uuid-here",
    "content": "Your idea text here",
    "processing_status": "queued"
  }
}
```

#### POST `/capture/dream`
Submit dream or subconscious idea.

**Request:**
```json
{
  "content": "Dream description",
  "dream_date": "2024-01-01T08:00:00Z",
  "lucidity_level": "high",
  "emotional_tone": "positive"
}
```

### Ideas Management

#### GET `/ideas`
Retrieve ideas with filtering and pagination.

**Query Parameters:**
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20)
- `category`: Filter by category
- `status`: Filter by processing status
- `search`: Full-text search
- `sort`: Sort by (created_at, urgency_score, novelty_score)
- `order`: Sort order (asc, desc)

**Response:**
```json
{
  "success": true,
  "data": {
    "ideas": [
      {
        "id": "uuid-here",
        "content_raw": "Original idea text",
        "content_transcribed": "Transcribed text",
        "category": "creative",
        "urgency_score": 85,
        "novelty_score": 92,
        "processing_status": "completed",
        "created_at": "2024-01-01T00:00:00Z",
        "tags": ["innovation", "urgent"],
        "expansions_count": 3,
        "visualizations_count": 2,
        "proposals_count": 1
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 150,
      "total_pages": 8
    }
  }
}
```

#### GET `/ideas/{idea_id}`
Get detailed information about a specific idea.

**Response:**
```json
{
  "success": true,
  "data": {
    "idea": {
      "id": "uuid-here",
      "content_raw": "Original idea text",
      "content_transcribed": "Transcribed text",
      "category": "creative",
      "urgency_score": 85,
      "novelty_score": 92,
      "processing_status": "completed",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:30:00Z",
      "tags": ["innovation", "urgent"],
      "expansions": [
        {
          "id": "expansion-uuid",
          "content": "Expanded idea content",
          "type": "claude",
          "created_at": "2024-01-01T00:10:00Z"
        }
      ],
      "visualizations": [
        {
          "id": "viz-uuid",
          "image_path": "/storage/images/idea-visualization.png",
          "prompt": "Visual prompt used",
          "type": "primary",
          "created_at": "2024-01-01T00:20:00Z"
        }
      ],
      "proposals": [
        {
          "id": "proposal-uuid",
          "title": "Project Proposal",
          "viability_score": 87,
          "status": "pending",
          "created_at": "2024-01-01T00:25:00Z"
        }
      ]
    }
  }
}
```

#### PUT `/ideas/{idea_id}`
Update an existing idea.

**Request:**
```json
{
  "content": "Updated idea content",
  "category": "business",
  "tags": ["updated", "business"],
  "metadata": {
    "notes": "Additional notes"
  }
}
```

#### DELETE `/ideas/{idea_id}`
Delete an idea and all related data.

**Response:**
```json
{
  "success": true,
  "message": "Idea deleted successfully"
}
```

### Expansions

#### GET `/ideas/{idea_id}/expansions`
Get all expansions for an idea.

#### POST `/ideas/{idea_id}/expansions`
Request new expansion for an idea.

**Request:**
```json
{
  "expansion_type": "creative",
  "focus": "technical implementation",
  "ai_model": "claude"
}
```

### Visualizations

#### GET `/ideas/{idea_id}/visualizations`
Get all visualizations for an idea.

#### POST `/ideas/{idea_id}/visualizations`
Request new visualization.

**Request:**
```json
{
  "style": "modern",
  "type": "concept",
  "prompt_override": "Optional custom prompt"
}
```

### Proposals

#### GET `/proposals`
Get all proposals with filtering.

**Query Parameters:**
- `status`: Filter by proposal status
- `viability_min`: Minimum viability score
- `sort`: Sort by (created_at, viability_score, priority_score)

**Response:**
```json
{
  "success": true,
  "data": {
    "proposals": [
      {
        "id": "uuid-here",
        "title": "Project Proposal Title",
        "idea_id": "idea-uuid",
        "viability_score": 87,
        "priority_score": 92,
        "status": "pending",
        "estimated_effort": "medium",
        "created_at": "2024-01-01T00:00:00Z",
        "timeline": {
          "total_duration": "3 months",
          "key_milestones": [...]
        }
      }
    ]
  }
}
```

#### GET `/proposals/{proposal_id}`
Get detailed proposal information.

#### PUT `/proposals/{proposal_id}`
Update proposal status or content.

**Request:**
```json
{
  "status": "approved",
  "notes": "Ready to proceed",
  "modifications": {
    "timeline": "Extended to 4 months"
  }
}
```

### Agents

#### GET `/agents`
Get status of all agents.

**Response:**
```json
{
  "success": true,
  "data": {
    "agents": [
      {
        "id": "listener",
        "name": "Capture Agent",
        "status": "active",
        "last_activity": "2024-01-01T00:00:00Z",
        "processed_today": 25,
        "performance_score": 98
      }
    ]
  }
}
```

#### POST `/agents/{agent_id}/trigger`
Manually trigger an agent process.

**Request:**
```json
{
  "action": "process",
  "data": {
    "idea_id": "uuid-here",
    "parameters": {}
  }
}
```

### Reviews

#### GET `/reviews`
Get review history and insights.

#### POST `/reviews/trigger`
Trigger manual review process.

**Request:**
```json
{
  "review_type": "daily",
  "strategy": "serendipity",
  "parameters": {
    "max_ideas": 5
  }
}
```

### Analytics

#### GET `/analytics/dashboard`
Get dashboard analytics data.

**Response:**
```json
{
  "success": true,
  "data": {
    "stats": {
      "total_ideas": 1250,
      "ideas_today": 8,
      "processing_rate": 0.95,
      "completion_rate": 0.87
    },
    "category_breakdown": {
      "creative": 45,
      "business": 30,
      "technical": 15,
      "personal": 10
    },
    "recent_activity": [...]
  }
}
```

### WebSocket Endpoints

#### `/ws/ideas`
Real-time idea processing updates.

**Connection:**
```javascript
const ws = new WebSocket('wss://dreamcatcher.yourdomain.com/api/ws/ideas');
```

**Message Format:**
```json
{
  "type": "idea_update",
  "data": {
    "idea_id": "uuid-here",
    "status": "processing",
    "stage": "expansion",
    "progress": 60
  }
}
```

#### `/ws/agents`
Real-time agent status updates.

## Rate Limits

- **API Endpoints**: 100 requests per minute
- **Voice Upload**: 10 requests per minute
- **WebSocket**: 1 connection per user

## Error Codes

- `INVALID_TOKEN`: Authentication failed
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INVALID_INPUT`: Request validation failed
- `PROCESSING_ERROR`: Internal processing error
- `AGENT_UNAVAILABLE`: Agent is offline
- `STORAGE_ERROR`: File storage issue

## SDK Examples

### JavaScript/Node.js

```javascript
import DreamcatcherAPI from 'dreamcatcher-sdk';

const api = new DreamcatcherAPI({
  baseURL: 'https://dreamcatcher.yourdomain.com/api',
  token: 'your-jwt-token'
});

// Capture text idea
const idea = await api.capture.text({
  content: 'New idea here',
  metadata: { priority: 'high' }
});

// Get idea details
const details = await api.ideas.get(idea.id);

// Request expansion
const expansion = await api.expansions.create(idea.id, {
  type: 'technical',
  ai_model: 'claude'
});
```

### Python

```python
from dreamcatcher_client import DreamcatcherClient

client = DreamcatcherClient(
    base_url="https://dreamcatcher.yourdomain.com/api",
    token="your-jwt-token"
)

# Capture voice idea
with open('recording.wav', 'rb') as audio_file:
    idea = client.capture.voice(audio_file)

# Get proposals
proposals = client.proposals.list(status='pending')

# Trigger review
review = client.reviews.trigger(
    review_type='daily',
    strategy='context_based'
)
```

### cURL Examples

```bash
# Health check
curl https://dreamcatcher.yourdomain.com/api/health

# Capture text idea
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"content": "New idea here"}' \
  https://dreamcatcher.yourdomain.com/api/capture/text

# Get ideas
curl -H "Authorization: Bearer <token>" \
  "https://dreamcatcher.yourdomain.com/api/ideas?category=creative&limit=10"

# Upload voice
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -F "audio=@recording.wav" \
  https://dreamcatcher.yourdomain.com/api/capture/voice
```

## Development

### Local Development

```bash
# Start development server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# API will be available at http://localhost:8000
# Documentation at http://localhost:8000/docs
```

### Testing

```bash
# Run API tests
pytest tests/api/

# Load testing
locust -f tests/load/locustfile.py --host=https://dreamcatcher.yourdomain.com
```

This API enables full control over your AI idea factory, allowing you to build custom interfaces, integrations, and automations around your creative process.

---

*API designed for developers who think in code and dream in possibilities.*