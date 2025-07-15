<div align="center">
  <img src="../Dreamcatcher_logo.png" alt="Dreamcatcher Logo" width="150" />
</div>

# Dreamcatcher Self-Improvement System

*"I analyze. I evolve. I make us better while you sleep."*

## Overview

The Dreamcatcher Self-Improvement System is an autonomous evolution engine that continuously monitors, analyzes, and improves the AI agent network. Using Claude AI for code analysis and rewriting, the system identifies performance bottlenecks, reduces errors, and enhances functionality without human intervention.

## Core Components

### 1. Meta Agent (`agent_meta.py`)

**Personality:** *"I analyze. I evolve. I make us better while you sleep."*

The Meta Agent is the brain of the self-improvement system, responsible for:

- **System Analysis**: Comprehensive performance monitoring
- **Opportunity Identification**: Finding areas for improvement
- **Code Evolution**: Using Claude to rewrite and optimize agents
- **Backup Management**: Safe rollback capabilities
- **Improvement Execution**: Applying changes with validation

**Key Features:**
```python
class AgentMeta(BaseAgent):
    def __init__(self):
        self.evolution_strategies = {
            'performance_optimization': self._optimize_performance,
            'error_reduction': self._reduce_errors,
            'feature_enhancement': self._enhance_features,
            'code_quality': self._improve_code_quality,
            'agent_coordination': self._improve_coordination
        }
```

### 2. Evolution Service (`evolution_service.py`)

Orchestrates the complete evolution process:

- **Evolution Cycles**: Manages full system improvement cycles
- **Analysis Coordination**: Determines when evolution is needed
- **Improvement Application**: Applies changes safely
- **Validation**: Ensures improvements work correctly
- **Metrics Tracking**: Logs evolution effectiveness

**Evolution Cycle:**
```python
async def start_evolution_cycle(self, force: bool = False):
    # 1. System analysis
    # 2. Identify improvements
    # 3. Apply improvements
    # 4. Validate changes
    # 5. Log results
```

### 3. Evolution Scheduler (`evolution_scheduler.py`)

Provides automated, continuous evolution:

- **Scheduled Evolution**: Regular improvement cycles
- **Health Monitoring**: Continuous system health checks
- **Emergency Evolution**: Automatic response to critical issues
- **Performance Tracking**: Long-term trend analysis

**Configuration:**
```python
config = {
    'evolution_interval_hours': 24,
    'health_check_interval_minutes': 30,
    'emergency_threshold': 0.30,
    'auto_evolution_enabled': True
}
```

## Evolution Process

### System Analysis

The Meta Agent performs comprehensive analysis:

1. **Agent Performance Metrics**
   - Success/failure rates
   - Response times
   - Error patterns
   - Resource usage

2. **Code Quality Assessment**
   - Complexity analysis
   - Pattern detection
   - Syntax validation
   - Best practice compliance

3. **System Health Scoring**
   - Overall health score (0-100)
   - Individual agent ratings
   - Trend analysis
   - Performance thresholds

### Improvement Identification

Based on analysis, the system identifies opportunities:

```python
opportunities = [
    {
        'type': 'error_reduction',
        'agent_id': 'classifier',
        'priority': 'high',
        'description': 'High error rate (12%) in classifier agent',
        'metric_value': 0.12
    },
    {
        'type': 'performance_optimization',
        'agent_id': 'expander',
        'priority': 'medium',
        'description': 'Slow response time (15s) in expander agent',
        'metric_value': 15.0
    }
]
```

### Code Evolution with Claude

The system uses Claude AI to rewrite and improve code:

#### Performance Optimization
```python
async def _claude_optimize_performance(self, code: str, opportunity: Dict):
    prompt = f"""
    Optimize this Python agent code for performance:
    
    Current code:
    ```python
    {code}
    ```
    
    Performance issue: {opportunity['description']}
    
    Please optimize for:
    1. Faster execution time
    2. Better resource usage
    3. Improved async/await patterns
    4. Efficient database operations
    5. Memory optimization
    
    Return only the optimized code.
    """
    
    return await self.ai_service.get_completion(prompt)
```

