from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional
import logging

from ..scheduler.evolution_scheduler import scheduler
from ..models.evolution import (
    EvolutionStatusResponse,
    EvolutionConfigRequest,
    EvolutionTrendsResponse
)

router = APIRouter(prefix="/scheduler", tags=["scheduler"])
logger = logging.getLogger(__name__)

@router.get("/status")
async def get_scheduler_status():
    """Get current scheduler status"""
    try:
        status = await scheduler.get_scheduler_status()
        return status
    except Exception as e:
        logger.error(f"Scheduler status retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start")
async def start_scheduler():
    """Start the evolution scheduler"""
    try:
        await scheduler.start()
        return {
            'success': True,
            'message': 'Evolution scheduler started successfully',
            'running': scheduler.running
        }
    except Exception as e:
        logger.error(f"Scheduler start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop")
async def stop_scheduler():
    """Stop the evolution scheduler"""
    try:
        await scheduler.stop()
        return {
            'success': True,
            'message': 'Evolution scheduler stopped successfully',
            'running': scheduler.running
        }
    except Exception as e:
        logger.error(f"Scheduler stop failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/config")
async def update_scheduler_config(config: EvolutionConfigRequest):
    """Update scheduler configuration"""
    try:
        config_dict = config.dict(exclude_unset=True)
        result = await scheduler.update_config(**config_dict)
        return result
    except Exception as e:
        logger.error(f"Scheduler configuration update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/force-evolution")
async def force_evolution(evolution_type: str = "manual"):
    """Force an evolution cycle immediately"""
    try:
        result = await scheduler.force_evolution(evolution_type)
        return result
    except Exception as e:
        logger.error(f"Forced evolution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trends")
async def get_performance_trends(days: int = 7):
    """Get performance trends over specified days"""
    try:
        trends = await scheduler.get_performance_trends(days)
        return trends
    except Exception as e:
        logger.error(f"Performance trends retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def scheduler_health_check():
    """Check scheduler health"""
    try:
        health_info = {
            'scheduler_running': scheduler.running,
            'current_evolutions': scheduler.current_evolutions,
            'last_evolution': scheduler.last_evolution.isoformat() if scheduler.last_evolution else None,
            'last_health_check': scheduler.last_health_check.isoformat() if scheduler.last_health_check else None,
            'evolution_stats': scheduler.evolution_stats.copy(),
            'config_valid': len(scheduler.config) > 0
        }
        return health_info
    except Exception as e:
        logger.error(f"Scheduler health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_scheduler_stats():
    """Get scheduler statistics"""
    try:
        stats = {
            'evolution_stats': scheduler.evolution_stats.copy(),
            'config': scheduler.config.copy(),
            'running': scheduler.running,
            'current_evolutions': scheduler.current_evolutions,
            'performance_history_size': len(scheduler.performance_history)
        }
        return stats
    except Exception as e:
        logger.error(f"Scheduler stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset-stats")
async def reset_scheduler_stats():
    """Reset scheduler statistics"""
    try:
        scheduler.evolution_stats = {
            'total_cycles': 0,
            'successful_cycles': 0,
            'failed_cycles': 0,
            'emergency_evolutions': 0,
            'improvements_applied': 0
        }
        scheduler.performance_history = []
        
        return {
            'success': True,
            'message': 'Scheduler statistics reset successfully',
            'reset_timestamp': scheduler.last_evolution.isoformat() if scheduler.last_evolution else None
        }
    except Exception as e:
        logger.error(f"Scheduler stats reset failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/emergency-stop")
async def emergency_stop_scheduler():
    """Emergency stop of all scheduler operations"""
    try:
        await scheduler.stop()
        
        # Reset evolution counter
        scheduler.current_evolutions = 0
        
        return {
            'success': True,
            'message': 'Emergency stop executed successfully',
            'running': scheduler.running,
            'current_evolutions': scheduler.current_evolutions
        }
    except Exception as e:
        logger.error(f"Emergency stop failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/next-evolution")
async def get_next_evolution():
    """Get next scheduled evolution time"""
    try:
        next_evolution = scheduler._get_next_scheduled_evolution()
        next_health_check = scheduler._get_next_health_check()
        
        return {
            'next_evolution': next_evolution,
            'next_health_check': next_health_check,
            'auto_evolution_enabled': scheduler.config['auto_evolution_enabled'],
            'evolution_interval_hours': scheduler.config['evolution_interval_hours'],
            'health_check_interval_minutes': scheduler.config['health_check_interval_minutes']
        }
    except Exception as e:
        logger.error(f"Next evolution retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-health-check")
async def test_health_check():
    """Test health check functionality"""
    try:
        # Force a health check
        await scheduler._perform_health_check()
        
        return {
            'success': True,
            'message': 'Health check completed successfully',
            'last_health_check': scheduler.last_health_check.isoformat() if scheduler.last_health_check else None
        }
    except Exception as e:
        logger.error(f"Health check test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs")
async def get_scheduler_logs(limit: int = 100):
    """Get recent scheduler logs"""
    try:
        # This would typically read from log files
        # For now, return basic log information
        logs = [
            {
                'timestamp': scheduler.last_evolution.isoformat() if scheduler.last_evolution else None,
                'level': 'INFO',
                'message': 'Last evolution completed',
                'data': scheduler.evolution_stats
            },
            {
                'timestamp': scheduler.last_health_check.isoformat() if scheduler.last_health_check else None,
                'level': 'INFO',
                'message': 'Last health check completed',
                'data': {'running': scheduler.running}
            }
        ]
        
        return {
            'logs': [log for log in logs if log['timestamp'] is not None],
            'total_logs': len([log for log in logs if log['timestamp'] is not None]),
            'limit': limit
        }
    except Exception as e:
        logger.error(f"Scheduler logs retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))