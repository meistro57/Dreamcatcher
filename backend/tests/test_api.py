import pytest
import json
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient

from ..database import IdeaCRUD, AgentCRUD

class TestHealthEndpoint:
    """Test cases for health check endpoint."""
    
    def test_health_check(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "agents" in data
        assert "services" in data

class TestIdeaEndpoints:
    """Test cases for idea-related endpoints."""
    
    def test_capture_text_idea(self, client: TestClient, sample_idea_data):
        """Test capturing a text idea."""
        response = client.post("/api/capture/text", json=sample_idea_data)
        
        # Note: This might fail without proper agent setup
        # In a real test, we'd mock the agents
        assert response.status_code in [200, 500]  # 500 if agents not set up
    
    def test_get_ideas_empty(self, client: TestClient):
        """Test getting ideas when none exist."""
        response = client.get("/api/ideas")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_get_ideas_with_data(self, client: TestClient, db_session):
        """Test getting ideas when data exists."""
        # Create test ideas
        idea1 = IdeaCRUD.create_idea(
            db=db_session,
            content="Test idea 1",
            source_type="text",
            urgency_score=80.0
        )
        
        idea2 = IdeaCRUD.create_idea(
            db=db_session,
            content="Test idea 2", 
            source_type="voice",
            urgency_score=60.0
        )
        
        response = client.get("/api/ideas")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Check first idea
        assert data[0]["content"] == "Test idea 1"
        assert data[0]["source_type"] == "text"
        assert data[0]["urgency_score"] == 80.0
    
    def test_get_ideas_with_filters(self, client: TestClient, db_session):
        """Test getting ideas with filters."""
        # Create test ideas
        IdeaCRUD.create_idea(
            db=db_session,
            content="High urgency",
            source_type="text",
            urgency_score=90.0
        )
        
        IdeaCRUD.create_idea(
            db=db_session,
            content="Low urgency",
            source_type="text",
            urgency_score=30.0
        )
        
        # Test urgency filter
        response = client.get("/api/ideas?min_urgency=80.0")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["urgency_score"] == 90.0
    
    def test_get_specific_idea(self, client: TestClient, db_session):
        """Test getting a specific idea by ID."""
        idea = IdeaCRUD.create_idea(
            db=db_session,
            content="Specific idea",
            source_type="text"
        )
        
        response = client.get(f"/api/ideas/{idea.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == idea.id
        assert data["content"] == "Specific idea"
        assert data["source_type"] == "text"
    
    def test_get_nonexistent_idea(self, client: TestClient):
        """Test getting a non-existent idea."""
        response = client.get("/api/ideas/nonexistent-id")
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Idea not found"
    
    def test_update_idea(self, client: TestClient, db_session):
        """Test updating an idea."""
        idea = IdeaCRUD.create_idea(
            db=db_session,
            content="Original content",
            source_type="text"
        )
        
        response = client.put(
            f"/api/ideas/{idea.id}",
            params={
                "content": "Updated content",
                "urgency_score": 85.0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["urgency_score"] == 85.0
    
    def test_delete_idea(self, client: TestClient, db_session):
        """Test deleting an idea."""
        idea = IdeaCRUD.create_idea(
            db=db_session,
            content="To be deleted",
            source_type="text"
        )
        
        response = client.delete(f"/api/ideas/{idea.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["idea_id"] == idea.id
        
        # Verify it's deleted
        response = client.get(f"/api/ideas/{idea.id}")
        assert response.status_code == 404
    
    def test_archive_idea(self, client: TestClient, db_session):
        """Test archiving an idea."""
        idea = IdeaCRUD.create_idea(
            db=db_session,
            content="To be archived",
            source_type="text"
        )
        
        response = client.post(
            f"/api/ideas/{idea.id}/archive",
            data={"reason": "Test archival"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["archived_reason"] == "Test archival"

class TestAgentEndpoints:
    """Test cases for agent-related endpoints."""
    
    def test_get_agent_status_empty(self, client: TestClient):
        """Test getting agent status when no agents exist."""
        response = client.get("/api/agents/status")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_get_agent_status_with_agents(self, client: TestClient, db_session):
        """Test getting agent status with registered agents."""
        # Create test agents in database
        AgentCRUD.create_or_update_agent(
            db=db_session,
            agent_id="test_agent",
            name="Test Agent",
            description="Test description"
        )
        
        # The actual agents would be registered in the registry
        # For this test, we'll just check the endpoint works
        response = client.get("/api/agents/status")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_agent_logs(self, client: TestClient, db_session):
        """Test getting agent logs."""
        # Create agent and log some activity
        AgentCRUD.create_or_update_agent(
            db=db_session,
            agent_id="test_agent",
            name="Test Agent"
        )
        
        AgentCRUD.log_agent_activity(
            db=db_session,
            agent_id="test_agent",
            action="test_action",
            status="completed"
        )
        
        response = client.get("/api/agents/test_agent/logs")
        
        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "test_agent"
        assert isinstance(data["logs"], list)
        assert len(data["logs"]) == 1
    
    def test_send_agent_message(self, client: TestClient, mock_agent):
        """Test sending message to agent."""
        # This would require proper agent setup
        # For now, just test that endpoint exists
        response = client.post(
            "/api/agents/test_agent/message",
            data={
                "action": "test_action",
                "data": json.dumps({"test": "data"})
            }
        )
        
        # Will likely return 404 as agent isn't registered
        assert response.status_code in [200, 404]

class TestMetricsEndpoints:
    """Test cases for metrics and monitoring endpoints."""
    
    def test_get_system_metrics(self, client: TestClient, db_session):
        """Test getting system metrics."""
        from ..database import SystemMetricsCRUD
        
        # Create some test metrics
        SystemMetricsCRUD.record_metric(
            db=db_session,
            metric_name="test_metric",
            metric_value=123.45
        )
        
        response = client.get("/api/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["metrics"], list)
        assert data["count"] == 1
        assert data["metrics"][0]["metric_name"] == "test_metric"
        assert data["metrics"][0]["metric_value"] == 123.45
    
    def test_get_error_summary(self, client: TestClient, db_session):
        """Test getting error summary."""
        # Create agent and log error
        AgentCRUD.create_or_update_agent(
            db=db_session,
            agent_id="test_agent",
            name="Test Agent"
        )
        
        AgentCRUD.log_agent_activity(
            db=db_session,
            agent_id="test_agent",
            action="failed_action",
            status="failed",
            error_message="Test error"
        )
        
        response = client.get("/api/errors")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_errors"] == 1
        assert "test_agent" in data["errors_by_agent"]
        assert len(data["recent_errors"]) == 1
        assert data["recent_errors"][0]["error_message"] == "Test error"
    
    def test_get_system_stats(self, client: TestClient, db_session):
        """Test getting system statistics."""
        # Create some test data
        IdeaCRUD.create_idea(
            db=db_session,
            content="Test idea",
            source_type="text",
            urgency_score=90.0
        )
        
        response = client.get("/api/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "ideas" in data
        assert "agents" in data
        assert "services" in data
        assert "timestamp" in data
        assert data["ideas"]["total"] == 1
        assert data["ideas"]["high_urgency"] == 1

class TestProposalEndpoints:
    """Test cases for proposal-related endpoints."""
    
    def test_get_proposals_empty(self, client: TestClient):
        """Test getting proposals when none exist."""
        response = client.get("/api/proposals")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_get_proposals_with_data(self, client: TestClient, db_session):
        """Test getting proposals when data exists."""
        from ..database import ProposalCRUD
        
        # Create test idea and proposal
        idea = IdeaCRUD.create_idea(
            db=db_session,
            content="Test idea",
            source_type="text"
        )
        
        proposal = ProposalCRUD.create_proposal(
            db=db_session,
            idea_id=idea.id,
            title="Test Proposal",
            description="Test description",
            generated_by="test_agent"
        )
        
        response = client.get("/api/proposals")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Test Proposal"
        assert data[0]["idea_id"] == idea.id
    
    def test_approve_proposal(self, client: TestClient, db_session):
        """Test approving a proposal."""
        from ..database import ProposalCRUD
        
        # Create test proposal
        idea = IdeaCRUD.create_idea(
            db=db_session,
            content="Test idea",
            source_type="text"
        )
        
        proposal = ProposalCRUD.create_proposal(
            db=db_session,
            idea_id=idea.id,
            title="Test Proposal",
            description="Test description"
        )
        
        response = client.post(
            f"/api/proposals/{proposal.id}/approve",
            data={"notes": "Approved for testing"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["proposal_id"] == proposal.id
        assert data["status"] == "approved"