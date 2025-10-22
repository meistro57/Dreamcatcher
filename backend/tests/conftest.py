import os
import sys
import tempfile
from pathlib import Path

import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock

# Ensure the backend root is on the import path so top-level modules resolve.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import your app modules
import main
from database import Base, get_db
from agents import agent_registry
from services import AIService

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with dependency overrides."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    main.app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(main.app) as test_client:
        yield test_client
    
    main.app.dependency_overrides.clear()

@pytest.fixture
def mock_ai_service():
    """Mock AI service for testing."""
    mock_service = MagicMock(spec=AIService)
    mock_service.is_available.return_value = True
    mock_service.get_available_models.return_value = ["claude-3-sonnet", "gpt-4"]
    mock_service.generate_response = AsyncMock(return_value={
        "response": "Test response",
        "tokens_used": 100,
        "model": "claude-3-sonnet"
    })
    return mock_service

@pytest.fixture
def sample_idea_data():
    """Sample idea data for testing."""
    return {
        "content": "Test idea content",
        "source_type": "text",
        "urgency": "high",
        "location": "home"
    }

@pytest.fixture
def temp_audio_file():
    """Create a temporary audio file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        # Write some dummy audio data
        tmp.write(b'dummy audio data')
        tmp.flush()
        yield tmp.name
    os.unlink(tmp.name)

@pytest.fixture(autouse=True)
def clear_agent_registry():
    """Clear agent registry before each test."""
    agent_registry.agents.clear()
    yield
    agent_registry.agents.clear()

@pytest.fixture
def mock_agent():
    """Create a mock agent for testing."""
    from ..agents.base_agent import BaseAgent
    
    class MockAgent(BaseAgent):
        def __init__(self):
            super().__init__("test_agent", "Test Agent", "Test description")
            self.process_called = False
            self.last_data = None
        
        async def process(self, data):
            self.process_called = True
            self.last_data = data
            return {
                "success": True,
                "result": "Test result",
                "data": data
            }
    
    return MockAgent()

@pytest.fixture
def mock_websocket():
    """Mock WebSocket for testing."""
    mock_ws = MagicMock()
    mock_ws.accept = AsyncMock()
    mock_ws.send_text = AsyncMock()
    mock_ws.receive_text = AsyncMock()
    mock_ws.close = AsyncMock()
    return mock_ws