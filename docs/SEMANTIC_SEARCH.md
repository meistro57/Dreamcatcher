# Semantic Search Documentation

## Overview

Dreamcatcher's semantic search system provides intelligent idea discovery based on meaning and context rather than simple keyword matching. The system uses vector embeddings and similarity search to help users find related ideas, discover connections, and explore their creative space more effectively.

## Architecture

### Core Components

1. **Embedding Service** (`backend/services/embedding_service.py`)
   - Generates vector embeddings using sentence-transformers
   - Manages embedding storage and retrieval
   - Calculates similarity scores between ideas

2. **Semantic Agent** (`backend/agents/agent_semantic.py`)
   - Processes ideas for semantic understanding
   - Handles search queries and related idea discovery
   - Integrates with the existing agent ecosystem

3. **Vector Database** (PostgreSQL + pgvector)
   - Stores embeddings as vector arrays
   - Provides efficient similarity search
   - Optimized indexing for performance

4. **Background Tasks** (`backend/tasks/embedding_tasks.py`)
   - Automatic embedding generation for new ideas
   - Batch processing for large datasets
   - Health monitoring and maintenance

## Features

### 🔍 Semantic Search
- **Intelligent Query Processing**: Understands intent behind search queries
- **Context-Aware Results**: Finds ideas based on meaning, not just keywords
- **Configurable Similarity**: Adjustable thresholds for precision/recall balance
- **Real-time Results**: Fast vector similarity search with pgvector

### 🔗 Related Ideas
- **Automatic Discovery**: Finds conceptually similar ideas without manual linking
- **Dynamic Relationships**: Updates as new ideas are added
- **Configurable Sensitivity**: Adjustable similarity thresholds
- **Cross-Category Links**: Discovers connections across different idea categories

### 📊 Embedding Management
- **Automatic Generation**: New ideas get embeddings automatically
- **Batch Processing**: Efficient handling of large datasets
- **Model Versioning**: Track which embedding model was used
- **Coverage Monitoring**: Dashboard showing embedding coverage statistics

### ⚡ Performance Optimization
- **Vector Indexing**: Optimized database indexes for fast similarity search
- **Batch Operations**: Efficient processing of multiple embeddings
- **Background Processing**: Non-blocking embedding generation
- **Caching**: Intelligent caching of frequently accessed embeddings

## Technical Implementation

### Embedding Generation

The system uses the `all-MiniLM-L6-v2` model from sentence-transformers, which provides:
- **384-dimensional vectors** for compact storage
- **Balanced performance** between speed and accuracy
- **Multilingual support** for international users
- **Fine-tuned for semantic similarity** tasks

```python
# Example embedding generation
from services.embedding_service import embedding_service

# Generate embedding for text
embedding = await embedding_service.generate_embedding("Build a mobile app for fitness tracking")

# Calculate similarity between two texts
similarity = embedding_service.calculate_similarity(embedding1, embedding2)
```

### Database Schema

```sql
-- Ideas table with embedding columns
ALTER TABLE ideas ADD COLUMN content_embedding vector(384);
ALTER TABLE ideas ADD COLUMN embedding_model VARCHAR(255);
ALTER TABLE ideas ADD COLUMN embedding_updated_at TIMESTAMP WITH TIME ZONE;

-- Optimized index for similarity search
CREATE INDEX ideas_embedding_idx ON ideas USING ivfflat (content_embedding vector_cosine_ops);
```

### API Endpoints

#### Semantic Search
```http
GET /api/search/semantic?query=fitness+app&limit=10&threshold=0.5
```

#### Related Ideas
```http
GET /api/ideas/{idea_id}/related?limit=5&threshold=0.6
```

#### Embedding Management
```http
POST /api/ideas/{idea_id}/generate_embedding
POST /api/embeddings/batch_update
GET /api/embeddings/stats
```

## Frontend Integration

### SemanticSearch Component
```tsx
import SemanticSearch from '../components/semantic/SemanticSearch'

// Usage in a page component
<SemanticSearch 
  onResults={(results) => handleSearchResults(results)}
  className="w-full"
/>
```

### RelatedIdeas Component
```tsx
import RelatedIdeas from '../components/semantic/RelatedIdeas'

// Show related ideas for a specific idea
<RelatedIdeas 
  ideaId={currentIdea.id}
  className="mt-4"
/>
```

### EmbeddingStats Component
```tsx
import EmbeddingStats from '../components/semantic/EmbeddingStats'

// Display embedding statistics and management
<EmbeddingStats className="p-4" />
```

## CLI Management

The semantic search system includes a comprehensive CLI tool for management and maintenance:

```bash
# Check system health
python backend/cli/semantic_cli.py health

# Generate embeddings for all ideas
python backend/cli/semantic_cli.py generate --batch-size 50

# Search for similar ideas
python backend/cli/semantic_cli.py search "mobile app idea" --user-id user123

# Find related ideas
python backend/cli/semantic_cli.py related idea-456 --limit 10

# Get embedding statistics
python backend/cli/semantic_cli.py stats

# Test similarity between texts
python backend/cli/semantic_cli.py test "fitness app" "health tracking application"

# Benchmark search performance
python backend/cli/semantic_cli.py benchmark --queries 20
```

