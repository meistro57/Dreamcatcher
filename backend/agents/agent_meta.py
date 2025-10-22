import asyncio
import json
import os
import subprocess
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import hashlib
import ast
import re

from .base_agent import BaseAgent

try:  # pragma: no cover
    from ..database import get_db, SystemMetricsCRUD, AgentLogCRUD
    from ..services import AIService
except ImportError:  # pragma: no cover
    from database import get_db, SystemMetricsCRUD, AgentLogCRUD
    from services import AIService

class AgentMeta(BaseAgent):
    """
    Meta-agent responsible for system self-improvement and evolution.
    Analyzes agent performance, identifies improvement opportunities,
    and uses Claude Code to evolve the system.
    """
    
    def __init__(self):
        super().__init__(
            agent_id="meta",
            name="Meta Evolution Agent",
            description="I analyze. I evolve. I make us better while you sleep.",
            version="1.0.0"
        )
        
        # Initialize AI service
        self.ai_service = AIService()
        
        # Claude Code integration
        self.claude_code_available = self._check_claude_code()
        
        # Evolution strategies
        self.evolution_strategies = {
            'performance_optimization': self._optimize_performance,
            'error_reduction': self._reduce_errors,
            'feature_enhancement': self._enhance_features,
            'code_quality': self._improve_code_quality,
            'agent_coordination': self._improve_coordination
        }
        
        # Performance thresholds
        self.performance_thresholds = {
            'error_rate': 0.05,  # 5% error rate triggers improvement
            'response_time': 10.0,  # 10 seconds max response time
            'success_rate': 0.95,  # 95% success rate minimum
            'user_satisfaction': 0.80  # 80% satisfaction minimum
        }
        
        # Code patterns for improvement
        self.improvement_patterns = {
            'error_handling': r'except\s+Exception\s+as\s+e:',
            'performance_issues': r'time\.sleep\(\d+\)',
            'hardcoded_values': r'["\'][\w\s]+["\']',
            'duplicate_code': r'def\s+(\w+)\s*\(',
            'memory_leaks': r'while\s+True:.*(?!break)'
        }
        
        # System directories
        self.agent_dir = "/home/mark/Dreamcatcher/backend/agents"
        self.backup_dir = "/home/mark/Dreamcatcher/backups/agents"
        self.evolution_log = "/home/mark/Dreamcatcher/logs/evolution.log"
        
        # Ensure directories exist
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.evolution_log), exist_ok=True)
    
    def _check_claude_code(self) -> bool:
        """Check if Claude Code is available"""
        try:
            result = subprocess.run(['claude-code', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process self-improvement request"""
        improvement_type = data.get('type', 'performance_optimization')
        target_agent = data.get('agent_id', None)
        
        try:
            # Analyze current system state
            analysis = await self._analyze_system_state()
            
            if not analysis:
                return {'error': 'Failed to analyze system state'}
            
            # Identify improvement opportunities
            opportunities = await self._identify_opportunities(analysis, target_agent)
            
            if not opportunities:
                return {
                    'success': True,
                    'message': 'No improvement opportunities identified',
                    'analysis': analysis
                }
            
            # Execute improvements
            improvements = []
            for opportunity in opportunities:
                result = await self._execute_improvement(opportunity)
                if result:
                    improvements.append(result)
            
            # Log evolution
            await self._log_evolution(improvements)
            
            return {
                'success': True,
                'improvements_made': len(improvements),
                'improvements': improvements,
                'analysis': analysis,
                'message': f"System evolved with {len(improvements)} improvements"
            }
            
        except Exception as e:
            self.logger.error(f"Meta evolution failed: {e}")
            return {'error': f'Evolution failed: {str(e)}'}
    
    async def _analyze_system_state(self) -> Dict[str, Any]:
        """Analyze current system performance and health"""
        try:
            with get_db() as db:
                # Get agent performance metrics
                agent_metrics = await self._get_agent_metrics(db)
                
                # Get error patterns
                error_patterns = await self._analyze_error_patterns(db)
                
                # Get system resource usage
                resource_usage = await self._get_resource_usage()
                
                # Get user feedback patterns
                user_patterns = await self._analyze_user_patterns(db)
                
                # Generate overall health score
                health_score = await self._calculate_health_score(
                    agent_metrics, error_patterns, resource_usage, user_patterns
                )
                
                return {
                    'timestamp': datetime.now().isoformat(),
                    'health_score': health_score,
                    'agent_metrics': agent_metrics,
                    'error_patterns': error_patterns,
                    'resource_usage': resource_usage,
                    'user_patterns': user_patterns
                }
                
        except Exception as e:
            self.logger.error(f"System analysis failed: {e}")
            return None
    
    async def _get_agent_metrics(self, db) -> Dict[str, Any]:
        """Get performance metrics for all agents"""
        try:
            # Get recent agent logs
            cutoff_time = datetime.now() - timedelta(days=7)
            logs = AgentLogCRUD.get_logs_since(db, cutoff_time)
            
            metrics = {}
            for log in logs:
                agent_id = log.agent_id
                if agent_id not in metrics:
                    metrics[agent_id] = {
                        'total_executions': 0,
                        'successful_executions': 0,
                        'failed_executions': 0,
                        'average_duration': 0,
                        'error_rate': 0,
                        'recent_errors': []
                    }
                
                metrics[agent_id]['total_executions'] += 1
                
                if log.status == 'completed':
                    metrics[agent_id]['successful_executions'] += 1
                elif log.status == 'failed':
                    metrics[agent_id]['failed_executions'] += 1
                    if log.error_message:
                        metrics[agent_id]['recent_errors'].append(log.error_message)
                
                if log.duration:
                    current_avg = metrics[agent_id]['average_duration']
                    total_execs = metrics[agent_id]['total_executions']
                    metrics[agent_id]['average_duration'] = (
                        (current_avg * (total_execs - 1) + log.duration) / total_execs
                    )
            
            # Calculate error rates
            for agent_id, data in metrics.items():
                if data['total_executions'] > 0:
                    data['error_rate'] = data['failed_executions'] / data['total_executions']
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Agent metrics analysis failed: {e}")
            return {}
    
    async def _analyze_error_patterns(self, db) -> Dict[str, Any]:
        """Analyze error patterns across the system"""
        try:
            # Get recent errors
            cutoff_time = datetime.now() - timedelta(days=7)
            error_logs = AgentLogCRUD.get_error_logs_since(db, cutoff_time)
            
            patterns = {
                'common_errors': {},
                'error_frequency': {},
                'critical_errors': [],
                'recurring_issues': []
            }
            
            for log in error_logs:
                if log.error_message:
                    # Count common error types
                    error_type = self._classify_error(log.error_message)
                    patterns['common_errors'][error_type] = patterns['common_errors'].get(error_type, 0) + 1
                    
                    # Track frequency by day
                    day = log.started_at.date().isoformat()
                    if day not in patterns['error_frequency']:
                        patterns['error_frequency'][day] = 0
                    patterns['error_frequency'][day] += 1
                    
                    # Identify critical errors
                    if any(keyword in log.error_message.lower() for keyword in ['timeout', 'memory', 'database', 'api']):
                        patterns['critical_errors'].append({
                            'agent_id': log.agent_id,
                            'error': log.error_message,
                            'timestamp': log.started_at.isoformat()
                        })
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error pattern analysis failed: {e}")
            return {}
    
    def _classify_error(self, error_message: str) -> str:
        """Classify error into categories"""
        error_lower = error_message.lower()
        
        if 'timeout' in error_lower:
            return 'timeout'
        elif 'connection' in error_lower:
            return 'connection'
        elif 'api' in error_lower:
            return 'api_error'
        elif 'database' in error_lower:
            return 'database_error'
        elif 'memory' in error_lower:
            return 'memory_error'
        elif 'file' in error_lower:
            return 'file_error'
        else:
            return 'other'
    
    async def _get_resource_usage(self) -> Dict[str, Any]:
        """Get system resource usage"""
        try:
            # Get basic system info
            import psutil
            
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'process_count': len(psutil.pids()),
                'timestamp': datetime.now().isoformat()
            }
            
        except ImportError:
            # Fallback if psutil not available
            return {
                'cpu_percent': 0,
                'memory_percent': 0,
                'disk_percent': 0,
                'process_count': 0,
                'timestamp': datetime.now().isoformat()
            }
    
    async def _analyze_user_patterns(self, db) -> Dict[str, Any]:
        """Analyze user interaction patterns"""
        try:
            # Get system metrics for user interactions
            cutoff_time = datetime.now() - timedelta(days=7)
            metrics = SystemMetricsCRUD.get_metrics_since(db, cutoff_time)
            
            patterns = {
                'idea_capture_rate': 0,
                'completion_rate': 0,
                'peak_usage_hours': [],
                'preferred_categories': {},
                'satisfaction_indicators': {}
            }
            
            for metric in metrics:
                if metric.metric_name == 'idea_captured':
                    patterns['idea_capture_rate'] += metric.metric_value
                elif metric.metric_name == 'proposal_completed':
                    patterns['completion_rate'] += metric.metric_value
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"User pattern analysis failed: {e}")
            return {}
    
    async def _calculate_health_score(self, agent_metrics: Dict, error_patterns: Dict, 
                                    resource_usage: Dict, user_patterns: Dict) -> float:
        """Calculate overall system health score (0-100)"""
        try:
            score = 100.0
            
            # Agent performance impact
            for agent_id, metrics in agent_metrics.items():
                error_rate = metrics.get('error_rate', 0)
                if error_rate > self.performance_thresholds['error_rate']:
                    score -= (error_rate - self.performance_thresholds['error_rate']) * 200
                
                avg_duration = metrics.get('average_duration', 0)
                if avg_duration > self.performance_thresholds['response_time']:
                    score -= (avg_duration - self.performance_thresholds['response_time']) * 2
            
            # Error pattern impact
            critical_errors = len(error_patterns.get('critical_errors', []))
            score -= critical_errors * 5
            
            # Resource usage impact
            cpu_usage = resource_usage.get('cpu_percent', 0)
            memory_usage = resource_usage.get('memory_percent', 0)
            
            if cpu_usage > 80:
                score -= (cpu_usage - 80) * 0.5
            if memory_usage > 80:
                score -= (memory_usage - 80) * 0.5
            
            return max(0, min(100, score))
            
        except Exception as e:
            self.logger.error(f"Health score calculation failed: {e}")
            return 50.0  # Default neutral score
    
    async def _identify_opportunities(self, analysis: Dict[str, Any], target_agent: str = None) -> List[Dict[str, Any]]:
        """Identify improvement opportunities based on analysis"""
        opportunities = []
        
        try:
            # Performance optimization opportunities
            agent_metrics = analysis.get('agent_metrics', {})
            for agent_id, metrics in agent_metrics.items():
                if target_agent and agent_id != target_agent:
                    continue
                
                # High error rate
                if metrics.get('error_rate', 0) > self.performance_thresholds['error_rate']:
                    opportunities.append({
                        'type': 'error_reduction',
                        'agent_id': agent_id,
                        'priority': 'high',
                        'description': f"High error rate ({metrics['error_rate']:.2%}) in {agent_id}",
                        'metric_value': metrics['error_rate']
                    })
                
                # Slow response time
                if metrics.get('average_duration', 0) > self.performance_thresholds['response_time']:
                    opportunities.append({
                        'type': 'performance_optimization',
                        'agent_id': agent_id,
                        'priority': 'medium',
                        'description': f"Slow response time ({metrics['average_duration']:.1f}s) in {agent_id}",
                        'metric_value': metrics['average_duration']
                    })
            
            # Code quality opportunities
            for agent_id in agent_metrics.keys():
                if target_agent and agent_id != target_agent:
                    continue
                
                code_issues = await self._analyze_code_quality(agent_id)
                if code_issues:
                    opportunities.append({
                        'type': 'code_quality',
                        'agent_id': agent_id,
                        'priority': 'low',
                        'description': f"Code quality issues in {agent_id}",
                        'issues': code_issues
                    })
            
            # System-wide opportunities
            health_score = analysis.get('health_score', 100)
            if health_score < 80:
                opportunities.append({
                    'type': 'feature_enhancement',
                    'agent_id': 'system',
                    'priority': 'medium',
                    'description': f"Low system health score ({health_score:.1f})",
                    'metric_value': health_score
                })
            
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Opportunity identification failed: {e}")
            return []
    
    async def _analyze_code_quality(self, agent_id: str) -> List[str]:
        """Analyze code quality for specific agent"""
        try:
            agent_file = f"{self.agent_dir}/agent_{agent_id}.py"
            
            if not os.path.exists(agent_file):
                return []
            
            with open(agent_file, 'r') as f:
                code = f.read()
            
            issues = []
            
            # Check for improvement patterns
            for pattern_name, pattern in self.improvement_patterns.items():
                matches = re.findall(pattern, code)
                if matches:
                    issues.append(f"{pattern_name}: {len(matches)} instances")
            
            # Check for code complexity
            try:
                tree = ast.parse(code)
                complexity = self._calculate_complexity(tree)
                if complexity > 10:
                    issues.append(f"High complexity: {complexity}")
            except SyntaxError:
                issues.append("Syntax issues detected")
            
            return issues
            
        except Exception as e:
            self.logger.error(f"Code quality analysis failed for {agent_id}: {e}")
            return []
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
        
        return complexity
    
    async def _execute_improvement(self, opportunity: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute a specific improvement"""
        try:
            improvement_type = opportunity['type']
            
            if improvement_type in self.evolution_strategies:
                strategy = self.evolution_strategies[improvement_type]
                result = await strategy(opportunity)
                
                if result:
                    return {
                        'opportunity': opportunity,
                        'result': result,
                        'timestamp': datetime.now().isoformat()
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Improvement execution failed: {e}")
            return None
    
    async def _optimize_performance(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize agent performance"""
        agent_id = opportunity['agent_id']
        
        try:
            # Create backup first
            await self._backup_agent(agent_id)
            
            # Analyze current code
            agent_file = f"{self.agent_dir}/agent_{agent_id}.py"
            
            if not os.path.exists(agent_file):
                return {'error': f'Agent file not found: {agent_file}'}
            
            with open(agent_file, 'r') as f:
                current_code = f.read()
            
            # Use Claude to optimize performance
            optimized_code = await self._claude_optimize_performance(current_code, opportunity)
            
            if optimized_code and optimized_code != current_code:
                # Validate the optimized code
                if await self._validate_code(optimized_code):
                    # Write optimized code
                    with open(agent_file, 'w') as f:
                        f.write(optimized_code)
                    
                    return {
                        'action': 'performance_optimization',
                        'agent_id': agent_id,
                        'changes': 'Performance optimizations applied',
                        'backup_created': True
                    }
            
            return {'error': 'No valid optimizations generated'}
            
        except Exception as e:
            self.logger.error(f"Performance optimization failed: {e}")
            return {'error': str(e)}
    
    async def _reduce_errors(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Reduce errors in agent code"""
        agent_id = opportunity['agent_id']
        
        try:
            # Create backup first
            await self._backup_agent(agent_id)
            
            # Get current code
            agent_file = f"{self.agent_dir}/agent_{agent_id}.py"
            
            with open(agent_file, 'r') as f:
                current_code = f.read()
            
            # Use Claude to improve error handling
            improved_code = await self._claude_improve_errors(current_code, opportunity)
            
            if improved_code and improved_code != current_code:
                if await self._validate_code(improved_code):
                    with open(agent_file, 'w') as f:
                        f.write(improved_code)
                    
                    return {
                        'action': 'error_reduction',
                        'agent_id': agent_id,
                        'changes': 'Error handling improvements applied',
                        'backup_created': True
                    }
            
            return {'error': 'No valid error improvements generated'}
            
        except Exception as e:
            self.logger.error(f"Error reduction failed: {e}")
            return {'error': str(e)}
    
    async def _enhance_features(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance agent features"""
        try:
            # Feature enhancement based on system analysis
            enhancement_suggestions = await self._claude_suggest_features(opportunity)
            
            return {
                'action': 'feature_enhancement',
                'suggestions': enhancement_suggestions,
                'requires_manual_review': True
            }
            
        except Exception as e:
            self.logger.error(f"Feature enhancement failed: {e}")
            return {'error': str(e)}
    
    async def _improve_code_quality(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Improve code quality"""
        agent_id = opportunity['agent_id']
        
        try:
            # Create backup first
            await self._backup_agent(agent_id)
            
            # Get current code
            agent_file = f"{self.agent_dir}/agent_{agent_id}.py"
            
            with open(agent_file, 'r') as f:
                current_code = f.read()
            
            # Use Claude to improve code quality
            improved_code = await self._claude_improve_quality(current_code, opportunity)
            
            if improved_code and improved_code != current_code:
                if await self._validate_code(improved_code):
                    with open(agent_file, 'w') as f:
                        f.write(improved_code)
                    
                    return {
                        'action': 'code_quality_improvement',
                        'agent_id': agent_id,
                        'changes': 'Code quality improvements applied',
                        'backup_created': True
                    }
            
            return {'error': 'No valid quality improvements generated'}
            
        except Exception as e:
            self.logger.error(f"Code quality improvement failed: {e}")
            return {'error': str(e)}
    
    async def _improve_coordination(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Improve agent coordination"""
        try:
            # Analyze agent communication patterns
            coordination_analysis = await self._claude_analyze_coordination(opportunity)
            
            return {
                'action': 'coordination_improvement',
                'analysis': coordination_analysis,
                'requires_manual_review': True
            }
            
        except Exception as e:
            self.logger.error(f"Coordination improvement failed: {e}")
            return {'error': str(e)}
    
    async def _backup_agent(self, agent_id: str) -> bool:
        """Create backup of agent before modification"""
        try:
            agent_file = f"{self.agent_dir}/agent_{agent_id}.py"
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f"{self.backup_dir}/agent_{agent_id}_{timestamp}.py"
            
            if os.path.exists(agent_file):
                with open(agent_file, 'r') as src, open(backup_file, 'w') as dst:
                    dst.write(src.read())
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Backup failed for {agent_id}: {e}")
            return False
    
    async def _validate_code(self, code: str) -> bool:
        """Validate code syntax and basic structure"""
        try:
            # Check syntax
            ast.parse(code)
            
            # Check for required methods
            if 'async def process(' not in code:
                return False
            
            # Check for imports
            if 'from .base_agent import BaseAgent' not in code:
                return False
            
            return True
            
        except SyntaxError:
            return False
    
    async def _claude_optimize_performance(self, code: str, opportunity: Dict[str, Any]) -> str:
        """Use Claude to optimize performance"""
        try:
            prompt = f"""
            Optimize this Python agent code for performance:

            Current code:
            ```python
            {code}
            ```

            Performance issue: {opportunity['description']}
            Current metric: {opportunity.get('metric_value', 'N/A')}

            Please optimize for:
            1. Faster execution time
            2. Better resource usage
            3. Improved async/await patterns
            4. Efficient database operations
            5. Memory optimization

            Return only the optimized code, maintaining all existing functionality.
            Preserve the class structure and method signatures.
            """
            
            response = await self.ai_service.get_completion(
                prompt=prompt,
                model="claude-3-sonnet",
                max_tokens=3000,
                temperature=0.3
            )
            
            return response or ""
            
        except Exception as e:
            self.logger.error(f"Claude performance optimization failed: {e}")
            return ""
    
    async def _claude_improve_errors(self, code: str, opportunity: Dict[str, Any]) -> str:
        """Use Claude to improve error handling"""
        try:
            prompt = f"""
            Improve error handling in this Python agent code:

            Current code:
            ```python
            {code}
            ```

            Error issue: {opportunity['description']}
            Error rate: {opportunity.get('metric_value', 'N/A')}

            Please improve:
            1. Better exception handling
            2. More specific error messages
            3. Graceful failure recovery
            4. Timeout handling
            5. Input validation

            Return only the improved code, maintaining all existing functionality.
            """
            
            response = await self.ai_service.get_completion(
                prompt=prompt,
                model="claude-3-sonnet",
                max_tokens=3000,
                temperature=0.3
            )
            
            return response or ""
            
        except Exception as e:
            self.logger.error(f"Claude error improvement failed: {e}")
            return ""
    
    async def _claude_improve_quality(self, code: str, opportunity: Dict[str, Any]) -> str:
        """Use Claude to improve code quality"""
        try:
            issues = opportunity.get('issues', [])
            
            prompt = f"""
            Improve the code quality of this Python agent:

            Current code:
            ```python
            {code}
            ```

            Identified issues: {', '.join(issues)}

            Please improve:
            1. Code readability and documentation
            2. Remove duplicate code
            3. Better variable naming
            4. Proper type hints
            5. Consistent formatting

            Return only the improved code, maintaining all existing functionality.
            """
            
            response = await self.ai_service.get_completion(
                prompt=prompt,
                model="claude-3-sonnet",
                max_tokens=3000,
                temperature=0.3
            )
            
            return response or ""
            
        except Exception as e:
            self.logger.error(f"Claude quality improvement failed: {e}")
            return ""
    
    async def _claude_suggest_features(self, opportunity: Dict[str, Any]) -> List[str]:
        """Use Claude to suggest feature enhancements"""
        try:
            prompt = f"""
            Based on this system analysis, suggest feature enhancements:

            System health score: {opportunity.get('metric_value', 'N/A')}
            Issue: {opportunity['description']}

            Suggest 3-5 specific feature enhancements that would:
            1. Improve system reliability
            2. Enhance user experience
            3. Optimize performance
            4. Add valuable functionality

            Return as a JSON array of feature suggestions.
            """
            
            response = await self.ai_service.get_completion(
                prompt=prompt,
                model="claude-3-sonnet",
                max_tokens=800,
                temperature=0.7
            )
            
            if response:
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    return [response]
            
            return []
            
        except Exception as e:
            self.logger.error(f"Claude feature suggestion failed: {e}")
            return []
    
    async def _claude_analyze_coordination(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Use Claude to analyze agent coordination"""
        try:
            prompt = f"""
            Analyze agent coordination patterns and suggest improvements:

            Issue: {opportunity['description']}

            Analyze:
            1. Agent communication efficiency
            2. Message queue optimization
            3. Workflow bottlenecks
            4. Coordination patterns

            Suggest specific improvements for better agent coordination.
            Return as JSON with analysis and recommendations.
            """
            
            response = await self.ai_service.get_completion(
                prompt=prompt,
                model="claude-3-sonnet",
                max_tokens=1000,
                temperature=0.5
            )
            
            if response:
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    return {'analysis': response}
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Claude coordination analysis failed: {e}")
            return {}
    
    async def _log_evolution(self, improvements: List[Dict[str, Any]]):
        """Log evolution activities"""
        try:
            with open(self.evolution_log, 'a') as f:
                for improvement in improvements:
                    log_entry = {
                        'timestamp': datetime.now().isoformat(),
                        'improvement': improvement,
                        'agent': self.agent_id
                    }
                    f.write(json.dumps(log_entry) + '\n')
                    
        except Exception as e:
            self.logger.error(f"Evolution logging failed: {e}")
    
    async def schedule_evolution(self, interval_hours: int = 24) -> Dict[str, Any]:
        """Schedule automatic evolution"""
        try:
            # In a real implementation, this would integrate with the scheduler
            # For now, we'll just log the scheduling
            
            self.logger.info(f"Scheduled evolution every {interval_hours} hours")
            
            return {
                'success': True,
                'interval_hours': interval_hours,
                'next_evolution': (datetime.now() + timedelta(hours=interval_hours)).isoformat(),
                'message': f"Evolution scheduled every {interval_hours} hours"
            }
            
        except Exception as e:
            self.logger.error(f"Evolution scheduling failed: {e}")
            return {'error': f'Scheduling failed: {str(e)}'}
    
    async def get_evolution_history(self) -> List[Dict[str, Any]]:
        """Get history of system evolutions"""
        try:
            if not os.path.exists(self.evolution_log):
                return []
            
            history = []
            with open(self.evolution_log, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        history.append(entry)
                    except json.JSONDecodeError:
                        continue
            
            return history[-50:]  # Return last 50 entries
            
        except Exception as e:
            self.logger.error(f"Evolution history retrieval failed: {e}")
            return []
    
    async def rollback_agent(self, agent_id: str, backup_timestamp: str = None) -> Dict[str, Any]:
        """Rollback agent to previous version"""
        try:
            if backup_timestamp:
                backup_file = f"{self.backup_dir}/agent_{agent_id}_{backup_timestamp}.py"
            else:
                # Find most recent backup
                import glob
                backups = glob.glob(f"{self.backup_dir}/agent_{agent_id}_*.py")
                if not backups:
                    return {'error': f'No backups found for agent {agent_id}'}
                backup_file = max(backups, key=os.path.getctime)
            
            if not os.path.exists(backup_file):
                return {'error': f'Backup file not found: {backup_file}'}
            
            agent_file = f"{self.agent_dir}/agent_{agent_id}.py"
            
            # Copy backup to current
            with open(backup_file, 'r') as src, open(agent_file, 'w') as dst:
                dst.write(src.read())
            
            return {
                'success': True,
                'agent_id': agent_id,
                'restored_from': backup_file,
                'message': f'Agent {agent_id} rolled back successfully'
            }
            
        except Exception as e:
            self.logger.error(f"Agent rollback failed: {e}")
            return {'error': f'Rollback failed: {str(e)}'}