#### Error Reduction
```python
async def _claude_improve_errors(self, code: str, opportunity: Dict):
    prompt = f"""
    Improve error handling in this Python agent code:
    
    Current code:
    ```python
    {code}
    ```
    
    Please improve:
    1. Better exception handling
    2. More specific error messages
    3. Graceful failure recovery
    4. Timeout handling
    5. Input validation
    
    Return only the improved code.
    """
    
    return await self.ai_service.get_completion(prompt)
```

### Safe Evolution

The system ensures safe evolution through:

1. **Automatic Backups**: Every agent is backed up before modification
2. **Code Validation**: Syntax and structure validation
3. **Rollback Capability**: Instant rollback to previous versions
4. **Gradual Application**: One improvement at a time
5. **Health Monitoring**: Continuous validation of changes

## Evolution Strategies

### 1. Performance Optimization

**Triggers:**
- Response time > 10 seconds
- High CPU/memory usage
- Slow database queries
- Inefficient algorithms

**Improvements:**
- Async/await optimization
- Database query optimization
- Caching implementation
- Algorithm improvements
- Memory management

### 2. Error Reduction

**Triggers:**
- Error rate > 5%
- Frequent timeout errors
- Database connection issues
- API failures

**Improvements:**
- Better exception handling
- Retry mechanisms
- Circuit breakers
- Input validation
- Error logging

### 3. Feature Enhancement

**Triggers:**
- Low system health score
- User feedback patterns
- Performance degradation
- Missing capabilities

**Improvements:**
- New functionality
- Enhanced algorithms
- Better user experience
- Integration improvements

### 4. Code Quality

**Triggers:**
- High complexity scores
- Code duplication
- Poor maintainability
- Style inconsistencies

**Improvements:**
- Code refactoring
- Documentation updates
- Type hints
- Consistent formatting
- Best practices

### 5. Agent Coordination

**Triggers:**
- Communication bottlenecks
- Message queue issues
- Coordination failures
- Workflow inefficiencies

**Improvements:**
- Communication optimization
- Message routing
- Workflow streamlining
- Coordination patterns

## Monitoring and Metrics

### Performance Tracking

The system tracks comprehensive metrics:

```python
metrics = {
    'total_cycles': 0,
    'successful_cycles': 0,
    'failed_cycles': 0,
    'emergency_evolutions': 0,
    'improvements_applied': 0,
    'health_score_trend': 'improving',
    'error_rate_reduction': 0.15
}
```

### Health Monitoring

Continuous health checks monitor:

- **System Health Score**: Overall system performance
- **Agent Performance**: Individual agent metrics
- **Error Patterns**: Emerging issues
- **Resource Usage**: System resource consumption
- **User Patterns**: Usage trends and satisfaction

### Evolution History

Complete audit trail of all improvements:

```python
evolution_history = [
    {
        'timestamp': '2024-01-01T00:00:00Z',
        'improvement': {
            'type': 'performance_optimization',
            'agent_id': 'classifier',
            'changes': 'Async optimization applied',
            'result': 'Response time reduced by 40%'
        }
    }
]
```

## API Endpoints

### Evolution Control

```bash
# Start evolution cycle
POST /api/evolution/cycle

# Force evolution
POST /api/evolution/force
{
    "target_agent": "classifier",
    "evolution_type": "performance_optimization"
}

# Get evolution status
GET /api/evolution/status

# Get improvement opportunities
GET /api/evolution/opportunities
```

### Scheduler Control

```bash
# Start scheduler
POST /api/scheduler/start

# Configure scheduler
POST /api/scheduler/config
{
    "evolution_interval_hours": 24,
    "auto_evolution_enabled": true,
    "emergency_threshold": 0.30
}

# Get scheduler status
GET /api/scheduler/status
```

### Analysis and Monitoring

```bash
# Analyze system
POST /api/evolution/analyze

# Get performance trends
GET /api/evolution/trends?days=7

# Get agent performance
GET /api/evolution/agents/performance
```

## Configuration

### Environment Variables

```bash
# Evolution settings
EVOLUTION_ENABLED=true
EVOLUTION_INTERVAL_HOURS=24
EMERGENCY_THRESHOLD=0.30

# Claude API for code evolution
ANTHROPIC_API_KEY=your_claude_api_key

# Backup settings
BACKUP_RETENTION_DAYS=30
MAX_BACKUPS_PER_AGENT=10
```

