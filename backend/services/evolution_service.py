import asyncio
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

try:  # pragma: no cover
    from ..database import get_db, SystemMetricsCRUD
    from ..agents.agent_meta import AgentMeta
except ImportError:  # pragma: no cover
    from database import get_db, SystemMetricsCRUD
    from agents.agent_meta import AgentMeta

class EvolutionService:
    """
    Service for managing system evolution and self-improvement.
    Coordinates with AgentMeta for continuous system enhancement.
    """
    
    def __init__(self):
        self.meta_agent = AgentMeta()
        self.logger = logging.getLogger(__name__)
        
        # Evolution configuration
        self.config = {
            'auto_evolution_enabled': True,
            'evolution_interval_hours': 24,
            'performance_threshold': 0.80,
            'error_threshold': 0.10,
            'min_data_points': 50
        }
        
        # Evolution states
        self.evolution_states = {
            'idle': 'System monitoring, no evolution needed',
            'analyzing': 'Analyzing system performance',
            'evolving': 'Applying improvements',
            'validating': 'Validating changes',
            'complete': 'Evolution cycle complete'
        }
        
        self.current_state = 'idle'
        self.last_evolution = None
        self.evolution_queue = []
    
    async def start_evolution_cycle(self, force: bool = False) -> Dict[str, Any]:
        """Start a complete evolution cycle"""
        try:
            if self.current_state != 'idle' and not force:
                return {
                    'error': f'Evolution already in progress: {self.current_state}',
                    'current_state': self.current_state
                }
            
            self.current_state = 'analyzing'
            self.logger.info("Starting evolution cycle")
            
            # Step 1: System analysis
            analysis_result = await self._analyze_system()
            if not analysis_result['success']:
                self.current_state = 'idle'
                return analysis_result
            
            # Step 2: Identify improvements
            self.current_state = 'evolving'
            improvement_result = await self._apply_improvements(analysis_result['data'])
            
            # Step 3: Validate changes
            self.current_state = 'validating'
            validation_result = await self._validate_improvements(improvement_result)
            
            # Step 4: Complete cycle
            self.current_state = 'complete'
            self.last_evolution = datetime.now()
            
            # Log evolution metrics
            await self._log_evolution_metrics(improvement_result)
            
            # Return to idle
            self.current_state = 'idle'
            
            return {
                'success': True,
                'evolution_complete': True,
                'improvements_applied': improvement_result.get('improvements_made', 0),
                'analysis': analysis_result['data'],
                'validation': validation_result,
                'timestamp': self.last_evolution.isoformat()
            }
            
        except Exception as e:
            self.current_state = 'idle'
            self.logger.error(f"Evolution cycle failed: {e}")
            return {'error': f'Evolution cycle failed: {str(e)}'}
    
    async def _analyze_system(self) -> Dict[str, Any]:
        """Analyze system performance and identify improvement opportunities"""
        try:
            # Use AgentMeta to analyze system state
            analysis = await self.meta_agent.process({
                'type': 'system_analysis',
                'include_recommendations': True
            })
            
            if not analysis.get('success'):
                return {'success': False, 'error': 'System analysis failed'}
            
            # Determine if evolution is needed
            should_evolve = await self._should_evolve(analysis)
            
            return {
                'success': True,
                'data': analysis,
                'evolution_needed': should_evolve,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"System analysis failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _should_evolve(self, analysis: Dict[str, Any]) -> bool:
        """Determine if system evolution is needed"""
        try:
            # Check performance metrics
            if 'analysis' in analysis and 'health_score' in analysis['analysis']:
                health_score = analysis['analysis']['health_score']
                if health_score < self.config['performance_threshold'] * 100:
                    return True
            
            # Check error rates
            if 'analysis' in analysis and 'agent_metrics' in analysis['analysis']:
                agent_metrics = analysis['analysis']['agent_metrics']
                for agent_id, metrics in agent_metrics.items():
                    error_rate = metrics.get('error_rate', 0)
                    if error_rate > self.config['error_threshold']:
                        return True
            
            # Check if minimum time has passed
            if self.last_evolution:
                time_since_last = datetime.now() - self.last_evolution
                if time_since_last.total_seconds() < self.config['evolution_interval_hours'] * 3600:
                    return False
            
            return False
            
        except Exception as e:
            self.logger.error(f"Evolution decision failed: {e}")
            return False
    
    async def _apply_improvements(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Apply system improvements based on analysis"""
        try:
            # Process improvements through AgentMeta
            improvement_result = await self.meta_agent.process({
                'type': 'performance_optimization',
                'analysis': analysis,
                'auto_apply': True
            })
            
            return improvement_result
            
        except Exception as e:
            self.logger.error(f"Improvement application failed: {e}")
            return {'error': str(e), 'improvements_made': 0}
    
    async def _validate_improvements(self, improvement_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that improvements are working correctly"""
        try:
            if not improvement_result.get('success'):
                return {'valid': False, 'reason': 'Improvements failed to apply'}
            
            # Wait for system to stabilize
            await asyncio.sleep(10)
            
            # Run quick system check
            quick_analysis = await self.meta_agent.process({
                'type': 'system_analysis',
                'quick_check': True
            })
            
            if quick_analysis.get('success'):
                health_score = quick_analysis.get('analysis', {}).get('health_score', 0)
                return {
                    'valid': True,
                    'health_score': health_score,
                    'validation_timestamp': datetime.now().isoformat()
                }
            
            return {'valid': False, 'reason': 'Post-improvement validation failed'}
            
        except Exception as e:
            self.logger.error(f"Improvement validation failed: {e}")
            return {'valid': False, 'reason': str(e)}
    
    async def _log_evolution_metrics(self, improvement_result: Dict[str, Any]):
        """Log evolution metrics to database"""
        try:
            with get_db() as db:
                # Log evolution event
                SystemMetricsCRUD.create_metric(
                    db=db,
                    metric_name="evolution_cycle_completed",
                    metric_value=1,
                    metric_type="counter",
                    labels=json.dumps({
                        "improvements_made": improvement_result.get('improvements_made', 0),
                        "timestamp": datetime.now().isoformat()
                    })
                )
                
                # Log improvement count
                SystemMetricsCRUD.create_metric(
                    db=db,
                    metric_name="improvements_applied",
                    metric_value=improvement_result.get('improvements_made', 0),
                    metric_type="gauge",
                    labels=json.dumps({
                        "cycle_timestamp": datetime.now().isoformat()
                    })
                )
                
        except Exception as e:
            self.logger.error(f"Evolution metrics logging failed: {e}")
    
    async def schedule_evolution(self, interval_hours: int = None) -> Dict[str, Any]:
        """Schedule automatic evolution"""
        try:
            if interval_hours:
                self.config['evolution_interval_hours'] = interval_hours
            
            # In a real implementation, this would integrate with a task scheduler
            # For now, we'll simulate scheduling
            
            next_evolution = datetime.now() + timedelta(hours=self.config['evolution_interval_hours'])
            
            self.logger.info(f"Evolution scheduled for {next_evolution}")
            
            return {
                'success': True,
                'scheduled': True,
                'interval_hours': self.config['evolution_interval_hours'],
                'next_evolution': next_evolution.isoformat(),
                'auto_evolution_enabled': self.config['auto_evolution_enabled']
            }
            
        except Exception as e:
            self.logger.error(f"Evolution scheduling failed: {e}")
            return {'error': f'Scheduling failed: {str(e)}'}
    
    async def get_evolution_status(self) -> Dict[str, Any]:
        """Get current evolution status"""
        try:
            return {
                'current_state': self.current_state,
                'state_description': self.evolution_states.get(self.current_state, 'Unknown state'),
                'last_evolution': self.last_evolution.isoformat() if self.last_evolution else None,
                'auto_evolution_enabled': self.config['auto_evolution_enabled'],
                'evolution_interval_hours': self.config['evolution_interval_hours'],
                'queue_size': len(self.evolution_queue),
                'next_scheduled': self._get_next_scheduled_evolution()
            }
            
        except Exception as e:
            self.logger.error(f"Status retrieval failed: {e}")
            return {'error': str(e)}
    
    def _get_next_scheduled_evolution(self) -> Optional[str]:
        """Get next scheduled evolution time"""
        if not self.last_evolution:
            return None
        
        next_evolution = self.last_evolution + timedelta(hours=self.config['evolution_interval_hours'])
        return next_evolution.isoformat()
    
    async def force_evolution(self, target_agent: str = None) -> Dict[str, Any]:
        """Force evolution for specific agent or entire system"""
        try:
            self.logger.info(f"Forcing evolution for {target_agent or 'entire system'}")
            
            # Run targeted evolution
            evolution_result = await self.meta_agent.process({
                'type': 'performance_optimization',
                'agent_id': target_agent,
                'force': True
            })
            
            return evolution_result
            
        except Exception as e:
            self.logger.error(f"Forced evolution failed: {e}")
            return {'error': str(e)}
    
    async def get_evolution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get evolution history"""
        try:
            history = await self.meta_agent.get_evolution_history()
            return history[-limit:] if history else []
            
        except Exception as e:
            self.logger.error(f"Evolution history retrieval failed: {e}")
            return []
    
    async def rollback_system(self, target_agent: str = None, backup_timestamp: str = None) -> Dict[str, Any]:
        """Rollback system or specific agent to previous version"""
        try:
            if target_agent:
                # Rollback specific agent
                return await self.meta_agent.rollback_agent(target_agent, backup_timestamp)
            else:
                # Rollback entire system (simplified implementation)
                return {
                    'error': 'System-wide rollback not implemented yet',
                    'suggestion': 'Use agent-specific rollback instead'
                }
                
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            return {'error': str(e)}
    
    async def configure_evolution(self, **kwargs) -> Dict[str, Any]:
        """Configure evolution parameters"""
        try:
            updated_config = {}
            
            for key, value in kwargs.items():
                if key in self.config:
                    self.config[key] = value
                    updated_config[key] = value
            
            return {
                'success': True,
                'updated_config': updated_config,
                'current_config': self.config.copy()
            }
            
        except Exception as e:
            self.logger.error(f"Configuration update failed: {e}")
            return {'error': str(e)}
    
    async def get_performance_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get performance trends over time"""
        try:
            with get_db() as db:
                # Get recent metrics
                cutoff_time = datetime.now() - timedelta(days=days)
                metrics = SystemMetricsCRUD.get_metrics_since(db, cutoff_time)
                
                trends = {
                    'evolution_cycles': 0,
                    'improvements_applied': 0,
                    'performance_trend': 'stable',
                    'metrics_by_day': {}
                }
                
                for metric in metrics:
                    day = metric.timestamp.date().isoformat()
                    
                    if day not in trends['metrics_by_day']:
                        trends['metrics_by_day'][day] = {
                            'evolution_cycles': 0,
                            'improvements': 0,
                            'errors': 0
                        }
                    
                    if metric.metric_name == 'evolution_cycle_completed':
                        trends['evolution_cycles'] += metric.metric_value
                        trends['metrics_by_day'][day]['evolution_cycles'] += metric.metric_value
                    elif metric.metric_name == 'improvements_applied':
                        trends['improvements_applied'] += metric.metric_value
                        trends['metrics_by_day'][day]['improvements'] += metric.metric_value
                
                return trends
                
        except Exception as e:
            self.logger.error(f"Performance trends analysis failed: {e}")
            return {'error': str(e)}
    
    async def emergency_stop(self) -> Dict[str, Any]:
        """Emergency stop of evolution process"""
        try:
            previous_state = self.current_state
            self.current_state = 'idle'
            
            self.logger.warning("Emergency stop activated")
            
            return {
                'success': True,
                'previous_state': previous_state,
                'current_state': self.current_state,
                'message': 'Evolution process stopped'
            }
            
        except Exception as e:
            self.logger.error(f"Emergency stop failed: {e}")
            return {'error': str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Check evolution service health"""
        try:
            return {
                'service_status': 'healthy',
                'current_state': self.current_state,
                'auto_evolution_enabled': self.config['auto_evolution_enabled'],
                'last_evolution': self.last_evolution.isoformat() if self.last_evolution else None,
                'meta_agent_available': self.meta_agent is not None,
                'config_valid': self._validate_config()
            }
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {'error': str(e)}
    
    def _validate_config(self) -> bool:
        """Validate evolution configuration"""
        try:
            required_keys = ['auto_evolution_enabled', 'evolution_interval_hours', 'performance_threshold']
            return all(key in self.config for key in required_keys)
        except:
            return False