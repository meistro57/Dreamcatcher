import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from database import IdeaCRUD, AgentCRUD, SystemMetricsCRUD, models

class TestIdeaCRUD:
    """Test cases for IdeaCRUD operations."""
    
    def test_create_idea(self, db_session: Session):
        """Test creating a new idea."""
        idea = IdeaCRUD.create_idea(
            db=db_session,
            content="Test idea content",
            source_type="text",
            urgency_score=75.0,
            category="development"
        )
        
        assert idea.id is not None
        assert idea.content_raw == "Test idea content"
        assert idea.source_type == "text"
        assert idea.urgency_score == 75.0
        assert idea.category == "development"
        assert idea.created_at is not None
    
    def test_get_idea(self, db_session: Session):
        """Test retrieving an idea by ID."""
        # Create an idea first
        idea = IdeaCRUD.create_idea(
            db=db_session,
            content="Test idea",
            source_type="text"
        )
        
        # Retrieve it
        retrieved_idea = IdeaCRUD.get_idea(db_session, idea.id)
        
        assert retrieved_idea is not None
        assert retrieved_idea.id == idea.id
        assert retrieved_idea.content_raw == "Test idea"
    
    def test_get_ideas_with_filters(self, db_session: Session):
        """Test retrieving ideas with various filters."""
        # Create test ideas
        IdeaCRUD.create_idea(
            db=db_session,
            content="High urgency idea",
            source_type="voice",
            urgency_score=90.0,
            category="urgent"
        )
        
        IdeaCRUD.create_idea(
            db=db_session,
            content="Low urgency idea",
            source_type="text",
            urgency_score=30.0,
            category="normal"
        )
        
        # Test urgency filter
        high_urgency = IdeaCRUD.get_ideas(db_session, min_urgency=80.0)
        assert len(high_urgency) == 1
        assert high_urgency[0].urgency_score == 90.0
        
        # Test source type filter
        voice_ideas = IdeaCRUD.get_ideas(db_session, source_type="voice")
        assert len(voice_ideas) == 1
        assert voice_ideas[0].source_type == "voice"
        
        # Test category filter
        urgent_ideas = IdeaCRUD.get_ideas(db_session, category="urgent")
        assert len(urgent_ideas) == 1
        assert urgent_ideas[0].category == "urgent"
    
    def test_update_idea(self, db_session: Session):
        """Test updating an idea."""
        idea = IdeaCRUD.create_idea(
            db=db_session,
            content="Original content",
            source_type="text"
        )
        
        updated_idea = IdeaCRUD.update_idea(
            db=db_session,
            idea_id=idea.id,
            urgency_score=85.0,
            category="updated"
        )
        
        assert updated_idea.urgency_score == 85.0
        assert updated_idea.category == "updated"
        assert updated_idea.content_raw == "Original content"  # Unchanged
    
    def test_delete_idea(self, db_session: Session):
        """Test deleting an idea."""
        idea = IdeaCRUD.create_idea(
            db=db_session,
            content="To be deleted",
            source_type="text"
        )
        
        # Delete the idea
        success = IdeaCRUD.delete_idea(db_session, idea.id)
        assert success is True
        
        # Verify it's gone
        deleted_idea = IdeaCRUD.get_idea(db_session, idea.id)
        assert deleted_idea is None
    
    def test_get_dormant_ideas(self, db_session: Session):
        """Test getting dormant ideas."""
        # Create an old idea with low urgency
        old_date = datetime.utcnow() - timedelta(days=35)
        idea = IdeaCRUD.create_idea(
            db=db_session,
            content="Dormant idea",
            source_type="text",
            urgency_score=20.0
        )
        
        # Manually set the updated_at to be old
        idea.updated_at = old_date
        db_session.commit()
        
        dormant_ideas = IdeaCRUD.get_dormant_ideas(db_session, days=30)
        assert len(dormant_ideas) == 1
        assert dormant_ideas[0].id == idea.id
    
    def test_get_random_ideas(self, db_session: Session):
        """Test getting random ideas."""
        # Create multiple ideas
        for i in range(5):
            IdeaCRUD.create_idea(
                db=db_session,
                content=f"Random idea {i}",
                source_type="text"
            )
        
        random_ideas = IdeaCRUD.get_random_ideas(db_session, count=3)
        assert len(random_ideas) == 3
        
        # Should get different results on subsequent calls (probabilistically)
        random_ideas_2 = IdeaCRUD.get_random_ideas(db_session, count=3)
        assert len(random_ideas_2) == 3
    
    def test_archive_idea(self, db_session: Session):
        """Test archiving an idea."""
        idea = IdeaCRUD.create_idea(
            db=db_session,
            content="To be archived",
            source_type="text"
        )
        
        archived_idea = IdeaCRUD.archive_idea(
            db_session, 
            idea.id, 
            reason="Test archival"
        )
        
        assert archived_idea.is_archived is True
        assert archived_idea.archived_reason == "Test archival"

