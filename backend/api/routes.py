from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
import asyncio
import logging
from datetime import datetime
import tempfile
import os

from ..database import get_db, IdeaCRUD, ProposalCRUD, AgentCRUD
from ..database.models import User
from ..agents import agent_registry, AgentListener, AgentClassifier
from ..services import AIService, AudioProcessor
from .websocket_manager import WebSocketManager
from .auth_routes import get_current_user
from .models import (
    CaptureTextRequest, CaptureVoiceResponse, CaptureTextResponse,
    IdeaResponse, ProposalResponse, AgentStatusResponse
)

# Initialize router
router = APIRouter()
security = HTTPBearer()

# Initialize services
audio_processor = AudioProcessor()
ai_service = AIService()
ws_manager = WebSocketManager()

# Setup logging
logger = logging.getLogger("api.routes")

# Initialize agents
listener_agent = AgentListener()
classifier_agent = AgentClassifier()

# Register agents
agent_registry.register(listener_agent)
agent_registry.register(classifier_agent)

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "agents": len(agent_registry.get_active_agents()),
        "services": {
            "ai": ai_service.is_available(),
            "audio": True,
            "database": True  # Would check db connection in real implementation
        }
    }

# Voice capture endpoint
@router.post("/capture/voice", response_model=CaptureVoiceResponse)
async def capture_voice(
    audio_file: UploadFile = File(...),
    urgency: str = Form("normal"),
    location: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Capture voice input and process it"""
    try:
        # Validate file type
        if not audio_file.filename.lower().endswith(('.wav', '.mp3', '.ogg', '.webm')):
            raise HTTPException(status_code=400, detail="Unsupported audio format")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            content = await audio_file.read()
            tmp_file.write(content)
            tmp_file.flush()
            
            # Process audio
            audio_result = await audio_processor.process_audio_file(tmp_file.name)
            
            # Send to listener agent
            result = await listener_agent.handle_message(
                type('',(object,),{
                    'id': f'voice_{datetime.utcnow().timestamp()}',
                    'sender': 'api',
                    'recipient': 'listener',
                    'action': 'process',
                    'data': {
                        'type': 'voice',
                        'audio_file': tmp_file.name,
                        'urgency': urgency,
                        'location_data': {'location': location} if location else {},
                        'device_info': {'source': 'api_upload'},
                        'user_id': current_user.id
                    },
                    'timestamp': datetime.utcnow()
                })()
            )
            
            # Clean up temp file
            os.unlink(tmp_file.name)
            
            if result and result.get('success'):
                # Notify WebSocket clients
                await ws_manager.broadcast({
                    'type': 'idea_captured',
                    'idea_id': result['idea_id'],
                    'source': 'voice',
                    'content': result.get('transcription', '')
                })
                
                return CaptureVoiceResponse(
                    success=True,
                    idea_id=result['idea_id'],
                    transcription=result.get('transcription', ''),
                    audio_quality=audio_result.get('quality_metrics', {}),
                    message=result.get('message', 'Voice captured successfully')
                )
            else:
                raise HTTPException(status_code=500, detail=result.get('error', 'Processing failed'))
                
    except Exception as e:
        logger.error(f"Voice capture failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Text capture endpoint
@router.post("/capture/text", response_model=CaptureTextResponse)
async def capture_text(
    request: CaptureTextRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Capture text input and process it"""
    try:
        # Send to listener agent
        result = await listener_agent.handle_message(
            type('',(object,),{
                'id': f'text_{datetime.utcnow().timestamp()}',
                'sender': 'api',
                'recipient': 'listener',
                'action': 'process',
                'data': {
                    'type': 'text',
                    'content': request.content,
                    'urgency': request.urgency,
                    'location_data': {'location': request.location} if request.location else {},
                    'device_info': {'source': 'api_text'},
                    'user_id': current_user.id
                },
                'timestamp': datetime.utcnow()
            })()
        )
        
        if result and result.get('success'):
            # Notify WebSocket clients
            await ws_manager.broadcast({
                'type': 'idea_captured',
                'idea_id': result['idea_id'],
                'source': 'text',
                'content': request.content
            })
            
            return CaptureTextResponse(
                success=True,
                idea_id=result['idea_id'],
                urgency_score=result.get('urgency_score', 50.0),
                message=result.get('message', 'Text captured successfully')
            )
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Processing failed'))
            
    except Exception as e:
        logger.error(f"Text capture failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Dream capture endpoint
@router.post("/capture/dream")
async def capture_dream(
    content: str = Form(...),
    dream_type: str = Form("regular"),
    sleep_stage: str = Form("unknown"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Capture dream log entry"""
    try:
        result = await listener_agent.handle_message(
            type('',(object,),{
                'id': f'dream_{datetime.utcnow().timestamp()}',
                'sender': 'api',
                'recipient': 'listener',
                'action': 'process',
                'data': {
                    'type': 'dream',
                    'content': content,
                    'dream_type': dream_type,
                    'sleep_stage': sleep_stage,
                    'user_id': current_user.id
                },
                'timestamp': datetime.utcnow()
            })()
        )
        
        if result and result.get('success'):
            await ws_manager.broadcast({
                'type': 'dream_captured',
                'idea_id': result['idea_id'],
                'dream_type': dream_type,
                'content': content
            })
            
            return {
                'success': True,
                'idea_id': result['idea_id'],
                'dream_type': dream_type,
                'message': result.get('message', 'Dream logged successfully')
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Processing failed'))
            
    except Exception as e:
        logger.error(f"Dream capture failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Get ideas endpoint
@router.get("/ideas", response_model=List[IdeaResponse])
async def get_ideas(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    source_type: Optional[str] = None,
    min_urgency: Optional[float] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get ideas with filtering"""
    try:
        ideas = IdeaCRUD.get_ideas(
            db=db,
            skip=skip,
            limit=limit,
            category=category,
            source_type=source_type,
            min_urgency=min_urgency,
            search=search
        )
        
        return [
            IdeaResponse(
                id=idea.id,
                content=idea.content_transcribed or idea.content_raw,
                source_type=idea.source_type,
                category=idea.category,
                urgency_score=idea.urgency_score or 0.0,
                novelty_score=idea.novelty_score or 0.0,
                created_at=idea.created_at,
                updated_at=idea.updated_at,
                processing_status=idea.processing_status,
                tags=[tag.name for tag in idea.tags] if idea.tags else []
            )
            for idea in ideas
        ]
        
    except Exception as e:
        logger.error(f"Failed to get ideas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Get specific idea
@router.get("/ideas/{idea_id}", response_model=IdeaResponse)
async def get_idea(idea_id: str, db: Session = Depends(get_db)):
    """Get specific idea by ID"""
    try:
        idea = IdeaCRUD.get_idea(db, idea_id)
        if not idea:
            raise HTTPException(status_code=404, detail="Idea not found")
        
        return IdeaResponse(
            id=idea.id,
            content=idea.content_transcribed or idea.content_raw,
            source_type=idea.source_type,
            category=idea.category,
            urgency_score=idea.urgency_score or 0.0,
            novelty_score=idea.novelty_score or 0.0,
            created_at=idea.created_at,
            updated_at=idea.updated_at,
            processing_status=idea.processing_status,
            tags=[tag.name for tag in idea.tags] if idea.tags else [],
            expansions=[exp.expanded_content for exp in idea.expansions] if idea.expansions else [],
            visuals=[{'path': vis.image_path, 'prompt': vis.prompt_used} for vis in idea.visuals] if idea.visuals else []
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get idea {idea_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Update idea endpoint
@router.put("/ideas/{idea_id}", response_model=IdeaResponse)
async def update_idea(
    idea_id: str,
    content: Optional[str] = None,
    category: Optional[str] = None,
    urgency_score: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Update an existing idea"""
    try:
        update_data = {}
        if content:
            update_data['content_processed'] = content
        if category:
            update_data['category'] = category
        if urgency_score is not None:
            update_data['urgency_score'] = urgency_score
        
        idea = IdeaCRUD.update_idea(db, idea_id, **update_data)
        if not idea:
            raise HTTPException(status_code=404, detail="Idea not found")
        
        # Notify WebSocket clients
        await ws_manager.broadcast({
            'type': 'idea_updated',
            'idea_id': idea_id,
            'updates': update_data
        })
        
        return IdeaResponse(
            id=idea.id,
            content=idea.content_transcribed or idea.content_raw,
            source_type=idea.source_type,
            category=idea.category,
            urgency_score=idea.urgency_score or 0.0,
            novelty_score=idea.novelty_score or 0.0,
            created_at=idea.created_at,
            updated_at=idea.updated_at,
            processing_status=idea.processing_status,
            tags=[tag.name for tag in idea.tags] if idea.tags else []
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update idea {idea_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Delete idea endpoint
@router.delete("/ideas/{idea_id}")
async def delete_idea(idea_id: str, db: Session = Depends(get_db)):
    """Delete an idea"""
    try:
        success = IdeaCRUD.delete_idea(db, idea_id)
        if not success:
            raise HTTPException(status_code=404, detail="Idea not found")
        
        # Notify WebSocket clients
        await ws_manager.broadcast({
            'type': 'idea_deleted',
            'idea_id': idea_id
        })
        
        return {
            'success': True,
            'idea_id': idea_id,
            'message': 'Idea deleted successfully'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete idea {idea_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Archive idea endpoint
@router.post("/ideas/{idea_id}/archive")
async def archive_idea(
    idea_id: str,
    reason: str = Form(""),
    db: Session = Depends(get_db)
):
    """Archive an idea"""
    try:
        idea = IdeaCRUD.archive_idea(db, idea_id, reason)
        if not idea:
            raise HTTPException(status_code=404, detail="Idea not found")
        
        # Notify WebSocket clients
        await ws_manager.broadcast({
            'type': 'idea_archived',
            'idea_id': idea_id,
            'reason': reason
        })
        
        return {
            'success': True,
            'idea_id': idea_id,
            'archived_reason': reason,
            'message': 'Idea archived successfully'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to archive idea {idea_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Expand idea endpoint
@router.post("/ideas/{idea_id}/expand")
async def expand_idea(
    idea_id: str,
    expansion_type: str = Form("detailed"),
    db: Session = Depends(get_db)
):
    """Manually trigger idea expansion"""
    try:
        idea = IdeaCRUD.get_idea(db, idea_id)
        if not idea:
            raise HTTPException(status_code=404, detail="Idea not found")
        
        # Send expansion request to appropriate agent
        from ..agents import agent_registry
        expander_agent = agent_registry.get_agent('expander')
        if not expander_agent:
            raise HTTPException(status_code=503, detail="Expander agent not available")
        
        # Create expansion message
        from ..agents.base_agent import AgentMessage
        message = AgentMessage(
            id=f"expand_{idea_id}_{datetime.utcnow().timestamp()}",
            sender='api',
            recipient='expander',
            action='expand',
            data={
                'idea_id': idea_id,
                'expansion_type': expansion_type,
                'content': idea.content_transcribed or idea.content_raw
            },
            timestamp=datetime.utcnow()
        )
        
        result = await expander_agent.handle_message(message)
        
        if result and result.get('success'):
            # Notify WebSocket clients
            await ws_manager.broadcast({
                'type': 'idea_expanded',
                'idea_id': idea_id,
                'expansion_type': expansion_type,
                'expansion_id': result.get('expansion_id')
            })
            
            return {
                'success': True,
                'idea_id': idea_id,
                'expansion_type': expansion_type,
                'expansion_id': result.get('expansion_id'),
                'message': 'Idea expansion triggered successfully'
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Expansion failed'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to expand idea {idea_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Get idea visuals endpoint
@router.get("/ideas/{idea_id}/visuals")
async def get_idea_visuals(idea_id: str, db: Session = Depends(get_db)):
    """Get visuals for an idea"""
    try:
        from ..database import VisualCRUD
        visuals = VisualCRUD.get_visuals_for_idea(db, idea_id)
        
        return {
            'idea_id': idea_id,
            'visuals': [
                {
                    'id': visual.id,
                    'image_path': visual.image_path,
                    'prompt_used': visual.prompt_used,
                    'quality_score': visual.quality_score,
                    'is_approved': visual.is_approved,
                    'created_at': visual.created_at.isoformat()
                }
                for visual in visuals
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get visuals for idea {idea_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Get idea expansions endpoint
@router.get("/ideas/{idea_id}/expansions")
async def get_idea_expansions(idea_id: str, db: Session = Depends(get_db)):
    """Get expansions for an idea"""
    try:
        from ..database import ExpansionCRUD
        expansions = ExpansionCRUD.get_expansions_for_idea(db, idea_id)
        
        return {
            'idea_id': idea_id,
            'expansions': [
                {
                    'id': expansion.id,
                    'expanded_content': expansion.expanded_content,
                    'expansion_type': expansion.expansion_type,
                    'prompt_used': expansion.prompt_used,
                    'agent_version': expansion.agent_version,
                    'created_at': expansion.created_at.isoformat()
                }
                for expansion in expansions
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get expansions for idea {idea_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Get proposals endpoint
@router.get("/proposals", response_model=List[ProposalResponse])
async def get_proposals(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get proposals with filtering"""
    try:
        if status == "pending":
            proposals = ProposalCRUD.get_pending_proposals(db)
        else:
            # Get all proposals with basic filtering
            proposals = db.query(Proposal).offset(skip).limit(limit).all()
        
        return [
            ProposalResponse(
                id=proposal.id,
                title=proposal.title,
                description=proposal.description,
                status=proposal.status,
                created_at=proposal.created_at,
                idea_id=proposal.idea_id,
                generated_by=proposal.generated_by
            )
            for proposal in proposals
        ]
        
    except Exception as e:
        logger.error(f"Failed to get proposals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Approve proposal endpoint
@router.post("/proposals/{proposal_id}/approve")
async def approve_proposal(
    proposal_id: str,
    notes: str = Form(""),
    db: Session = Depends(get_db)
):
    """Approve a proposal"""
    try:
        proposal = ProposalCRUD.approve_proposal(db, proposal_id, notes)
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")
        
        # Notify WebSocket clients
        await ws_manager.broadcast({
            'type': 'proposal_approved',
            'proposal_id': proposal_id,
            'title': proposal.title
        })
        
        return {
            'success': True,
            'proposal_id': proposal_id,
            'status': proposal.status,
            'message': 'Proposal approved successfully'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve proposal {proposal_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Agent status endpoint
@router.get("/agents/status", response_model=List[AgentStatusResponse])
async def get_agent_status():
    """Get status of all agents"""
    try:
        agents = agent_registry.get_all_agents()
        
        return [
            AgentStatusResponse(
                agent_id=agent.agent_id,
                name=agent.name,
                is_active=agent.is_active,
                total_processed=agent.total_processed,
                success_rate=agent.success_count / agent.total_processed if agent.total_processed > 0 else 0,
                version=agent.version
            )
            for agent in agents
        ]
        
    except Exception as e:
        logger.error(f"Failed to get agent status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Send message to agent endpoint
@router.post("/agents/{agent_id}/message")
async def send_agent_message(
    agent_id: str,
    action: str = Form(...),
    data: str = Form(...),
    db: Session = Depends(get_db)
):
    """Send a message to a specific agent"""
    try:
        agent = agent_registry.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Parse data JSON
        try:
            message_data = json.loads(data)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON data")
        
        # Create message
        from ..agents.base_agent import AgentMessage
        message = AgentMessage(
            id=f"api_{agent_id}_{datetime.utcnow().timestamp()}",
            sender='api',
            recipient=agent_id,
            action=action,
            data=message_data,
            timestamp=datetime.utcnow()
        )
        
        # Send message
        result = await agent.handle_message(message)
        
        return {
            'success': True,
            'agent_id': agent_id,
            'action': action,
            'result': result,
            'message': 'Message sent successfully'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send message to agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Get agent logs endpoint
@router.get("/agents/{agent_id}/logs")
async def get_agent_logs(
    agent_id: str,
    hours: int = 24,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get logs for a specific agent"""
    try:
        from ..database import AgentLogCRUD
        logs = AgentLogCRUD.get_agent_logs(db, agent_id, status, hours)
        
        return {
            'agent_id': agent_id,
            'logs': [
                {
                    'id': log.id,
                    'action': log.action,
                    'status': log.status,
                    'started_at': log.started_at.isoformat(),
                    'completed_at': log.completed_at.isoformat() if log.completed_at else None,
                    'processing_time': log.processing_time,
                    'input_data': log.input_data,
                    'output_data': log.output_data,
                    'error_message': log.error_message
                }
                for log in logs
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get logs for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Get system metrics endpoint
@router.get("/metrics")
async def get_system_metrics(
    metric_name: Optional[str] = None,
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get system metrics"""
    try:
        from ..database import SystemMetricsCRUD
        metrics = SystemMetricsCRUD.get_metrics(db, metric_name, hours)
        
        return {
            'metrics': [
                {
                    'metric_name': metric.metric_name,
                    'metric_value': metric.metric_value,
                    'metric_type': metric.metric_type,
                    'timestamp': metric.timestamp.isoformat(),
                    'metadata': metric.metadata
                }
                for metric in metrics
            ],
            'count': len(metrics)
        }
        
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Get error summary endpoint
@router.get("/errors")
async def get_error_summary(hours: int = 24, db: Session = Depends(get_db)):
    """Get error summary"""
    try:
        from ..database import AgentLogCRUD
        error_logs = AgentLogCRUD.get_error_logs(db, hours)
        
        # Group errors by agent
        errors_by_agent = {}
        for log in error_logs:
            if log.agent_id not in errors_by_agent:
                errors_by_agent[log.agent_id] = []
            errors_by_agent[log.agent_id].append({
                'action': log.action,
                'error_message': log.error_message,
                'timestamp': log.started_at.isoformat()
            })
        
        return {
            'total_errors': len(error_logs),
            'errors_by_agent': errors_by_agent,
            'recent_errors': [
                {
                    'agent_id': log.agent_id,
                    'action': log.action,
                    'error_message': log.error_message,
                    'timestamp': log.started_at.isoformat()
                }
                for log in error_logs[:20]  # Last 20 errors
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get error summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# System stats endpoint
@router.get("/stats")
async def get_system_stats(db: Session = Depends(get_db)):
    """Get system statistics"""
    try:
        # Get idea stats
        ideas = IdeaCRUD.get_ideas(db, limit=1000)
        
        # Get classification stats
        classifier_stats = classifier_agent.get_classification_stats()
        
        # Get agent system status
        agent_status = agent_registry.get_system_status()
        
        return {
            'ideas': {
                'total': len(ideas),
                'by_source': {
                    'voice': len([i for i in ideas if i.source_type == 'voice']),
                    'text': len([i for i in ideas if i.source_type == 'text']),
                    'dream': len([i for i in ideas if i.source_type == 'dream'])
                },
                'high_urgency': len([i for i in ideas if (i.urgency_score or 0) > 80])
            },
            'classification': classifier_stats,
            'agents': agent_status,
            'services': {
                'ai_available': ai_service.is_available(),
                'ai_models': ai_service.get_available_models()
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time updates
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await ws_manager.connect(websocket)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            
            # Handle ping/pong or other client messages
            if data == "ping":
                await websocket.send_text("pong")
            
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)