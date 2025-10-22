"""
Test suite for semantic search functionality
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import numpy as np

from services.embedding_service import EmbeddingService
from agents.agent_semantic import SemanticAgent
from database.models import Idea, User
from tasks.embedding_tasks import EmbeddingTaskManager


class TestEmbeddingService:
    """Test embedding service functionality"""
    
    @pytest.fixture
    def embedding_service(self):
        """Create embedding service instance"""
        return EmbeddingService("all-MiniLM-L6-v2")
    
    @pytest.fixture
    def mock_model(self):
        """Mock sentence transformer model"""
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([0.1, 0.2, 0.3])
        return mock_model
    
    @pytest.mark.asyncio
    async def test_generate_embedding(self, embedding_service, mock_model):
        """Test embedding generation"""
        embedding_service.model = mock_model
        
        text = "This is a test idea"
        embedding = await embedding_service.generate_embedding(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 3
        assert embedding == [0.1, 0.2, 0.3]
        mock_model.encode.assert_called_once_with(text)
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_batch(self, embedding_service, mock_model):
        """Test batch embedding generation"""
        embedding_service.model = mock_model
        mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
        
        texts = ["First idea", "Second idea"]
        embeddings = await embedding_service.generate_embeddings_batch(texts)
        
        assert isinstance(embeddings, list)
        assert len(embeddings) == 2
        assert embeddings[0] == [0.1, 0.2, 0.3]
        assert embeddings[1] == [0.4, 0.5, 0.6]
        mock_model.encode.assert_called_once_with(texts)
    
    def test_calculate_similarity(self, embedding_service):
        """Test similarity calculation"""
        emb1 = [1.0, 0.0, 0.0]
        emb2 = [0.0, 1.0, 0.0]
        emb3 = [1.0, 0.0, 0.0]
        
        # Test dissimilar embeddings
        similarity = embedding_service.calculate_similarity(emb1, emb2)
        assert 0.0 <= similarity <= 1.0
        assert similarity < 0.7  # Should be relatively low
        
        # Test identical embeddings
        similarity = embedding_service.calculate_similarity(emb1, emb3)
        assert similarity > 0.9  # Should be very high
    
    @pytest.mark.asyncio
    async def test_update_idea_embedding(self, embedding_service, mock_model):
        """Test updating idea embedding"""
        embedding_service.model = mock_model
        
        with patch('backend.services.embedding_service.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            mock_idea = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = mock_idea
            
            idea_id = "test-idea-123"
            content = "Test idea content"
            
            result = await embedding_service.update_idea_embedding(idea_id, content)
            
            assert result is True
            assert mock_idea.content_embedding == [0.1, 0.2, 0.3]
            assert mock_idea.embedding_model == "all-MiniLM-L6-v2"
            assert mock_idea.embedding_updated_at is not None
            mock_db.commit.assert_called_once()


class TestSemanticAgent:
    """Test semantic agent functionality"""
    
    @pytest.fixture
    def semantic_agent(self):
        """Create semantic agent instance"""
        return SemanticAgent()
    
    @pytest.mark.asyncio
    async def test_process_idea_success(self, semantic_agent):
        """Test successful idea processing"""
        idea_id = "test-idea-123"
        
        with patch('backend.agents.agent_semantic.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            mock_idea = MagicMock()
            mock_idea.content_processed = "Test idea content"
            mock_db.query.return_value.filter.return_value.first.return_value = mock_idea
            
            with patch.object(semantic_agent.embedding_service, 'update_idea_embedding', return_value=True):
                with patch.object(semantic_agent.embedding_service, 'find_related_ideas', return_value=[]):
                    result = await semantic_agent.process_idea(idea_id)
            
            assert result['success'] is True
            assert result['embedding_generated'] is True
            assert 'related_ideas' in result
    
    @pytest.mark.asyncio
    async def test_search_similar_ideas(self, semantic_agent):
        """Test semantic search functionality"""
        query = "test query"
        user_id = "user-123"
        
        mock_results = [
            {
                'id': 'idea-1',
                'content_processed': 'Similar idea content',
                'similarity_score': 0.85
            }
        ]
        
        with patch.object(semantic_agent.embedding_service, 'search_similar_ideas', return_value=mock_results):
            result = await semantic_agent.search_similar_ideas(query, user_id)
        
        assert result['success'] is True
        assert result['results'] == mock_results
        assert result['query'] == query
        assert result['total_results'] == 1
    
    @pytest.mark.asyncio
    async def test_find_related_ideas(self, semantic_agent):
        """Test finding related ideas"""
        idea_id = "test-idea-123"
        
        mock_related = [
            {
                'id': 'related-idea-1',
                'content_processed': 'Related content',
                'similarity_score': 0.75
            }
        ]
        
        with patch.object(semantic_agent.embedding_service, 'find_related_ideas', return_value=mock_related):
            result = await semantic_agent.find_related_ideas(idea_id)
        
        assert result['success'] is True
        assert result['related_ideas'] == mock_related
        assert result['total_found'] == 1
    
    @pytest.mark.asyncio
    async def test_batch_update_embeddings(self, semantic_agent):
        """Test batch embedding updates"""
        batch_size = 10
        
        with patch.object(semantic_agent.embedding_service, 'batch_update_embeddings', return_value=5):
            result = await semantic_agent.batch_update_embeddings(batch_size)
        
        assert result['success'] is True
        assert result['updated_count'] == 5
    
    @pytest.mark.asyncio
    async def test_process_message_actions(self, semantic_agent):
        """Test message processing for different actions"""
        # Test process_idea action
        message = {
            'action': 'process_idea',
            'idea_id': 'test-idea-123'
        }
        
        with patch.object(semantic_agent, 'process_idea', return_value={'success': True}):
            result = await semantic_agent.process_message(message)
        
        assert result['success'] is True
        
        # Test search_similar action
        message = {
            'action': 'search_similar',
            'query': 'test query',
            'user_id': 'user-123'
        }
        
        with patch.object(semantic_agent, 'search_similar_ideas', return_value={'success': True}):
            result = await semantic_agent.process_message(message)
        
        assert result['success'] is True
        
        # Test unknown action
        message = {
            'action': 'unknown_action'
        }
        
        result = await semantic_agent.process_message(message)
        
        assert result['success'] is False
        assert 'Unknown action' in result['error']


class TestEmbeddingTaskManager:
    """Test embedding task manager"""
    
    @pytest.fixture
    def task_manager(self):
        """Create task manager instance"""
        return EmbeddingTaskManager()
    
    @pytest.mark.asyncio
    async def test_get_pending_ideas(self, task_manager):
        """Test getting pending ideas"""
        with patch('backend.tasks.embedding_tasks.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            mock_idea = MagicMock()
            mock_idea.id = "test-idea-123"
            mock_idea.content_processed = "Test content"
            mock_idea.user_id = "user-123"
            mock_idea.category = "creative"
            mock_idea.created_at = datetime.utcnow()
            mock_idea.updated_at = datetime.utcnow()
            
            mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_idea]
            
            pending_ideas = await task_manager.get_pending_ideas()
            
            assert len(pending_ideas) == 1
            assert pending_ideas[0]['id'] == "test-idea-123"
            assert pending_ideas[0]['content'] == "Test content"
    
    @pytest.mark.asyncio
    async def test_process_batch(self, task_manager):
        """Test batch processing"""
        batch = [
            {
                'id': 'idea-1',
                'content': 'Content 1',
                'user_id': 'user-123'
            },
            {
                'id': 'idea-2',
                'content': 'Content 2',
                'user_id': 'user-123'
            }
        ]
        
        with patch('backend.tasks.embedding_tasks.semantic_agent') as mock_agent:
            mock_agent.process_idea.return_value = {'success': True}
            
            await task_manager.process_batch(batch)
            
            assert mock_agent.process_idea.call_count == 2
            mock_agent.process_idea.assert_any_call('idea-1')
            mock_agent.process_idea.assert_any_call('idea-2')
    
    @pytest.mark.asyncio
    async def test_get_embedding_health(self, task_manager):
        """Test embedding health check"""
        with patch('backend.tasks.embedding_tasks.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock query results
            mock_db.query.return_value.filter.return_value.count.side_effect = [100, 80, 10, 5]
            
            health = await task_manager.get_embedding_health()
            
            assert health['status'] == 'healthy'
            assert health['total_ideas'] == 100
            assert health['ideas_with_embeddings'] == 80
            assert health['pending_ideas'] == 10
            assert health['coverage_percentage'] == 80.0
            assert health['recent_updates_24h'] == 5
            assert 'last_check' in health


class TestSemanticSearchIntegration:
    """Integration tests for semantic search"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_search_flow(self):
        """Test complete search flow"""
        # This would be a more comprehensive integration test
        # that tests the entire flow from API endpoint to database
        pass
    
    @pytest.mark.asyncio
    async def test_embedding_generation_pipeline(self):
        """Test embedding generation pipeline"""
        # Test the complete pipeline from idea creation to embedding generation
        pass
    
    @pytest.mark.asyncio
    async def test_similarity_search_accuracy(self):
        """Test accuracy of similarity search"""
        # Test with known similar and dissimilar content
        pass


