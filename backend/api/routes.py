from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel
import json
import asyncio
import logging
from datetime import datetime
import tempfile
import os
from pathlib import Path
from importlib import import_module
from uuid import uuid4

try:  # pragma: no cover - import flexibility for tests and runtime
    from ..database import get_db_dependency, IdeaCRUD, ProposalCRUD, AgentCRUD, AgentLogCRUD, SystemMetricsCRUD
    from ..database.models import User
    from ..agents import agent_registry, AgentListener, AgentClassifier
    from ..agents.base_agent import AgentMessage
    from ..agents.agent_semantic import semantic_agent
    from ..services.embedding_service import embedding_service
    from ..services import AIService, AudioProcessor
    from .websocket_manager import WebSocketManager
    from .auth_routes import get_current_user
    from .models import (
        CaptureTextRequest, CaptureVoiceResponse, CaptureTextResponse, IdeaCreateRequest,
        IdeaResponse, ProposalResponse, AgentStatusResponse
    )
except ImportError:  # pragma: no cover - fallback when run as script
    from database import get_db_dependency, IdeaCRUD, ProposalCRUD, AgentCRUD, AgentLogCRUD, SystemMetricsCRUD
    from database.models import User
    from agents import agent_registry, AgentListener, AgentClassifier
    from agents.base_agent import AgentMessage
    from agents.agent_semantic import semantic_agent
    from services.embedding_service import embedding_service
    from services import AIService, AudioProcessor
    from api.websocket_manager import WebSocketManager
    from api.auth_routes import get_current_user
    from api.models import (
        CaptureTextRequest, CaptureVoiceResponse, CaptureTextResponse, IdeaCreateRequest,
        IdeaResponse, ProposalResponse, AgentStatusResponse
    )

# Constants
MAX_AUDIO_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_TEXT_LENGTH = 10000

