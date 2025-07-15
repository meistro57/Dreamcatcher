from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Request Models
class CaptureTextRequest(BaseModel):
    content: str = Field(..., description="The text content to capture")
    urgency: str = Field("normal", description="Urgency level: low, normal, high, urgent, emergency")
    location: Optional[str] = Field(None, description="Optional location context")

class CaptureVoiceRequest(BaseModel):
    urgency: str = Field("normal", description="Urgency level")
    location: Optional[str] = Field(None, description="Optional location context")

# Response Models
class CaptureVoiceResponse(BaseModel):
    success: bool
    idea_id: str
    transcription: str
    audio_quality: Dict[str, Any] = Field(default_factory=dict)
    message: str

class CaptureTextResponse(BaseModel):
    success: bool
    idea_id: str
    urgency_score: float
    message: str

class IdeaResponse(BaseModel):
    id: str
    content: str
    source_type: str
    category: Optional[str] = None
    urgency_score: float = 0.0
    novelty_score: float = 0.0
    created_at: datetime
    updated_at: datetime
    processing_status: str
    tags: List[str] = Field(default_factory=list)
    expansions: List[str] = Field(default_factory=list)
    visuals: List[Dict[str, Any]] = Field(default_factory=list)

class ProposalResponse(BaseModel):
    id: str
    title: str
    description: str
    status: str
    created_at: datetime
    idea_id: str
    generated_by: str

class AgentStatusResponse(BaseModel):
    agent_id: str
    name: str
    is_active: bool
    total_processed: int
    success_rate: float
    version: str

class TagResponse(BaseModel):
    id: int
    name: str
    color: str
    description: str = ""

class ExpansionResponse(BaseModel):
    id: str
    expanded_content: str
    expansion_type: str
    created_at: datetime

class VisualResponse(BaseModel):
    id: str
    image_path: str
    prompt_used: str
    quality_score: float
    is_approved: bool
    created_at: datetime

# WebSocket Message Models
class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class IdeaCapturedMessage(BaseModel):
    type: str = "idea_captured"
    idea_id: str
    source: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ProposalGeneratedMessage(BaseModel):
    type: str = "proposal_generated"
    proposal_id: str
    idea_id: str
    title: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AgentStatusMessage(BaseModel):
    type: str = "agent_status"
    agent_id: str
    status: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Error Models
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# System Models
class SystemStatsResponse(BaseModel):
    ideas: Dict[str, Any]
    classification: Dict[str, Any]
    agents: Dict[str, Any]
    services: Dict[str, Any]
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    agents: int
    services: Dict[str, bool]