# Test fixtures for database setup
@pytest.fixture
def sample_ideas():
    """Create sample ideas for testing"""
    return [
        {
            'id': 'idea-1',
            'content': 'Build a mobile app for tracking fitness goals',
            'category': 'technical',
            'user_id': 'user-123'
        },
        {
            'id': 'idea-2',
            'content': 'Create a fitness tracking application for smartphones',
            'category': 'technical',
            'user_id': 'user-123'
        },
        {
            'id': 'idea-3',
            'content': 'Write a book about cooking recipes',
            'category': 'creative',
            'user_id': 'user-123'
        }
    ]


@pytest.fixture
def sample_embeddings():
    """Create sample embeddings for testing"""
    return {
        'idea-1': [0.1, 0.2, 0.3, 0.4],
        'idea-2': [0.15, 0.25, 0.35, 0.45],  # Similar to idea-1
        'idea-3': [0.8, 0.9, 0.1, 0.2]       # Different from idea-1 and idea-2
    }


# Performance tests
class TestSemanticSearchPerformance:
    """Performance tests for semantic search"""
    
    @pytest.mark.asyncio
    async def test_batch_embedding_performance(self):
        """Test performance of batch embedding generation"""
        # Test with various batch sizes
        pass
    
    @pytest.mark.asyncio
    async def test_search_response_time(self):
        """Test search response time"""
        # Test search performance with different query types
        pass
    
    @pytest.mark.asyncio
    async def test_similarity_calculation_performance(self):
        """Test similarity calculation performance"""
        # Test with different numbers of embeddings
        pass


if __name__ == "__main__":
    pytest.main([__file__])