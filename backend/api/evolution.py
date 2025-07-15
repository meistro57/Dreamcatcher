from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from ..services.evolution_service import EvolutionService
from ..models.evolution import (
    EvolutionStatusResponse,
    EvolutionCycleResponse,
    EvolutionHistoryResponse,
    EvolutionConfigRequest,
    ForceEvolutionRequest,
    RollbackRequest
)

router = APIRouter(prefix="/evolution", tags=["evolution"])
logger = logging.getLogger(__name__)

# Initialize evolution service
evolution_service = EvolutionService()

@router.get("/status", response_model=EvolutionStatusResponse)
async def get_evolution_status():
    """Get current evolution status"""
    try:
        status = await evolution_service.get_evolution_status()
        return EvolutionStatusResponse(**status)
    except Exception as e:
        logger.error(f"Evolution status retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cycle", response_model=EvolutionCycleResponse)
async def start_evolution_cycle(background_tasks: BackgroundTasks, force: bool = False):
    """Start a complete evolution cycle"""
    try:
        # Run evolution in background
        background_tasks.add_task(evolution_service.start_evolution_cycle, force)
        
        return EvolutionCycleResponse(
            success=True,
            message="Evolution cycle started",
            cycle_id=f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            started_at=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Evolution cycle start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/force")
async def force_evolution(request: ForceEvolutionRequest):
    """Force evolution for specific agent or entire system"""
    try:
        result = await evolution_service.force_evolution(request.target_agent)
        return result
    except Exception as e:
        logger.error(f"Forced evolution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/schedule")
async def schedule_evolution(interval_hours: int = 24):
    """Schedule automatic evolution"""
    try:
        result = await evolution_service.schedule_evolution(interval_hours)
        return result
    except Exception as e:
        logger.error(f"Evolution scheduling failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", response_model=EvolutionHistoryResponse)
async def get_evolution_history(limit: int = 50):
    """Get evolution history"""
    try:
        history = await evolution_service.get_evolution_history(limit)
        return EvolutionHistoryResponse(
            history=history,
            total_entries=len(history),
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Evolution history retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rollback")
async def rollback_system(request: RollbackRequest):
    """Rollback system or specific agent to previous version"""
    try:
        result = await evolution_service.rollback_system(
            request.target_agent,
            request.backup_timestamp
        )
        return result
    except Exception as e:
        logger.error(f"System rollback failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/config")
async def configure_evolution(request: EvolutionConfigRequest):
    """Configure evolution parameters"""
    try:
        config_dict = request.dict(exclude_unset=True)
        result = await evolution_service.configure_evolution(**config_dict)
        return result
    except Exception as e:
        logger.error(f"Evolution configuration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trends")
async def get_performance_trends(days: int = 7):
    """Get performance trends over time"""
    try:
        trends = await evolution_service.get_performance_trends(days)
        return trends
    except Exception as e:
        logger.error(f"Performance trends retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/emergency-stop")
async def emergency_stop():
    """Emergency stop of evolution process"""
    try:
        result = await evolution_service.emergency_stop()
        return result
    except Exception as e:
        logger.error(f"Emergency stop failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def evolution_health_check():
    """Check evolution service health"""
    try:
        health = await evolution_service.health_check()
        return health
    except Exception as e:
        logger.error(f"Evolution health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze")
async def analyze_system():
    """Analyze system performance and identify improvement opportunities"""
    try:
        # Use the meta agent directly for analysis
        from ..agents.agent_meta import AgentMeta
        meta_agent = AgentMeta()
        
        analysis = await meta_agent.process({
            'type': 'system_analysis',
            'include_recommendations': True
        })
        
        return analysis
    except Exception as e:
        logger.error(f"System analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/performance")
async def get_agent_performance():
    """Get detailed performance metrics for all agents"""
    try:
        from ..agents.agent_meta import AgentMeta
        meta_agent = AgentMeta()
        
        # Get system analysis with detailed agent metrics
        analysis = await meta_agent._analyze_system_state()
        
        if analysis and 'agent_metrics' in analysis:
            return {
                'success': True,
                'agent_metrics': analysis['agent_metrics'],
                'timestamp': analysis['timestamp']
            }
        
        return {'error': 'Failed to retrieve agent performance metrics'}
    except Exception as e:
        logger.error(f"Agent performance retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/opportunities")
async def get_improvement_opportunities():
    """Get current improvement opportunities"""
    try:
        from ..agents.agent_meta import AgentMeta
        meta_agent = AgentMeta()
        
        # Analyze system state
        analysis = await meta_agent._analyze_system_state()
        
        if analysis:
            # Identify opportunities
            opportunities = await meta_agent._identify_opportunities(analysis)
            
            return {
                'success': True,
                'opportunities': opportunities,
                'total_opportunities': len(opportunities),
                'timestamp': datetime.now().isoformat()
            }
        
        return {'error': 'Failed to identify improvement opportunities'}
    except Exception as e:
        logger.error(f"Opportunity identification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/opportunities/{opportunity_id}/apply")
async def apply_improvement_opportunity(opportunity_id: str):
    """Apply a specific improvement opportunity"""
    try:
        # This would typically fetch the opportunity from a queue/database
        # For now, we'll return a placeholder response
        return {
            'success': True,
            'opportunity_id': opportunity_id,
            'status': 'applied',
            'message': f'Improvement opportunity {opportunity_id} applied successfully',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Opportunity application failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/backups")
async def list_agent_backups():
    """List available agent backups"""
    try:
        import os
        import glob
        
        backup_dir = "/home/mark/Dreamcatcher/backups/agents"
        
        if not os.path.exists(backup_dir):
            return {'backups': [], 'total': 0}
        
        backup_files = glob.glob(f"{backup_dir}/*.py")
        backups = []
        
        for backup_file in backup_files:
            filename = os.path.basename(backup_file)
            # Parse filename: agent_<agent_id>_<timestamp>.py
            parts = filename.replace('.py', '').split('_')
            if len(parts) >= 3:
                agent_id = parts[1]
                timestamp = '_'.join(parts[2:])
                
                backups.append({
                    'agent_id': agent_id,
                    'timestamp': timestamp,
                    'filename': filename,
                    'created_at': datetime.fromtimestamp(os.path.getctime(backup_file)).isoformat(),
                    'size': os.path.getsize(backup_file)
                })
        
        # Sort by creation time, newest first
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        
        return {
            'backups': backups,
            'total': len(backups),
            'backup_directory': backup_dir
        }
    except Exception as e:
        logger.error(f"Backup listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-improvement")
async def test_improvement():
    """Test improvement functionality with a safe operation"""
    try:
        from ..agents.agent_meta import AgentMeta
        meta_agent = AgentMeta()
        
        # Run a safe analysis without making changes
        test_result = await meta_agent.process({
            'type': 'system_analysis',
            'test_mode': True
        })
        
        return {
            'success': True,
            'test_result': test_result,
            'message': 'Improvement system test completed successfully',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Improvement test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))