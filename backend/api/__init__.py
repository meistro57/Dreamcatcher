from .routes import router
from .models import *
from .websocket_manager import websocket_manager
from .evolution import router as evolution_router
from .scheduler import router as scheduler_router

# Include sub-routers in main router
router.include_router(evolution_router)
router.include_router(scheduler_router)

__all__ = ['router', 'websocket_manager']