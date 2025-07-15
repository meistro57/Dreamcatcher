import asyncio
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from .database import create_tables, db_manager
from .api import router, websocket_manager
from .agents import agent_registry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dreamcatcher")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Dreamcatcher backend...")
    
    # Initialize database
    try:
        create_tables()
        logger.info("Database tables created/verified")
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
    allow_origins=["*"],  # In production, specify allowed origins
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
            "detail": str(exc) if os.getenv("DEBUG") else "Something went wrong",
            "timestamp": asyncio.get_event_loop().time()
        }
    )

# Include API routes
app.include_router(router, prefix="/api")

# Static files for generated images, etc.
if os.path.exists("storage"):
    app.mount("/storage", StaticFiles(directory="storage"), name="storage")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Dreamcatcher API",
        "tagline": "The basement never sleeps. Neither does this code.",
        "version": "1.0.0",
        "status": "running",
        "agents": len(agent_registry.get_active_agents()),
        "websocket_connections": websocket_manager.get_connection_count()
    }

# Version endpoint
@app.get("/version")
async def version():
    """Version information"""
    return {
        "version": "1.0.0",
        "api_version": "1.0",
        "description": "AI-powered idea factory",
        "build_timestamp": "2025-07-15T00:00:00Z"
    }

# Development server
if __name__ == "__main__":
    # Load environment variables
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    logger.info(f"Starting development server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )