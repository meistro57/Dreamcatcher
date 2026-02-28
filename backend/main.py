import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

try:  # pragma: no cover - exercised implicitly during imports
    from .database import create_tables, db_manager
    from .database.init_auth import init_auth_system
    from .api import router, websocket_manager
    from .api.auth_routes import router as auth_router
    from .agents import agent_registry
    from .tasks.embedding_tasks import start_embedding_tasks, stop_embedding_tasks
except ImportError:  # pragma: no cover - fallback for script-style execution
    from database import create_tables, db_manager
    from database.init_auth import init_auth_system
    from api import router, websocket_manager
    from api.auth_routes import router as auth_router
    from agents import agent_registry
    from tasks.embedding_tasks import start_embedding_tasks, stop_embedding_tasks


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dreamcatcher")


def _parse_cors_origins() -> List[str]:
    """Load and validate allowed CORS origins from env."""
    raw_origins = os.getenv("CORS_ORIGINS")
    if not raw_origins:
        raise RuntimeError("CORS_ORIGINS must be set for credentialed CORS requests")

    try:
        origins = json.loads(raw_origins)
    except json.JSONDecodeError as exc:
        raise RuntimeError("CORS_ORIGINS must be valid JSON array") from exc

    if not isinstance(origins, list) or not origins:
        raise RuntimeError("CORS_ORIGINS must be a non-empty JSON array")

    invalid = [origin for origin in origins if not isinstance(origin, str) or not origin.strip()]
    if invalid:
        raise RuntimeError("CORS_ORIGINS must only contain non-empty strings")

    return origins


ALLOWED_CORS_ORIGINS = _parse_cors_origins()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Dreamcatcher backend...")

    # Initialize database
    try:
        create_tables()
        logger.info("Database tables created/verified")

        # Initialize authentication system
        init_auth_system()
        logger.info("Authentication system initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

    # Start agent system
    try:
        # Start all active agents
        agent_tasks = []
        for agent in agent_registry.get_active_agents():
            task = asyncio.create_task(agent.start())
            agent_tasks.append(task)
            logger.info(f"Started agent: {agent.agent_id}")

        # Store tasks in app state
        app.state.agent_tasks = agent_tasks

        logger.info(f"Started {len(agent_tasks)} agents")

    except Exception as e:
        logger.error(f"Agent system startup failed: {e}")
        raise

    # Start WebSocket manager maintenance
    try:
        ping_task = asyncio.create_task(websocket_ping_loop())
        cleanup_task = asyncio.create_task(websocket_cleanup_loop())

        app.state.websocket_tasks = [ping_task, cleanup_task]

        logger.info("WebSocket manager started")

    except Exception as e:
        logger.error(f"WebSocket manager startup failed: {e}")

    # Start embedding tasks
    try:
        embedding_task = asyncio.create_task(start_embedding_tasks())
        app.state.embedding_task = embedding_task

        logger.info("Embedding task manager started")

    except Exception as e:
        logger.error(f"Embedding task manager startup failed: {e}")

    logger.info("Dreamcatcher backend started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Dreamcatcher backend...")

    # Stop agent tasks
    if hasattr(app.state, 'agent_tasks'):
        for task in app.state.agent_tasks:
            task.cancel()
        await asyncio.gather(*app.state.agent_tasks, return_exceptions=True)

    # Stop WebSocket tasks
    if hasattr(app.state, 'websocket_tasks'):
        for task in app.state.websocket_tasks:
            task.cancel()
        await asyncio.gather(*app.state.websocket_tasks, return_exceptions=True)

    # Stop embedding tasks
    if hasattr(app.state, 'embedding_task'):
        await stop_embedding_tasks()
        app.state.embedding_task.cancel()
        try:
            await app.state.embedding_task
        except asyncio.CancelledError:
            pass

    logger.info("Dreamcatcher backend stopped")


async def websocket_ping_loop():
    """Periodic ping to keep WebSocket connections alive"""
    while True:
        try:
            await websocket_manager.ping_all_connections()
            await asyncio.sleep(30)  # Ping every 30 seconds
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"WebSocket ping error: {e}")
            await asyncio.sleep(60)  # Wait longer on error


async def websocket_cleanup_loop():
    """Periodic cleanup of stale WebSocket connections"""
    while True:
        try:
            cleaned = await websocket_manager.cleanup_stale_connections()
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} stale WebSocket connections")
            await asyncio.sleep(300)  # Cleanup every 5 minutes
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"WebSocket cleanup error: {e}")
            await asyncio.sleep(600)  # Wait longer on error


# Create FastAPI app
app = FastAPI(
    title="Dreamcatcher API",
    description="AI-powered idea factory that never sleeps",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# Custom exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Global exception on {request.method} {request.url}: {exc}")

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if os.getenv("DEBUG", "false").lower() == "true" else "An unexpected error occurred"
        }
    )


# Include routers
app.include_router(router, prefix="/api")
app.include_router(auth_router, prefix="/api")

# Mount static files for uploads
if os.path.exists("storage"):
    app.mount("/storage", StaticFiles(directory="storage"), name="storage")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Dreamcatcher API",
        "version": "1.0.0",
        "status": "active",
        "docs": "/docs",
        "health": "/api/health"
    }


@app.get("/api/status")
async def api_status():
    """API status endpoint"""
    return {
        "api": "Dreamcatcher",
        "status": "operational",
        "timestamp": asyncio.get_event_loop().time(),
        "database": "connected" if db_manager.health_check() else "disconnected"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("ENVIRONMENT", "development") == "development",
        log_level="info"
    )
