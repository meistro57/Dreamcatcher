from .routes import router
from .models import *  # noqa: F401,F403 - re-export for convenience
from .websocket_manager import websocket_manager

try:  # pragma: no cover - optional features
    from .evolution import router as evolution_router
    router.include_router(evolution_router)
except ImportError:
    evolution_router = None

try:  # pragma: no cover - optional features
    from .scheduler import router as scheduler_router
    router.include_router(scheduler_router)
except ImportError:
    scheduler_router = None

__all__ = ['router', 'websocket_manager']