## Configuration

### Environment Variables
```env
# Embedding model configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# Performance settings
EMBEDDING_BATCH_SIZE=50
EMBEDDING_TASK_INTERVAL=300

# Database configuration
DATABASE_URL=postgresql://user:pass@localhost/dreamcatcher
```

### Model Selection

The system supports different embedding models:

1. **all-MiniLM-L6-v2** (default)
   - 384 dimensions
   - Fast inference
   - Good general performance

2. **all-mpnet-base-v2**
   - 768 dimensions
   - Higher accuracy
   - Slower inference

3. **all-distilroberta-v1**
   - 768 dimensions
   - Balanced performance
   - Good for English text

## Performance Considerations

### Embedding Generation
- **Batch Processing**: Process multiple ideas together for efficiency
- **Background Tasks**: Generate embeddings asynchronously
- **Model Caching**: Keep the embedding model in memory
- **GPU Acceleration**: Use GPU if available for faster processing

### Search Performance
- **Vector Indexing**: Use IVFFlat index for approximate nearest neighbor search
- **Query Optimization**: Optimize similarity queries with proper indexing
- **Result Caching**: Cache frequently accessed search results
- **Pagination**: Implement pagination for large result sets

### Storage Optimization
- **Vector Compression**: Use appropriate precision for embeddings
- **Index Tuning**: Optimize vector index parameters
- **Cleanup Tasks**: Remove outdated embeddings periodically
- **Monitoring**: Track storage usage and performance metrics

## Monitoring and Maintenance

### Health Metrics
- **Embedding Coverage**: Percentage of ideas with embeddings
- **Generation Rate**: Ideas processed per hour
- **Search Performance**: Average query response time
- **Error Rates**: Failed embedding generations
- **Model Performance**: Similarity accuracy metrics

### Maintenance Tasks
- **Batch Updates**: Regular embedding generation for new ideas
- **Model Updates**: Upgrade to newer embedding models
- **Index Rebuilding**: Rebuild vector indexes for performance
- **Cleanup**: Remove orphaned or outdated embeddings

### Troubleshooting

#### Common Issues

1. **Slow Search Performance**
   - Check vector index configuration
   - Monitor database performance
   - Consider index rebuilding

2. **Low Embedding Coverage**
   - Run batch embedding generation
   - Check background task status
   - Review error logs

3. **Poor Search Results**
   - Adjust similarity thresholds
   - Check embedding quality
   - Consider model upgrade

#### Debug Commands
```bash
# Check embedding health
curl http://localhost:8000/api/embeddings/stats

# View semantic agent logs
docker-compose logs -f app | grep semantic

# Test similarity calculation
python backend/cli/semantic_cli.py test "idea 1" "idea 2"

# Run health check
python backend/cli/semantic_cli.py health
```

## Future Enhancements

### Planned Features
- **Multi-modal Embeddings**: Support for image and audio embeddings
- **Custom Models**: Fine-tuned models for specific domains
- **Federated Search**: Search across multiple user collections
- **Semantic Clustering**: Automatic grouping of similar ideas
- **Query Expansion**: Enhanced search with related terms

### Performance Improvements
- **Approximate Search**: HNSW index for even faster search
- **Distributed Processing**: Multi-node embedding generation
- **Streaming Updates**: Real-time embedding updates
- **Compression**: Quantized embeddings for storage efficiency

## Security Considerations

### Data Privacy
- **User Isolation**: Embeddings are user-specific
- **Encryption**: Sensitive data encrypted at rest
- **Access Control**: Role-based access to embedding functions
- **Audit Logging**: Track embedding operations

### Performance Security
- **Rate Limiting**: Prevent abuse of search endpoints
- **Resource Limits**: Control embedding generation load
- **Input Validation**: Sanitize search queries
- **Model Security**: Secure embedding model storage

## Testing

### Unit Tests
- **Embedding Generation**: Test vector creation and storage
- **Similarity Calculation**: Verify similarity algorithms
- **Search Functionality**: Test query processing and results
- **Background Tasks**: Test async processing

### Integration Tests
- **End-to-End Search**: Complete search workflow
- **Agent Integration**: Semantic agent in agent ecosystem
- **Database Operations**: Vector storage and retrieval
- **API Endpoints**: REST API functionality

### Performance Tests
- **Search Benchmarks**: Query response time testing
- **Batch Processing**: Embedding generation performance
- **Scalability Tests**: Large dataset handling
- **Concurrent Users**: Multi-user search performance

## Contributing

### Development Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Run migrations: `python backend/database/run_migrations.py`
3. Generate test embeddings: `python backend/cli/semantic_cli.py generate`
4. Run tests: `pytest backend/tests/test_semantic_search.py`

### Code Style
- Follow existing project conventions
- Add type hints to all functions
- Document complex algorithms
- Write comprehensive tests

### Performance Guidelines
- Optimize for batch operations
- Use async/await for I/O operations
- Monitor memory usage with large datasets
- Profile embedding generation performance

---

*Semantic search makes idea discovery intelligent, helping users find connections they never knew existed.*