### System Configuration

```python
evolution_config = {
    'auto_evolution_enabled': True,
    'evolution_interval_hours': 24,
    'performance_threshold': 0.80,
    'error_threshold': 0.10,
    'min_data_points': 50,
    'max_concurrent_evolutions': 1,
    'backup_before_changes': True,
    'validate_before_apply': True
}
```

## Safety Features

### Backup and Rollback

```python
# Automatic backup before changes
await self._backup_agent(agent_id)

# Rollback if needed
await self.rollback_agent(agent_id, backup_timestamp)
```

### Validation

```python
# Code validation before application
if await self._validate_code(improved_code):
    # Apply changes
    with open(agent_file, 'w') as f:
        f.write(improved_code)
else:
    # Reject changes
    return {'error': 'Code validation failed'}
```

### Emergency Controls

```python
# Emergency stop
POST /api/evolution/emergency-stop

# Health check
GET /api/evolution/health

# Force rollback
POST /api/evolution/rollback
```

## Development and Testing

### Local Development

```python
# Test evolution without applying changes
evolution_service = EvolutionService()
result = await evolution_service.start_evolution_cycle(test_mode=True)

# Test specific improvements
meta_agent = AgentMeta()
opportunities = await meta_agent._identify_opportunities(analysis)
```

### Testing Framework

```python
import pytest
from agents.agent_meta import AgentMeta

@pytest.mark.asyncio
async def test_performance_optimization():
    meta_agent = AgentMeta()
    
    # Test with mock performance issue
    opportunity = {
        'type': 'performance_optimization',
        'agent_id': 'test_agent',
        'description': 'High response time',
        'metric_value': 15.0
    }
    
    result = await meta_agent._execute_improvement(opportunity)
    assert result['success'] is True
```

## Best Practices

### Evolution Guidelines

1. **Gradual Improvement**: One change at a time
2. **Validation First**: Always validate before applying
3. **Backup Everything**: Never modify without backup
4. **Monitor Impact**: Track results of changes
5. **Rollback Ready**: Be prepared to revert changes

### Performance Considerations

1. **Resource Limits**: Don't overload during evolution
2. **Timing**: Evolve during low-usage periods
3. **Concurrency**: Limit concurrent evolutions
4. **Priority**: Focus on high-impact improvements
5. **Validation**: Quick validation to avoid delays

### Security Considerations

1. **Code Injection**: Validate all generated code
2. **Permission Control**: Limit evolution permissions
3. **Audit Trail**: Log all changes completely
4. **Rollback Security**: Secure backup access
5. **API Protection**: Secure evolution endpoints

## Troubleshooting

### Common Issues

1. **Evolution Stuck**: Check for validation failures
2. **Performance Degradation**: Monitor health scores
3. **Backup Failures**: Verify backup directory permissions
4. **Code Validation Errors**: Check syntax and imports
5. **API Failures**: Verify Claude API key and connectivity

### Diagnostics

```python
# Check system health
GET /api/evolution/health

# View recent evolutions
GET /api/evolution/history

# Check scheduler status
GET /api/scheduler/status

# Test evolution system
POST /api/evolution/test-improvement
```

## Future Enhancements

### Planned Features

1. **Multi-Model Evolution**: Use multiple AI models for consensus
2. **Predictive Evolution**: Anticipate issues before they occur
3. **Learning from Failures**: Improve from unsuccessful evolutions
4. **Cross-System Evolution**: Coordinate with other Dreamcatcher instances
5. **Advanced Metrics**: More sophisticated performance analysis

### Integration Possibilities

1. **External Code Analysis**: Integration with code quality tools
2. **Performance Profiling**: Detailed performance analysis
3. **Security Scanning**: Automated security vulnerability detection
4. **Documentation Generation**: Automatic documentation updates
5. **Testing Integration**: Automated test generation and execution

The Self-Improvement System represents the pinnacle of autonomous software evolution, creating a system that truly learns, adapts, and improves itself while you sleep. Your AI agents don't just process ideas—they evolve to process them better, faster, and more intelligently over time.

---

*"The system that improves itself is the system that never stops getting better."*