class TestAgentCRUD:
    """Test cases for AgentCRUD operations."""
    
    def test_create_agent(self, db_session: Session):
        """Test creating/updating an agent."""
        agent = AgentCRUD.create_or_update_agent(
            db=db_session,
            agent_id="test_agent",
            name="Test Agent",
            description="Test description",
            version="1.0.0",
            config={"test": "value"}
        )
        
        assert agent.id == "test_agent"
        assert agent.name == "Test Agent"
        assert agent.description == "Test description"
        assert agent.version == "1.0.0"
        assert agent.config == {"test": "value"}
    
    def test_log_agent_activity(self, db_session: Session):
        """Test logging agent activity."""
        # Create an agent first
        AgentCRUD.create_or_update_agent(
            db=db_session,
            agent_id="test_agent",
            name="Test Agent"
        )
        
        log = AgentCRUD.log_agent_activity(
            db=db_session,
            agent_id="test_agent",
            action="test_action",
            status="completed",
            input_data={"input": "test"},
            output_data={"output": "result"}
        )
        
        assert log.agent_id == "test_agent"
        assert log.action == "test_action"
        assert log.status == "completed"
        assert log.input_data == {"input": "test"}
        assert log.output_data == {"output": "result"}
    
    def test_get_agent_performance(self, db_session: Session):
        """Test getting agent performance metrics."""
        # Create an agent
        AgentCRUD.create_or_update_agent(
            db=db_session,
            agent_id="test_agent",
            name="Test Agent"
        )
        
        # Log some activities
        AgentCRUD.log_agent_activity(
            db=db_session,
            agent_id="test_agent",
            action="test_action",
            status="completed"
        )
        
        AgentCRUD.log_agent_activity(
            db=db_session,
            agent_id="test_agent",
            action="test_action",
            status="failed"
        )
        
        performance = AgentCRUD.get_agent_performance(db_session, "test_agent")
        
        assert performance['total_tasks'] == 2
        assert performance['successful_tasks'] == 1
        assert performance['failed_tasks'] == 1
        assert performance['success_rate'] == 0.5

class TestSystemMetricsCRUD:
    """Test cases for SystemMetricsCRUD operations."""
    
    def test_record_metric(self, db_session: Session):
        """Test recording a system metric."""
        metric = SystemMetricsCRUD.record_metric(
            db=db_session,
            metric_name="test_metric",
            metric_value=123.45,
            metric_type="gauge",
            metadata={"source": "test"}
        )
        
        assert metric.metric_name == "test_metric"
        assert metric.metric_value == 123.45
        assert metric.metric_type == "gauge"
        assert metric.metadata == {"source": "test"}
    
    def test_get_metrics(self, db_session: Session):
        """Test retrieving metrics."""
        # Record some metrics
        SystemMetricsCRUD.record_metric(
            db=db_session,
            metric_name="cpu_usage",
            metric_value=65.0
        )
        
        SystemMetricsCRUD.record_metric(
            db=db_session,
            metric_name="memory_usage",
            metric_value=80.0
        )
        
        # Get all metrics
        all_metrics = SystemMetricsCRUD.get_metrics(db_session)
        assert len(all_metrics) == 2
        
        # Get specific metric
        cpu_metrics = SystemMetricsCRUD.get_metrics(db_session, metric_name="cpu_usage")
        assert len(cpu_metrics) == 1
        assert cpu_metrics[0].metric_name == "cpu_usage"
        assert cpu_metrics[0].metric_value == 65.0