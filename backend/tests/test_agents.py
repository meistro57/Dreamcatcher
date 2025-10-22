import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from agents.base_agent import BaseAgent, AgentRegistry, AgentMessage
from agents.agent_classifier import AgentClassifier
from agents.agent_listener import AgentListener

class TestBaseAgent:
    """Test cases for BaseAgent functionality."""
    
    def test_agent_initialization(self):
        """Test agent initialization."""
        agent = BaseAgent("test_agent", "Test Agent", "Test description", "1.0.0")
        
        assert agent.agent_id == "test_agent"
        assert agent.name == "Test Agent"
        assert agent.description == "Test description"
        assert agent.version == "1.0.0"
        assert agent.is_active is True
        assert agent.total_processed == 0
        assert agent.success_count == 0
        assert agent.failure_count == 0
    
    def test_agent_performance_metrics(self):
        """Test agent performance metrics."""
        agent = BaseAgent("test_agent", "Test Agent")
        
        # Simulate some processing
        agent.total_processed = 10
        agent.success_count = 8
        agent.failure_count = 2
        
        metrics = agent.get_performance_metrics()
        
        assert metrics['agent_id'] == "test_agent"
        assert metrics['total_processed'] == 10
        assert metrics['success_count'] == 8
        assert metrics['failure_count'] == 2
        assert metrics['success_rate'] == 0.8
        assert metrics['is_active'] is True
    
    def test_agent_activation_deactivation(self):
        """Test agent activation and deactivation."""
        agent = BaseAgent("test_agent", "Test Agent")
        
        assert agent.is_active is True
        
        agent.deactivate()
        assert agent.is_active is False
        
        agent.activate()
        assert agent.is_active is True
    
    def test_agent_config_update(self):
        """Test agent configuration updates."""
        agent = BaseAgent("test_agent", "Test Agent")
        
        initial_config = {"key1": "value1"}
        agent.update_config(initial_config)
        assert agent.config == initial_config
        
        update_config = {"key2": "value2"}
        agent.update_config(update_config)
        assert agent.config == {"key1": "value1", "key2": "value2"}
    
    @pytest.mark.asyncio
    async def test_send_message(self, mock_agent):
        """Test sending messages between agents."""
        recipient_agent = BaseAgent("recipient", "Recipient Agent")
        
        # Mock the delivery system
        mock_agent._deliver_message = AsyncMock()
        
        await mock_agent.send_message(
            recipient="recipient",
            action="test_action",
            data={"test": "data"}
        )
        
        assert mock_agent._deliver_message.called
        call_args = mock_agent._deliver_message.call_args[0][0]
        assert call_args.sender == "test_agent"
        assert call_args.recipient == "recipient"
        assert call_args.action == "test_action"
        assert call_args.data == {"test": "data"}
    
    @pytest.mark.asyncio
    async def test_handle_message_success(self, mock_agent, db_session):
        """Test successful message handling."""
        message = AgentMessage(
            id="test_message",
            sender="sender",
            recipient="test_agent",
            action="test_action",
            data={"input": "test"},
            timestamp=datetime.utcnow()
        )
        
        result = await mock_agent.handle_message(message)
        
        assert result is not None
        assert result['success'] is True
        assert result['result'] == "Test result"
        assert mock_agent.process_called is True
        assert mock_agent.success_count == 1
        assert mock_agent.total_processed == 1
    
    @pytest.mark.asyncio
    async def test_handle_message_failure(self, db_session):
        """Test message handling failure."""
        class FailingAgent(BaseAgent):
            async def process(self, data):
                raise Exception("Test error")
        
        agent = FailingAgent("failing_agent", "Failing Agent")
        
        message = AgentMessage(
            id="test_message",
            sender="sender",
            recipient="failing_agent",
            action="test_action",
            data={"input": "test"},
            timestamp=datetime.utcnow()
        )
        
        result = await agent.handle_message(message)
        
        assert result is None
        assert agent.failure_count == 1
        assert agent.total_processed == 1

