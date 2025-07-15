# Dreamcatcher Backend Testing

This directory contains the test suite for the Dreamcatcher backend.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Test configuration and fixtures
├── test_database.py         # Database and CRUD tests
├── test_agents.py           # Agent system tests
├── test_api.py              # API endpoint tests
└── README.md                # This file
```

## Running Tests

### Quick Start
```bash
# From backend directory
python run_tests.py

# Or directly with pytest
python -m pytest tests/
```

### Test Categories

#### Database Tests (`test_database.py`)
- **IdeaCRUD Tests**: Create, read, update, delete ideas
- **AgentCRUD Tests**: Agent registration and activity logging
- **SystemMetricsCRUD Tests**: System metrics recording and retrieval

#### Agent Tests (`test_agents.py`)
- **BaseAgent Tests**: Core agent functionality
- **AgentRegistry Tests**: Agent registration and message routing
- **AgentClassifier Tests**: Idea classification functionality
- **AgentListener Tests**: Input processing and transcription

#### API Tests (`test_api.py`)
- **Health Endpoint**: Service health checks
- **Idea Endpoints**: CRUD operations via API
- **Agent Endpoints**: Agent management and monitoring
- **Metrics Endpoints**: System metrics and error tracking
- **Proposal Endpoints**: Proposal management

### Test Configuration

The test suite uses:
- **pytest**: Test framework
- **pytest-asyncio**: Async test support
- **SQLite**: In-memory test database
- **FastAPI TestClient**: API testing
- **Mock/AsyncMock**: Service mocking

### Key Fixtures

#### Database Fixtures
- `db_session`: Fresh database session for each test
- `client`: FastAPI test client with database override

#### Mock Fixtures
- `mock_ai_service`: Mocked AI service for testing
- `mock_agent`: Test agent implementation
- `mock_websocket`: WebSocket mock for testing

#### Data Fixtures
- `sample_idea_data`: Standard idea data for testing
- `temp_audio_file`: Temporary audio file for voice tests

### Writing Tests

#### Basic Test Structure
```python
def test_something(db_session):
    # Arrange
    data = create_test_data()
    
    # Act
    result = perform_operation(data)
    
    # Assert
    assert result.success is True
    assert result.data == expected_data
```

#### Async Tests
```python
@pytest.mark.asyncio
async def test_async_operation(mock_agent):
    # Test async functionality
    result = await mock_agent.process(test_data)
    assert result['success'] is True
```

#### API Tests
```python
def test_api_endpoint(client: TestClient):
    response = client.get("/api/endpoint")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
```

### Test Data Management

Tests use isolated database sessions that are:
- Created fresh for each test
- Automatically cleaned up after each test
- Use SQLite in-memory for speed
- Independent of production database

### Mocking Strategy

The test suite mocks external dependencies:
- **AI Services**: Claude/OpenAI API calls
- **Audio Processing**: Whisper transcription
- **WebSocket Connections**: Real-time updates
- **File System**: Temporary files and storage

### Common Test Patterns

#### Testing CRUD Operations
```python
def test_create_and_retrieve(db_session):
    # Create
    item = ItemCRUD.create_item(db_session, data)
    assert item.id is not None
    
    # Retrieve
    retrieved = ItemCRUD.get_item(db_session, item.id)
    assert retrieved.id == item.id
```

#### Testing Agent Processing
```python
@pytest.mark.asyncio
async def test_agent_processing(mock_agent):
    result = await mock_agent.process(test_data)
    assert mock_agent.process_called is True
    assert result['success'] is True
```

#### Testing API Endpoints
```python
def test_api_error_handling(client: TestClient):
    response = client.get("/api/nonexistent")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
```

### Best Practices

1. **Isolation**: Each test should be independent
2. **Clear Names**: Test names should describe what they test
3. **Arrange-Act-Assert**: Follow the AAA pattern
4. **Mock External**: Mock all external dependencies
5. **Test Edge Cases**: Include error conditions and edge cases
6. **Fast Tests**: Keep tests fast with mocking and in-memory DB

### Running Specific Tests

```bash
# Run specific test file
python -m pytest tests/test_database.py

# Run specific test class
python -m pytest tests/test_database.py::TestIdeaCRUD

# Run specific test method
python -m pytest tests/test_database.py::TestIdeaCRUD::test_create_idea

# Run tests with specific marker
python -m pytest -m "not slow"
```

### Test Coverage

To run tests with coverage:
```bash
python -m pytest tests/ --cov=. --cov-report=html
```

### Debugging Tests

For debugging failing tests:
```bash
# Show full traceback
python -m pytest tests/ --tb=long

# Drop into debugger on failure
python -m pytest tests/ --pdb

# Show output from print statements
python -m pytest tests/ -s
```

## Adding New Tests

When adding new functionality:

1. **Create tests first** (TDD approach)
2. **Test both success and failure paths**
3. **Mock external dependencies**
4. **Use appropriate fixtures**
5. **Follow existing patterns**
6. **Update this README if needed**

## Continuous Integration

The test suite is designed to run in CI/CD environments:
- No external dependencies (all mocked)
- Uses in-memory database
- Deterministic results
- Fast execution
- Clear pass/fail indicators