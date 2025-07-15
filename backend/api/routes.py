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
from ..agents import agent_registry, AgentListener, AgentClassifier
from ..services import AIService, AudioProcessor
from .websocket_manager import WebSocketManager
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
                        'device_info': {'source': 'api_upload'}
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
                    'device_info': {'source': 'api_text'}
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
                    'sleep_stage': sleep_stage
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