# Enums for validation
class UrgencyLevel(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"
    critical = "critical"


class ApiKeysUpdateRequest(BaseModel):
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    persist_to_env: bool = False


class AiModelUpdateRequest(BaseModel):
    model: str
    persist_to_env: bool = False

# Initialize router
router = APIRouter()
security = HTTPBearer()

# Initialize services
audio_processor = AudioProcessor()
ai_service = AIService()
ws_manager = WebSocketManager()

# Setup logging
logger = logging.getLogger("api.routes")

SYSTEM_ACTION_TIMEOUT_SECONDS = 900
SYSTEM_ACTION_HISTORY_DEFAULT_LIMIT = 50
SYSTEM_ACTION_HISTORY_MAX_LIMIT = 500

# Initialize agents
listener_agent = AgentListener()
classifier_agent = AgentClassifier()

def _register_agent_safely(module_path: str, class_name: str, agent_name: str):
    """Register optional agents without failing API startup."""
    try:
        agent_module = import_module(module_path)
        agent_factory = getattr(agent_module, class_name)
        agent_registry.register(agent_factory())
        logger.info(f"Registered agent: {agent_name}")
    except Exception as e:
        logger.warning(f"Skipping agent {agent_name}: {e}")

# Register core agents
agent_registry.register(listener_agent)
agent_registry.register(classifier_agent)
agent_registry.register(semantic_agent)

# Register additional runtime agents
_register_agent_safely("agents.agent_expander", "AgentExpander", "expander")
_register_agent_safely("agents.agent_proposer", "AgentProposer", "proposer")
_register_agent_safely("agents.agent_reviewer", "AgentReviewer", "reviewer")
_register_agent_safely("agents.agent_visualizer", "AgentVisualizer", "visualizer")
_register_agent_safely("agents.agent_meta", "AgentMeta", "meta")

def _is_system_actions_enabled_for_user(current_user: User) -> bool:
    enabled = os.getenv("ENABLE_SYSTEM_ACTIONS", "false").lower() == "true"
    if not enabled:
        return False

    allowed_users_raw = os.getenv("SYSTEM_ACTION_USERS", "admin")
    allowed_users = {item.strip() for item in allowed_users_raw.split(",") if item.strip()}
    username = getattr(current_user, "username", None)

    if "*" in allowed_users:
        return True
    if username and username in allowed_users:
        return True

    return False

def _resolve_compose_file() -> Optional[Path]:
    candidates = [
        Path.cwd() / "docker-compose.local.yml",
        Path.cwd().parent / "docker-compose.local.yml",
        Path("/home/mark/Dreamcatcher/docker-compose.local.yml"),
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None

def _resolve_env_file() -> Optional[Path]:
    candidates = [
        Path.cwd() / ".env",
        Path.cwd().parent / ".env",
        Path("/home/mark/Dreamcatcher/.env"),
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _resolve_system_action_audit_file() -> Path:
    configured = os.getenv("SYSTEM_ACTION_AUDIT_FILE")
    if configured:
        return Path(configured)

    candidates = [
        Path.cwd() / "logs" / "system_actions_audit.jsonl",
        Path.cwd().parent / "logs" / "system_actions_audit.jsonl",
        Path("/home/mark/Dreamcatcher/logs/system_actions_audit.jsonl"),
    ]
    for candidate in candidates:
        parent = candidate.parent
        if parent.exists():
            return candidate

    return Path.cwd() / "logs" / "system_actions_audit.jsonl"


def _append_system_action_audit(entry: Dict[str, Any]) -> None:
    try:
        audit_path = _resolve_system_action_audit_file()
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        with audit_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, default=str) + "\n")
    except Exception as exc:
        logger.warning(f"Failed to write system action audit entry: {exc}")


def _read_system_action_audit(limit: int, status: Optional[str] = None) -> List[Dict[str, Any]]:
    audit_path = _resolve_system_action_audit_file()
    if not audit_path.exists():
        return []

    entries: List[Dict[str, Any]] = []
    try:
        lines = audit_path.read_text(encoding="utf-8").splitlines()
    except Exception as exc:
        logger.warning(f"Failed to read system action audit log: {exc}")
        return []

    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue

        if status and item.get("status") != status:
            continue

        entries.append(item)
        if len(entries) >= limit:
            break

    return entries

def _persist_env_values(updates: Dict[str, str]) -> Optional[Path]:
    env_file = _resolve_env_file()
    if not env_file:
        return None

    try:
        original_text = env_file.read_text(encoding="utf-8")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read env file: {exc}")

    lines = original_text.splitlines()
    keys_remaining = set(updates.keys())
    updated_lines: List[str] = []

    for line in lines:
        line_out = line
        for key in list(keys_remaining):
            if line.startswith(f"{key}="):
                line_out = f"{key}={updates[key]}"
                keys_remaining.remove(key)
                break
        updated_lines.append(line_out)

    for key in keys_remaining:
        updated_lines.append(f"{key}={updates[key]}")

    try:
        env_file.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to write env file: {exc}")

    return env_file

def _get_system_action_steps() -> Dict[str, List[List[str]]]:
    compose_file = _resolve_compose_file()
    if not compose_file:
        return {}

    compose = ["docker", "compose", "-f", str(compose_file)]
    return {
        "restart_backend": [compose + ["restart", "backend"]],
        "rebuild_backend": [compose + ["build", "backend"], compose + ["up", "-d", "backend"]],
        "restart_frontend": [compose + ["restart", "frontend"]],
        "rebuild_frontend": [compose + ["build", "frontend"], compose + ["up", "-d", "frontend"]],
        "restart_stack": [compose + ["restart"]],
        "rebuild_stack": [compose + ["build", "backend", "frontend"], compose + ["up", "-d", "backend", "frontend"]],
    }

async def _run_system_action(action: str) -> Dict[str, Any]:
    steps = _get_system_action_steps().get(action)
    if not steps:
        raise HTTPException(status_code=400, detail=f"Unsupported action: {action}")

    outputs: List[Dict[str, Any]] = []
    for step in steps:
        process = await asyncio.create_subprocess_exec(
            *step,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=SYSTEM_ACTION_TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            process.kill()
            await process.communicate()
            raise HTTPException(status_code=504, detail=f"Action timed out while running: {' '.join(step)}")

        stdout_text = stdout.decode(errors="replace")
        stderr_text = stderr.decode(errors="replace")
        outputs.append({
            "command": " ".join(step),
            "return_code": process.returncode,
            "stdout": stdout_text[-8000:],
            "stderr": stderr_text[-8000:]
        })

        if process.returncode != 0:
            return {
                "success": False,
                "action": action,
                "steps": outputs
            }

    return {
        "success": True,
        "action": action,
        "steps": outputs
    }

# Health check endpoint
@router.get("/health")
async def health_check(db: Session = Depends(get_db_dependency)):
    """Health check endpoint"""
    # Check database health
    db_healthy = False
    try:
        # Simple query to test database connection
        db.execute(text("SELECT 1"))
        db_healthy = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_healthy = False

    return {
        "status": "healthy" if db_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "agents": len(agent_registry.get_active_agents()),
        "services": {
            "ai": ai_service.is_available(),
            "audio": True,
            "database": db_healthy
        }
    }

@router.get("/system/actions")
async def get_system_actions_status(current_user: User = Depends(get_current_user)):
    """Get available system actions for this runtime."""
    enabled_for_user = _is_system_actions_enabled_for_user(current_user)
    actions = sorted(list(_get_system_action_steps().keys())) if enabled_for_user else []

    return {
        "enabled": enabled_for_user,
        "actions": actions,
        "message": (
            "System actions available"
            if enabled_for_user
            else "System actions are disabled. Set ENABLE_SYSTEM_ACTIONS=true and include your username in SYSTEM_ACTION_USERS."
        )
    }


@router.get("/system/actions/history")
async def get_system_actions_history(
    limit: int = SYSTEM_ACTION_HISTORY_DEFAULT_LIMIT,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Return recent system action execution history for authorized users."""
    if not _is_system_actions_enabled_for_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="System actions disabled for this user. Configure ENABLE_SYSTEM_ACTIONS and SYSTEM_ACTION_USERS."
        )

    if status and status not in {"success", "failed"}:
        raise HTTPException(status_code=400, detail="status must be either 'success' or 'failed'")

    sanitized_limit = max(1, min(limit, SYSTEM_ACTION_HISTORY_MAX_LIMIT))
    entries = _read_system_action_audit(sanitized_limit, status=status)
    return {"count": len(entries), "entries": entries}

@router.post("/system/actions/{action}")
async def run_system_action(action: str, current_user: User = Depends(get_current_user)):
    """Run a guarded system action such as restart/rebuild."""
    if not _is_system_actions_enabled_for_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="System actions disabled for this user. Configure ENABLE_SYSTEM_ACTIONS and SYSTEM_ACTION_USERS."
        )

    started_at = datetime.utcnow()
    actor = getattr(current_user, "username", None) or getattr(current_user, "email", "unknown")
    audit_id = str(uuid4())

    try:
        result = await _run_system_action(action)
    except HTTPException as exc:
        duration_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)
        _append_system_action_audit({
            "id": audit_id,
            "timestamp": started_at.isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
            "actor": actor,
            "action": action,
            "status": "failed",
            "duration_ms": duration_ms,
            "error": exc.detail,
            "steps": [],
        })
        raise

    duration_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)
    audit_entry = {
        "id": audit_id,
        "timestamp": started_at.isoformat(),
        "completed_at": datetime.utcnow().isoformat(),
        "actor": actor,
        "action": action,
        "status": "success" if result.get("success") else "failed",
        "duration_ms": duration_ms,
        "steps": [
            {
                "command": step.get("command"),
                "return_code": step.get("return_code"),
            }
            for step in result.get("steps", [])
        ],
    }
    if not result.get("success"):
        audit_entry["error"] = "System action step failed"

    _append_system_action_audit(audit_entry)

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result)
    return result


@router.get("/settings/api-keys/status")
async def get_api_keys_status(current_user: User = Depends(get_current_user)):
    """Get API key configuration status without exposing secrets."""
    return {
        "anthropic_configured": bool(os.getenv("ANTHROPIC_API_KEY")),
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "openrouter_configured": bool(os.getenv("OPENROUTER_API_KEY")),
        "ai_available": ai_service.is_available(),
        "can_persist_to_env": _is_system_actions_enabled_for_user(current_user),
        "default_model": ai_service.default_model,
        "available_models": ai_service.get_available_models(),
    }


@router.get("/settings/ai-models")
async def get_ai_models(
    include_openrouter_dynamic: bool = True,
    refresh_openrouter: bool = False,
    current_user: User = Depends(get_current_user)
):
    """List available AI models, including OpenRouter catalog when enabled."""
    del current_user  # endpoint is auth-protected and user identity is not needed yet
    return ai_service.get_model_catalog(
        include_openrouter_dynamic=include_openrouter_dynamic,
        refresh_openrouter=refresh_openrouter,
    )


@router.post("/settings/ai-model")
async def set_default_ai_model(
    payload: AiModelUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """Set runtime default AI model and optionally persist to .env."""
    if payload.persist_to_env and not _is_system_actions_enabled_for_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Persisting default AI model requires system actions permission."
        )

    try:
        selected_model = ai_service.set_default_model(payload.model)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    persisted = False
    persisted_path = None
    if payload.persist_to_env:
        env_path = _persist_env_values({"DEFAULT_AI_MODEL": selected_model})
        persisted = bool(env_path)
        persisted_path = str(env_path) if env_path else None

    return {
        "message": "Default AI model updated",
        "default_model": selected_model,
        "persisted_to_env": persisted,
        "env_path": persisted_path,
    }


@router.post("/settings/api-keys")
async def update_api_keys(
    payload: ApiKeysUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """Update API keys for the running backend process."""
    if payload.persist_to_env and not _is_system_actions_enabled_for_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="Persisting API keys requires system actions permission."
        )

    updated = []
    env_updates: Dict[str, str] = {}

    if payload.anthropic_api_key is not None:
        value = payload.anthropic_api_key.strip()
        os.environ["ANTHROPIC_API_KEY"] = value
        env_updates["ANTHROPIC_API_KEY"] = value
        updated.append("anthropic")

    if payload.openai_api_key is not None:
        value = payload.openai_api_key.strip()
        os.environ["OPENAI_API_KEY"] = value
        env_updates["OPENAI_API_KEY"] = value
        updated.append("openai")

    if payload.openrouter_api_key is not None:
        value = payload.openrouter_api_key.strip()
        os.environ["OPENROUTER_API_KEY"] = value
        env_updates["OPENROUTER_API_KEY"] = value
        updated.append("openrouter")

    if not updated:
        raise HTTPException(status_code=400, detail="No API keys provided")

    # Reinitialize AI client availability for this running process.
    ai_service._initialize_clients()

    persisted = False
    persisted_path = None
    if payload.persist_to_env:
        if env_updates:
            env_path = _persist_env_values(env_updates)
            persisted = bool(env_path)
            persisted_path = str(env_path) if env_path else None

    return {
        "message": "API keys updated for current runtime",
        "updated": updated,
        "ai_available": ai_service.is_available(),
        "persisted_to_env": persisted,
        "env_path": persisted_path
    }

# Voice capture endpoint
@router.post("/capture/voice", response_model=CaptureVoiceResponse)
async def capture_voice(
    audio_file: UploadFile = File(...),
    urgency: UrgencyLevel = Form(UrgencyLevel.normal),
    location: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_dependency)
):
    """Capture voice input and process it"""
    tmp_file_path = None
    try:
        # Validate file type
        if not audio_file.filename.lower().endswith(('.wav', '.mp3', '.ogg', '.webm')):
            raise HTTPException(status_code=400, detail="Unsupported audio format")

        # Read and validate file size
        content = await audio_file.read()
        if len(content) > MAX_AUDIO_FILE_SIZE:
            raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {MAX_AUDIO_FILE_SIZE/1024/1024}MB")

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_file_path = tmp_file.name
            tmp_file.write(content)
            tmp_file.flush()

        # Process audio
        audio_result = await audio_processor.process_audio_file(tmp_file_path)

        # Send to listener agent using proper AgentMessage
        message = AgentMessage(
            id=f'voice_{datetime.utcnow().timestamp()}',
            sender='api',
            recipient='listener',
            action='process',
            data={
                'type': 'voice',
                'audio_file': tmp_file_path,
                'urgency': urgency.value,
                'location_data': {'location': location} if location else {},
                'device_info': {'source': 'api_upload'},
                'user_id': current_user.id
            },
            timestamp=datetime.utcnow()
        )
        result = await listener_agent.handle_message(message)

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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice capture failed: {e}")
        debug = os.getenv("DEBUG", "false").lower() == "true"
        raise HTTPException(
            status_code=500,
            detail=str(e) if debug else "Internal server error"
        )
    finally:
        # Clean up temp file
        if tmp_file_path and os.path.exists(tmp_file_path):
            try:
                os.unlink(tmp_file_path)
            except Exception as e:
                logger.error(f"Failed to clean up temp file {tmp_file_path}: {e}")

# Text capture endpoint
@router.post("/capture/text", response_model=CaptureTextResponse)
async def capture_text(
    request: CaptureTextRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_dependency)
):
    """Capture text input and process it"""
    try:
        # Validate text length
        if len(request.content) > MAX_TEXT_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Text too long. Maximum length is {MAX_TEXT_LENGTH} characters"
            )

        # Send to listener agent using proper AgentMessage
        message = AgentMessage(
            id=f'text_{datetime.utcnow().timestamp()}',
            sender='api',
            recipient='listener',
            action='process',
            data={
                'type': 'text',
                'content': request.content,
                'urgency': request.urgency,
                'location_data': {'location': request.location} if request.location else {},
                'device_info': {'source': 'api_text'},
                'user_id': current_user.id
            },
            timestamp=datetime.utcnow()
        )
        result = await listener_agent.handle_message(message)

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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text capture failed: {e}")
        debug = os.getenv("DEBUG", "false").lower() == "true"
        raise HTTPException(
            status_code=500,
            detail=str(e) if debug else "Internal server error"
        )

# Dream capture endpoint
@router.post("/capture/dream")
async def capture_dream(
    content: str = Form(...),
    dream_type: str = Form("regular"),
    sleep_stage: str = Form("unknown"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_dependency)
):
    """Capture dream log entry"""
    try:
        # Validate content length
        if len(content) > MAX_TEXT_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Dream text too long. Maximum length is {MAX_TEXT_LENGTH} characters"
            )

        # Send to listener agent using proper AgentMessage
        message = AgentMessage(
            id=f'dream_{datetime.utcnow().timestamp()}',
            sender='api',
            recipient='listener',
            action='process',
            data={
                'type': 'dream',
                'content': content,
                'dream_type': dream_type,
                'sleep_stage': sleep_stage,
                'user_id': current_user.id
            },
            timestamp=datetime.utcnow()
        )
        result = await listener_agent.handle_message(message)

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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dream capture failed: {e}")
        debug = os.getenv("DEBUG", "false").lower() == "true"
        raise HTTPException(
            status_code=500,
            detail=str(e) if debug else "Internal server error"
        )

# Get ideas endpoint
@router.post("/ideas", response_model=IdeaResponse)
async def create_idea(
    request: IdeaCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_dependency)
):
    """Create an idea directly (frontend contract endpoint)."""
    try:
        content = request.content.strip()
        if not content:
            raise HTTPException(status_code=400, detail="content is required")
        if len(content) > MAX_TEXT_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Text too long. Maximum length is {MAX_TEXT_LENGTH} characters"
            )

        idea = IdeaCRUD.create_idea(
            db=db,
            content=content,
            source_type=request.source_type,
            user_id=current_user.id,
            content_transcribed=content,
            category=request.category,
            urgency_score=request.urgency_score if request.urgency_score is not None else 50.0,
            processing_status="pending",
        )

        await ws_manager.broadcast({
            'type': 'idea_captured',
            'idea_id': idea.id,
            'source': request.source_type,
            'content': content
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
            tags=[],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create idea: {e}")
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
    db: Session = Depends(get_db_dependency)
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
async def get_idea(idea_id: str, db: Session = Depends(get_db_dependency)):
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
    db: Session = Depends(get_db_dependency)
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
async def delete_idea(idea_id: str, db: Session = Depends(get_db_dependency)):
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
    db: Session = Depends(get_db_dependency)
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
    db: Session = Depends(get_db_dependency)
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
async def get_idea_visuals(idea_id: str, db: Session = Depends(get_db_dependency)):
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
async def get_idea_expansions(idea_id: str, db: Session = Depends(get_db_dependency)):
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

# Semantic search endpoints
@router.get("/search/semantic")
async def semantic_search(
    query: str,
    limit: int = 10,
    threshold: float = 0.5,
    current_user: User = Depends(get_current_user)
):
    """Search for ideas using semantic similarity"""
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Use semantic agent to search
        result = await semantic_agent.search_similar_ideas(
            query=query,
            user_id=current_user.id,
            limit=limit,
            threshold=threshold
        )
        
        if result.get('success'):
            return {
                'success': True,
                'query': query,
                'results': result['results'],
                'total_results': result['total_results'],
                'search_type': 'semantic'
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Search failed'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ideas/{idea_id}/related")
async def get_related_ideas(
    idea_id: str,
    limit: int = 5,
    threshold: float = 0.6,
    current_user: User = Depends(get_current_user)
):
    """Get ideas related to a specific idea"""
    try:
        # Use semantic agent to find related ideas
        result = await semantic_agent.find_related_ideas(
            idea_id=idea_id,
            limit=limit,
            threshold=threshold
        )
        
        if result.get('success'):
            return {
                'success': True,
                'idea_id': idea_id,
                'related_ideas': result['related_ideas'],
                'total_found': result['total_found']
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to find related ideas'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get related ideas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ideas/{idea_id}/generate_embedding")
async def generate_idea_embedding(
    idea_id: str,
    current_user: User = Depends(get_current_user)
):
    """Generate or update embedding for a specific idea"""
    try:
        # Use semantic agent to process the idea
        result = await semantic_agent.process_idea(idea_id)
        
        if result.get('success'):
            return {
                'success': True,
                'idea_id': idea_id,
                'embedding_generated': result['embedding_generated'],
                'related_ideas': result.get('related_ideas', []),
                'message': result.get('message', 'Embedding generated successfully')
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to generate embedding'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate embedding for idea {idea_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/embeddings/batch_update")
async def batch_update_embeddings(
    batch_size: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Update embeddings for ideas that don't have them"""
    try:
        # Use semantic agent to batch update embeddings
        result = await semantic_agent.batch_update_embeddings(batch_size)
        
        if result.get('success'):
            return {
                'success': True,
                'updated_count': result['updated_count'],
                'message': result.get('message', 'Batch update completed')
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Batch update failed'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to batch update embeddings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/embeddings/stats")
async def get_embedding_stats(
    current_user: User = Depends(get_current_user)
):
    """Get statistics about embeddings in the system"""
    try:
        # Use semantic agent to get stats
        result = await semantic_agent.get_embedding_stats()
        
        if result.get('success'):
            return {
                'success': True,
                'stats': result['stats']
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to get stats'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get embedding stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs/search/semantic")
async def semantic_log_search(
    query: str,
    limit: int = 20,
    threshold: float = 0.4,
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Search agent logs by semantic similarity."""
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        if limit < 1 or limit > 100:
            raise HTTPException(status_code=400, detail="limit must be between 1 and 100")

        if threshold < 0 or threshold > 1:
            raise HTTPException(status_code=400, detail="threshold must be between 0 and 1")

        results = await embedding_service.search_similar_logs(
            query=query,
            limit=limit,
            threshold=threshold,
            agent_id=agent_id,
            status=status
        )

        return {
            "success": True,
            "query": query,
            "results": results,
            "total_results": len(results),
            "search_type": "semantic_logs"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Semantic log search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/logs/embeddings/batch_update")
async def batch_update_log_embeddings(
    batch_size: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Update embeddings for logs that do not have one."""
    try:
        if batch_size < 1 or batch_size > 1000:
            raise HTTPException(status_code=400, detail="batch_size must be between 1 and 1000")

        updated_count = await embedding_service.batch_update_log_embeddings(batch_size)
        return {
            "success": True,
            "updated_count": updated_count,
            "message": f"Updated {updated_count} log embeddings"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to batch update log embeddings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs/embeddings/stats")
async def get_log_embedding_stats(
    current_user: User = Depends(get_current_user)
):
    """Get embedding coverage statistics for agent logs."""
    try:
        stats = await embedding_service.get_log_embedding_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Failed to get log embedding stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Get proposals endpoint
@router.get("/proposals", response_model=List[ProposalResponse])
async def get_proposals(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db_dependency)
):
    """Get proposals with filtering"""
    try:
        if status == "pending":
            proposals = ProposalCRUD.get_pending_proposals(db)
        else:
            proposals = ProposalCRUD.get_proposals(db, skip=skip, limit=limit)
        
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
    db: Session = Depends(get_db_dependency)
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
async def get_agent_status(db: Session = Depends(get_db_dependency)):
    """Get status of all agents"""
    try:
        agents = agent_registry.get_all_agents()
        failed_logs = AgentLogCRUD.get_error_logs(db, hours=168)
        last_error_by_agent: Dict[str, Dict[str, Any]] = {}
        for log in failed_logs:
            if log.agent_id not in last_error_by_agent:
                last_error_by_agent[log.agent_id] = {
                    "error_message": log.error_message,
                    "started_at": log.started_at
                }
        
        return [
            AgentStatusResponse(
                agent_id=agent.agent_id,
                name=agent.name,
                is_active=agent.is_active,
                total_processed=agent.total_processed,
                success_rate=agent.success_count / agent.total_processed if agent.total_processed > 0 else 0,
                version=agent.version,
                queue_depth=agent.message_queue.qsize() if hasattr(agent, "message_queue") else 0,
                last_error=last_error_by_agent.get(agent.agent_id, {}).get("error_message"),
                last_error_at=last_error_by_agent.get(agent.agent_id, {}).get("started_at")
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
    db: Session = Depends(get_db_dependency)
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
    db: Session = Depends(get_db_dependency)
):
    """Get logs for a specific agent"""
    try:
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

@router.get("/logs")
async def get_recent_logs(
    hours: int = 24,
    status: Optional[str] = None,
    agent_id: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_dependency)
):
    """Get recent logs across agents with optional filtering."""
    try:
        if limit < 1 or limit > 500:
            raise HTTPException(status_code=400, detail="limit must be between 1 and 500")

        logs = AgentLogCRUD.get_agent_logs(db, agent_id, status, hours)
        logs = logs[:limit]

        return {
            "success": True,
            "count": len(logs),
            "logs": [
                {
                    "id": log.id,
                    "agent_id": log.agent_id,
                    "idea_id": log.idea_id,
                    "action": log.action,
                    "status": log.status,
                    "started_at": log.started_at.isoformat() if log.started_at else None,
                    "completed_at": log.completed_at.isoformat() if log.completed_at else None,
                    "processing_time": log.processing_time,
                    "input_data": log.input_data,
                    "output_data": log.output_data,
                    "error_message": log.error_message
                }
                for log in logs
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get recent logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Get system metrics endpoint
@router.get("/metrics")
async def get_system_metrics(
    metric_name: Optional[str] = None,
    hours: int = 24,
    db: Session = Depends(get_db_dependency)
):
    """Get system metrics"""
    try:
        metrics = SystemMetricsCRUD.get_metrics(db, metric_name, hours)
        
        return {
            'metrics': [
                {
                    'metric_name': metric.metric_name,
                    'metric_value': metric.metric_value,
                    'metric_type': metric.metric_type,
                    'timestamp': metric.timestamp.isoformat(),
                    'metadata': metric.labels or {}
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
async def get_error_summary(hours: int = 24, db: Session = Depends(get_db_dependency)):
    """Get error summary"""
    try:
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
async def get_system_stats(db: Session = Depends(get_db_dependency)):
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
