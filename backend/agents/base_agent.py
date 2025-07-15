from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import json
import logging
from dataclasses import dataclass

from ..database import get_db, AgentCRUD

@dataclass
class AgentMessage:
    """Message structure for agent communication"""
    id: str
    sender: str
    recipient: str
    action: str
    data: Dict[str, Any]
    timestamp: datetime
    correlation_id: Optional[str] = None

class BaseAgent(ABC):
    """Base class for all Dreamcatcher agents"""
    
    def __init__(self, agent_id: str, name: str, description: str = '', version: str = '1.0.0'):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.version = version
        self.is_active = True
        self.config = {}
        self.logger = logging.getLogger(f"agent.{agent_id}")
        
        # Performance tracking
        self.total_processed = 0
        self.success_count = 0
        self.failure_count = 0
        
        # Message queue for async processing
        self.message_queue = asyncio.Queue()
        
        # Register agent in database
        self._register_agent()
        
        # Register with agent registry
        from . import agent_registry
        agent_registry.register(self)
    
    def _register_agent(self):
        """Register agent in database"""
        try:
            with get_db() as db:
                AgentCRUD.create_or_update_agent(
                    db=db,
                    agent_id=self.agent_id,
                    name=self.name,
                    description=self.description,
                    version=self.version,
                    config=self.config
                )
                self.logger.info(f"Agent {self.agent_id} registered successfully")
        except Exception as e:
            self.logger.error(f"Failed to register agent {self.agent_id}: {e}")
    
    @abstractmethod
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming data and return result
        Must be implemented by all agent subclasses
        """
        pass
    
    async def handle_message(self, message: AgentMessage) -> Optional[Dict[str, Any]]:
        """Handle incoming message"""
        started_at = datetime.utcnow()
        
        try:
            self.logger.info(f"Processing message {message.id} from {message.sender}")
            
            # Log activity start
            with get_db() as db:
                AgentCRUD.log_agent_activity(
                    db=db,
                    agent_id=self.agent_id,
                    action=message.action,
                    status='started',
                    idea_id=message.data.get('idea_id'),
                    input_data=message.data,
                    started_at=started_at
                )
            
            # Process the message
            result = await self.process(message.data)
            
            completed_at = datetime.utcnow()
            
            # Log successful completion
            with get_db() as db:
                AgentCRUD.log_agent_activity(
                    db=db,
                    agent_id=self.agent_id,
                    action=message.action,
                    status='completed',
                    idea_id=message.data.get('idea_id'),
                    input_data=message.data,
                    output_data=result,
                    started_at=started_at,
                    completed_at=completed_at
                )
            
            self.success_count += 1
            self.total_processed += 1
            
            return result
            
        except Exception as e:
            completed_at = datetime.utcnow()
            self.logger.error(f"Error processing message {message.id}: {e}")
            
            # Log failure
            with get_db() as db:
                AgentCRUD.log_agent_activity(
                    db=db,
                    agent_id=self.agent_id,
                    action=message.action,
                    status='failed',
                    idea_id=message.data.get('idea_id'),
                    input_data=message.data,
                    error_message=str(e),
                    started_at=started_at,
                    completed_at=completed_at
                )
            
            self.failure_count += 1
            self.total_processed += 1
            
            return None
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        return {
            'agent_id': self.agent_id,
            'total_processed': self.total_processed,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'success_rate': self.success_count / self.total_processed if self.total_processed > 0 else 0,
            'is_active': self.is_active
        }
    
    def update_config(self, config: Dict[str, Any]):
        """Update agent configuration"""
        self.config.update(config)
        self._register_agent()  # Update in database
    
    def activate(self):
        """Activate agent"""
        self.is_active = True
        self.logger.info(f"Agent {self.agent_id} activated")
    
    def deactivate(self):
        """Deactivate agent"""
        self.is_active = False
        self.logger.info(f"Agent {self.agent_id} deactivated")
    
    async def start(self):
        """Start the agent message processing loop"""
        self.logger.info(f"Starting agent {self.agent_id}")
        
        while self.is_active:
            try:
                # Wait for message with timeout
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                
                # Process the message
                result = await self.handle_message(message)
                
                # Mark task as done
                self.message_queue.task_done()
                
                # If this was a request that expects a response, handle it
                if message.correlation_id:
                    await self._send_response(message, result)
                    
            except asyncio.TimeoutError:
                # No message received, continue loop
                continue
            except Exception as e:
                self.logger.error(f"Error in agent loop: {e}")
                await asyncio.sleep(1)  # Brief pause before continuing
    
    async def send_message(self, recipient: str, action: str, data: Dict[str, Any], correlation_id: Optional[str] = None):
        """Send message to another agent"""
        message = AgentMessage(
            id=f"{self.agent_id}_{datetime.utcnow().timestamp()}",
            sender=self.agent_id,
            recipient=recipient,
            action=action,
            data=data,
            timestamp=datetime.utcnow(),
            correlation_id=correlation_id
        )
        
        # In a real implementation, this would use a message bus (Redis, RabbitMQ, etc.)
        # For now, we'll implement a simple registry-based approach
        await self._deliver_message(message)
    
    async def _deliver_message(self, message: AgentMessage):
        """Deliver message to target agent via registry"""
        from . import agent_registry
        try:
            await agent_registry.send_message(message)
            self.logger.info(f"Delivered message {message.id} to {message.recipient}")
        except Exception as e:
            self.logger.error(f"Failed to deliver message {message.id}: {e}")
    
    async def _send_response(self, original_message: AgentMessage, result: Optional[Dict[str, Any]]):
        """Send response back to original sender"""
        if result:
            await self.send_message(
                recipient=original_message.sender,
                action=f"{original_message.action}_response",
                data=result,
                correlation_id=original_message.correlation_id
            )
    
    def __str__(self):
        return f"Agent({self.agent_id}, {self.name}, active={self.is_active})"
    
    def __repr__(self):
        return self.__str__()


class AgentRegistry:
    """Registry for managing agent instances"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.logger = logging.getLogger("agent_registry")
    
    def register(self, agent: BaseAgent):
        """Register an agent"""
        self.agents[agent.agent_id] = agent
        self.logger.info(f"Registered agent: {agent.agent_id}")
    
    def unregister(self, agent_id: str):
        """Unregister an agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            self.logger.info(f"Unregistered agent: {agent_id}")
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    def get_all_agents(self) -> List[BaseAgent]:
        """Get all registered agents"""
        return list(self.agents.values())
    
    def get_active_agents(self) -> List[BaseAgent]:
        """Get all active agents"""
        return [agent for agent in self.agents.values() if agent.is_active]
    
    async def broadcast_message(self, sender: str, action: str, data: Dict[str, Any]):
        """Broadcast message to all active agents"""
        for agent in self.get_active_agents():
            if agent.agent_id != sender:
                message = AgentMessage(
                    id=f"broadcast_{datetime.utcnow().timestamp()}",
                    sender=sender,
                    recipient=agent.agent_id,
                    action=action,
                    data=data,
                    timestamp=datetime.utcnow()
                )
                await agent.message_queue.put(message)
    
    async def send_message(self, message: AgentMessage):
        """Send message to specific agent"""
        target_agent = self.get_agent(message.recipient)
        if target_agent and target_agent.is_active:
            await target_agent.message_queue.put(message)
        else:
            self.logger.warning(f"Agent {message.recipient} not found or inactive")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        agents = self.get_all_agents()
        active_count = len(self.get_active_agents())
        
        return {
            'total_agents': len(agents),
            'active_agents': active_count,
            'inactive_agents': len(agents) - active_count,
            'agent_performance': [agent.get_performance_metrics() for agent in agents]
        }

# Global agent registry instance
agent_registry = AgentRegistry()