class TestAgentRegistry:
    """Test cases for AgentRegistry functionality."""
    
    def test_agent_registration(self):
        """Test agent registration."""
        registry = AgentRegistry()
        agent = BaseAgent("test_agent", "Test Agent")
        
        registry.register(agent)
        
        assert "test_agent" in registry.agents
        assert registry.get_agent("test_agent") == agent
    
    def test_agent_unregistration(self):
        """Test agent unregistration."""
        registry = AgentRegistry()
        agent = BaseAgent("test_agent", "Test Agent")
        
        registry.register(agent)
        assert registry.get_agent("test_agent") is not None
        
        registry.unregister("test_agent")
        assert registry.get_agent("test_agent") is None
    
    def test_get_all_agents(self):
        """Test getting all agents."""
        registry = AgentRegistry()
        agent1 = BaseAgent("agent1", "Agent 1")
        agent2 = BaseAgent("agent2", "Agent 2")
        
        registry.register(agent1)
        registry.register(agent2)
        
        all_agents = registry.get_all_agents()
        assert len(all_agents) == 2
        assert agent1 in all_agents
        assert agent2 in all_agents
    
    def test_get_active_agents(self):
        """Test getting active agents."""
        registry = AgentRegistry()
        agent1 = BaseAgent("agent1", "Agent 1")
        agent2 = BaseAgent("agent2", "Agent 2")
        
        registry.register(agent1)
        registry.register(agent2)
        
        # Deactivate one agent
        agent2.deactivate()
        
        active_agents = registry.get_active_agents()
        assert len(active_agents) == 1
        assert agent1 in active_agents
        assert agent2 not in active_agents
    
    @pytest.mark.asyncio
    async def test_send_message(self):
        """Test sending message through registry."""
        registry = AgentRegistry()
        agent = BaseAgent("test_agent", "Test Agent")
        registry.register(agent)
        
        message = AgentMessage(
            id="test_message",
            sender="sender",
            recipient="test_agent",
            action="test_action",
            data={"test": "data"},
            timestamp=datetime.utcnow()
        )
        
        # Mock the agent's message queue
        agent.message_queue = AsyncMock()
        
        await registry.send_message(message)
        
        agent.message_queue.put.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_broadcast_message(self):
        """Test broadcasting message to all agents."""
        registry = AgentRegistry()
        agent1 = BaseAgent("agent1", "Agent 1")
        agent2 = BaseAgent("agent2", "Agent 2")
        sender_agent = BaseAgent("sender", "Sender Agent")
        
        registry.register(agent1)
        registry.register(agent2)
        registry.register(sender_agent)
        
        # Mock message queues
        agent1.message_queue = AsyncMock()
        agent2.message_queue = AsyncMock()
        sender_agent.message_queue = AsyncMock()
        
        await registry.broadcast_message(
            sender="sender",
            action="broadcast_action",
            data={"broadcast": "data"}
        )
        
        # Sender should not receive the message
        sender_agent.message_queue.put.assert_not_called()
        
        # Other agents should receive the message
        agent1.message_queue.put.assert_called_once()
        agent2.message_queue.put.assert_called_once()
    
    def test_system_status(self):
        """Test getting system status."""
        registry = AgentRegistry()
        agent1 = BaseAgent("agent1", "Agent 1")
        agent2 = BaseAgent("agent2", "Agent 2")
        
        registry.register(agent1)
        registry.register(agent2)
        
        # Deactivate one agent
        agent2.deactivate()
        
        status = registry.get_system_status()
        
        assert status['total_agents'] == 2
        assert status['active_agents'] == 1
        assert status['inactive_agents'] == 1
        assert len(status['agent_performance']) == 2

class TestAgentClassifier:
    """Test cases for AgentClassifier functionality."""
    
    def test_classifier_initialization(self):
        """Test classifier initialization."""
        classifier = AgentClassifier()
        
        assert classifier.agent_id == "classifier"
        assert classifier.name == "Idea Classifier"
        assert len(classifier.classification_categories) > 0
        assert "development" in classifier.classification_categories
    
    def test_classification_stats(self):
        """Test getting classification statistics."""
        classifier = AgentClassifier()
        
        # Simulate some classifications
        classifier.classification_counts = {
            "development": 5,
            "business": 3,
            "personal": 2
        }
        
        stats = classifier.get_classification_stats()
        
        assert stats['total_classifications'] == 10
        assert stats['categories']['development'] == 5
        assert stats['categories']['business'] == 3
        assert stats['categories']['personal'] == 2
    
    @pytest.mark.asyncio
    async def test_classify_idea(self, mock_ai_service):
        """Test idea classification."""
        classifier = AgentClassifier()
        
        # Mock AI service response
        mock_ai_service.generate_response.return_value = {
            "response": '{"category": "development", "confidence": 0.85, "urgency_score": 75.0}',
            "tokens_used": 50
        }
        
        # Mock the AI service
        classifier.ai_service = mock_ai_service
        
        data = {
            "content": "Build a new API endpoint",
            "source_type": "text"
        }
        
        result = await classifier.process(data)
        
        assert result['success'] is True
        assert result['classification']['category'] == "development"
        assert result['classification']['confidence'] == 0.85
        assert result['classification']['urgency_score'] == 75.0

class TestAgentListener:
    """Test cases for AgentListener functionality."""
    
    def test_listener_initialization(self):
        """Test listener initialization."""
        listener = AgentListener()
        
        assert listener.agent_id == "listener"
        assert listener.name == "Input Listener"
        assert hasattr(listener, 'audio_processor')
        assert hasattr(listener, 'ai_service')
    
    @pytest.mark.asyncio
    async def test_process_text_input(self, mock_ai_service, db_session):
        """Test processing text input."""
        listener = AgentListener()
        
        # Mock AI service
        mock_ai_service.generate_response.return_value = {
            "response": "Processed text content",
            "tokens_used": 30
        }
        listener.ai_service = mock_ai_service
        
        data = {
            "type": "text",
            "content": "Test idea content",
            "urgency": "high"
        }
        
        result = await listener.process(data)
        
        assert result['success'] is True
        assert result['idea_id'] is not None
        assert result['content_type'] == "text"
        assert 'transcription' in result or 'content' in result
    
    @pytest.mark.asyncio
    async def test_process_voice_input(self, mock_ai_service, temp_audio_file):
        """Test processing voice input."""
        listener = AgentListener()
        
        # Mock AI service
        mock_ai_service.generate_response.return_value = {
            "response": "Processed voice content",
            "tokens_used": 50
        }
        listener.ai_service = mock_ai_service
        
        # Mock audio processor
        listener.audio_processor = MagicMock()
        listener.audio_processor.process_audio_file = AsyncMock(return_value={
            "transcription": "Transcribed voice content",
            "quality_metrics": {"snr": 25.0, "clarity": 0.8}
        })
        
        data = {
            "type": "voice",
            "audio_file": temp_audio_file,
            "urgency": "normal"
        }
        
        result = await listener.process(data)
        
        assert result['success'] is True
        assert result['transcription'] == "Transcribed voice content"
        assert result['audio_quality'] is not None