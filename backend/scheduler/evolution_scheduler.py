import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import json

from ..services.evolution_service import EvolutionService
from ..database import get_db, SystemMetricsCRUD

class EvolutionScheduler:
    """
    Scheduler for automated system evolution and self-improvement.
    Runs periodic evolution cycles and monitors system health.
    """
    
    def __init__(self):
        self.evolution_service = EvolutionService()
        self.logger = logging.getLogger(__name__)
        
        # Scheduler configuration
        self.config = {
            'evolution_interval_hours': 24,
            'health_check_interval_minutes': 30,
            'emergency_threshold': 0.30,  # Health score below 30% triggers emergency evolution
            'auto_evolution_enabled': True,
            'max_concurrent_evolutions': 1
        }
        
        # Scheduler state
        self.running = False
        self.last_evolution = None
        self.last_health_check = None
        self.evolution_task = None
        self.health_check_task = None
        self.current_evolutions = 0
        
        # Performance tracking
        self.performance_history = []
        self.evolution_stats = {
            'total_cycles': 0,
            'successful_cycles': 0,
            'failed_cycles': 0,
            'emergency_evolutions': 0,
            'improvements_applied': 0
        }
    
    async def start(self):
        """Start the evolution scheduler"""
        if self.running:
            self.logger.warning("Evolution scheduler already running")
            return
        
        self.running = True
        self.logger.info("Starting evolution scheduler")
        
        # Start background tasks
        self.evolution_task = asyncio.create_task(self._evolution_loop())
        self.health_check_task = asyncio.create_task(self._health_check_loop())
        
        self.logger.info("Evolution scheduler started successfully")
    
    async def stop(self):
        """Stop the evolution scheduler"""
        if not self.running:
            self.logger.warning("Evolution scheduler not running")
            return
        
        self.running = False
        self.logger.info("Stopping evolution scheduler")
        
        # Cancel background tasks
        if self.evolution_task:
            self.evolution_task.cancel()
        if self.health_check_task:
            self.health_check_task.cancel()
        
        # Wait for tasks to complete
        if self.evolution_task:
            try:
                await self.evolution_task
            except asyncio.CancelledError:
                pass
        
        if self.health_check_task:
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Evolution scheduler stopped")
    
    async def _evolution_loop(self):
        """Main evolution scheduling loop"""
        while self.running:
            try:
                if not self.config['auto_evolution_enabled']:
                    await asyncio.sleep(60)  # Check every minute if auto evolution is disabled
                    continue
                
                # Check if it's time for evolution
                if self._should_run_evolution():
                    await self._run_scheduled_evolution()
                
                # Wait for next check
                await asyncio.sleep(3600)  # Check every hour
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Evolution loop error: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _health_check_loop(self):
        """Health check monitoring loop"""
        while self.running:
            try:
                await self._perform_health_check()
                
                # Wait for next health check
                await asyncio.sleep(self.config['health_check_interval_minutes'] * 60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    def _should_run_evolution(self) -> bool:
        """Determine if evolution should run"""
        if not self.config['auto_evolution_enabled']:
            return False
        
        if self.current_evolutions >= self.config['max_concurrent_evolutions']:
            return False
        
        # Check time-based trigger
        if self.last_evolution:
            time_since_last = datetime.now() - self.last_evolution
            if time_since_last.total_seconds() < self.config['evolution_interval_hours'] * 3600:
                return False
        
        return True
    
    async def _run_scheduled_evolution(self):
        """Run a scheduled evolution cycle"""
        if self.current_evolutions >= self.config['max_concurrent_evolutions']:
            self.logger.warning("Maximum concurrent evolutions reached")
            return
        
        self.current_evolutions += 1
        self.evolution_stats['total_cycles'] += 1
        
        try:
            self.logger.info("Starting scheduled evolution cycle")
            
            # Run evolution
            result = await self.evolution_service.start_evolution_cycle()
            
            if result.get('success'):
                self.evolution_stats['successful_cycles'] += 1
                self.evolution_stats['improvements_applied'] += result.get('improvements_applied', 0)
                self.last_evolution = datetime.now()
                
                # Log success
                await self._log_evolution_event('scheduled', 'success', result)
                
                self.logger.info(f"Scheduled evolution completed successfully. "
                               f"Improvements applied: {result.get('improvements_applied', 0)}")
            else:
                self.evolution_stats['failed_cycles'] += 1
                await self._log_evolution_event('scheduled', 'failed', result)
                
                self.logger.error(f"Scheduled evolution failed: {result.get('error', 'Unknown error')}")
        
        except Exception as e:
            self.evolution_stats['failed_cycles'] += 1
            self.logger.error(f"Evolution cycle exception: {e}")
            await self._log_evolution_event('scheduled', 'error', {'error': str(e)})
        
        finally:
            self.current_evolutions -= 1
    
    async def _perform_health_check(self):
        """Perform system health check"""
        try:
            # Get evolution service health
            health_result = await self.evolution_service.health_check()
            
            if health_result.get('error'):
                self.logger.warning(f"Evolution service health check failed: {health_result['error']}")
                return
            
            # Get system analysis
            from ..agents.agent_meta import AgentMeta
            meta_agent = AgentMeta()
            
            analysis = await meta_agent._analyze_system_state()
            
            if analysis:
                health_score = analysis.get('health_score', 100)
                
                # Store health metrics
                await self._store_health_metrics(health_score, analysis)
                
                # Check for emergency evolution trigger
                if health_score < self.config['emergency_threshold'] * 100:
                    await self._trigger_emergency_evolution(health_score)
                
                self.last_health_check = datetime.now()
                
                # Log health status
                self.logger.info(f"System health check completed. Health score: {health_score:.1f}")
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
    
    async def _trigger_emergency_evolution(self, health_score: float):
        """Trigger emergency evolution due to low health score"""
        if self.current_evolutions >= self.config['max_concurrent_evolutions']:
            self.logger.warning("Cannot trigger emergency evolution - max concurrent evolutions reached")
            return
        
        self.logger.warning(f"Triggering emergency evolution due to low health score: {health_score:.1f}")
        
        self.current_evolutions += 1
        self.evolution_stats['emergency_evolutions'] += 1
        
        try:
            # Force evolution with high priority
            result = await self.evolution_service.start_evolution_cycle(force=True)
            
            if result.get('success'):
                self.evolution_stats['successful_cycles'] += 1
                self.evolution_stats['improvements_applied'] += result.get('improvements_applied', 0)
                self.last_evolution = datetime.now()
                
                await self._log_evolution_event('emergency', 'success', result)
                
                self.logger.info(f"Emergency evolution completed successfully. "
                               f"Improvements applied: {result.get('improvements_applied', 0)}")
            else:
                self.evolution_stats['failed_cycles'] += 1
                await self._log_evolution_event('emergency', 'failed', result)
                
                self.logger.error(f"Emergency evolution failed: {result.get('error', 'Unknown error')}")
        
        except Exception as e:
            self.evolution_stats['failed_cycles'] += 1
            self.logger.error(f"Emergency evolution exception: {e}")
            await self._log_evolution_event('emergency', 'error', {'error': str(e)})
        
        finally:
            self.current_evolutions -= 1
    
    async def _store_health_metrics(self, health_score: float, analysis: Dict[str, Any]):
        """Store health metrics in database"""
        try:
            with get_db() as db:
                # Store health score
                SystemMetricsCRUD.create_metric(
                    db=db,
                    metric_name="system_health_score",
                    metric_value=health_score,
                    metric_type="gauge",
                    labels=json.dumps({
                        "timestamp": datetime.now().isoformat(),
                        "scheduler_check": True
                    })
                )
                
                # Store agent performance metrics
                agent_metrics = analysis.get('agent_metrics', {})
                for agent_id, metrics in agent_metrics.items():
                    SystemMetricsCRUD.create_metric(
                        db=db,
                        metric_name=f"agent_error_rate_{agent_id}",
                        metric_value=metrics.get('error_rate', 0),
                        metric_type="gauge",
                        labels=json.dumps({
                            "agent_id": agent_id,
                            "timestamp": datetime.now().isoformat()
                        })
                    )
                    
                    SystemMetricsCRUD.create_metric(
                        db=db,
                        metric_name=f"agent_response_time_{agent_id}",
                        metric_value=metrics.get('average_duration', 0),
                        metric_type="gauge",
                        labels=json.dumps({
                            "agent_id": agent_id,
                            "timestamp": datetime.now().isoformat()
                        })
                    )
                
        except Exception as e:
            self.logger.error(f"Health metrics storage failed: {e}")
    
    async def _log_evolution_event(self, evolution_type: str, status: str, result: Dict[str, Any]):
        """Log evolution event to database"""
        try:
            with get_db() as db:
                SystemMetricsCRUD.create_metric(
                    db=db,
                    metric_name=f"evolution_{evolution_type}_{status}",
                    metric_value=1,
                    metric_type="counter",
                    labels=json.dumps({
                        "evolution_type": evolution_type,
                        "status": status,
                        "improvements_applied": result.get('improvements_applied', 0),
                        "timestamp": datetime.now().isoformat()
                    })
                )
                
        except Exception as e:
            self.logger.error(f"Evolution event logging failed: {e}")
    
    async def get_scheduler_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        return {
            'running': self.running,
            'config': self.config.copy(),
            'last_evolution': self.last_evolution.isoformat() if self.last_evolution else None,
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'current_evolutions': self.current_evolutions,
            'evolution_stats': self.evolution_stats.copy(),
            'next_scheduled_evolution': self._get_next_scheduled_evolution(),
            'next_health_check': self._get_next_health_check()
        }
    
    def _get_next_scheduled_evolution(self) -> Optional[str]:
        """Get next scheduled evolution time"""
        if not self.config['auto_evolution_enabled']:
            return None
        
        if self.last_evolution:
            next_evolution = self.last_evolution + timedelta(hours=self.config['evolution_interval_hours'])
        else:
            next_evolution = datetime.now() + timedelta(hours=self.config['evolution_interval_hours'])
        
        return next_evolution.isoformat()
    
    def _get_next_health_check(self) -> Optional[str]:
        """Get next health check time"""
        if self.last_health_check:
            next_check = self.last_health_check + timedelta(minutes=self.config['health_check_interval_minutes'])
        else:
            next_check = datetime.now() + timedelta(minutes=self.config['health_check_interval_minutes'])
        
        return next_check.isoformat()
    
    async def update_config(self, **kwargs) -> Dict[str, Any]:
        """Update scheduler configuration"""
        updated = {}
        
        for key, value in kwargs.items():
            if key in self.config:
                self.config[key] = value
                updated[key] = value
        
        # Update evolution service config if needed
        if 'evolution_interval_hours' in updated:
            await self.evolution_service.configure_evolution(
                evolution_interval_hours=updated['evolution_interval_hours']
            )
        
        if 'auto_evolution_enabled' in updated:
            await self.evolution_service.configure_evolution(
                auto_evolution_enabled=updated['auto_evolution_enabled']
            )
        
        self.logger.info(f"Scheduler configuration updated: {updated}")
        
        return {
            'success': True,
            'updated_config': updated,
            'current_config': self.config.copy()
        }
    
    async def force_evolution(self, evolution_type: str = 'manual') -> Dict[str, Any]:
        """Force an evolution cycle immediately"""
        if self.current_evolutions >= self.config['max_concurrent_evolutions']:
            return {
                'error': 'Maximum concurrent evolutions reached',
                'current_evolutions': self.current_evolutions,
                'max_concurrent': self.config['max_concurrent_evolutions']
            }
        
        self.current_evolutions += 1
        self.evolution_stats['total_cycles'] += 1
        
        try:
            self.logger.info(f"Starting forced evolution cycle: {evolution_type}")
            
            result = await self.evolution_service.start_evolution_cycle(force=True)
            
            if result.get('success'):
                self.evolution_stats['successful_cycles'] += 1
                self.evolution_stats['improvements_applied'] += result.get('improvements_applied', 0)
                self.last_evolution = datetime.now()
                
                await self._log_evolution_event(evolution_type, 'success', result)
                
                return {
                    'success': True,
                    'evolution_type': evolution_type,
                    'improvements_applied': result.get('improvements_applied', 0),
                    'message': 'Forced evolution completed successfully'
                }
            else:
                self.evolution_stats['failed_cycles'] += 1
                await self._log_evolution_event(evolution_type, 'failed', result)
                
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error'),
                    'evolution_type': evolution_type
                }
        
        except Exception as e:
            self.evolution_stats['failed_cycles'] += 1
            self.logger.error(f"Forced evolution exception: {e}")
            await self._log_evolution_event(evolution_type, 'error', {'error': str(e)})
            
            return {
                'success': False,
                'error': str(e),
                'evolution_type': evolution_type
            }
        
        finally:
            self.current_evolutions -= 1
    
    async def get_performance_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get performance trends over specified days"""
        try:
            with get_db() as db:
                cutoff_time = datetime.now() - timedelta(days=days)
                
                # Get health score trends
                health_metrics = SystemMetricsCRUD.get_metrics_by_name_since(
                    db, "system_health_score", cutoff_time
                )
                
                # Get evolution metrics
                evolution_metrics = SystemMetricsCRUD.get_metrics_by_pattern_since(
                    db, "evolution_%", cutoff_time
                )
                
                # Process trends
                trends = {
                    'health_trend': self._calculate_health_trend(health_metrics),
                    'evolution_frequency': self._calculate_evolution_frequency(evolution_metrics),
                    'improvement_rate': self._calculate_improvement_rate(evolution_metrics),
                    'period_days': days,
                    'analysis_timestamp': datetime.now().isoformat()
                }
                
                return trends
                
        except Exception as e:
            self.logger.error(f"Performance trends analysis failed: {e}")
            return {'error': str(e)}
    
    def _calculate_health_trend(self, health_metrics: List) -> Dict[str, Any]:
        """Calculate health score trend"""
        if not health_metrics:
            return {'trend': 'no_data', 'values': []}
        
        values = [metric.metric_value for metric in health_metrics]
        
        if len(values) < 2:
            return {'trend': 'insufficient_data', 'values': values}
        
        # Simple trend calculation
        recent_avg = sum(values[-5:]) / min(5, len(values))
        earlier_avg = sum(values[:5]) / min(5, len(values))
        
        if recent_avg > earlier_avg + 5:
            trend = 'improving'
        elif recent_avg < earlier_avg - 5:
            trend = 'declining'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'values': values,
            'recent_average': recent_avg,
            'earlier_average': earlier_avg,
            'change': recent_avg - earlier_avg
        }
    
    def _calculate_evolution_frequency(self, evolution_metrics: List) -> Dict[str, Any]:
        """Calculate evolution frequency"""
        if not evolution_metrics:
            return {'frequency': 0, 'events': []}
        
        # Count successful evolutions
        successful_evolutions = [
            metric for metric in evolution_metrics
            if 'success' in metric.metric_name
        ]
        
        return {
            'frequency': len(successful_evolutions),
            'total_events': len(evolution_metrics),
            'success_rate': len(successful_evolutions) / len(evolution_metrics) if evolution_metrics else 0
        }
    
    def _calculate_improvement_rate(self, evolution_metrics: List) -> Dict[str, Any]:
        """Calculate improvement application rate"""
        total_improvements = 0
        
        for metric in evolution_metrics:
            if 'success' in metric.metric_name and metric.labels:
                try:
                    labels = json.loads(metric.labels)
                    total_improvements += labels.get('improvements_applied', 0)
                except json.JSONDecodeError:
                    continue
        
        return {
            'total_improvements': total_improvements,
            'average_per_cycle': total_improvements / len(evolution_metrics) if evolution_metrics else 0
        }

# Global scheduler instance
scheduler = EvolutionScheduler()