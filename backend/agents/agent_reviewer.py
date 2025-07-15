import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random

from .base_agent import BaseAgent
from ..database import get_db, IdeaCRUD, ProposalCRUD, SystemMetricsCRUD
from ..services import AIService

class AgentReviewer(BaseAgent):
    """
    Agent responsible for scheduled reviews and idea resurrection.
    Periodically surfaces dormant ideas and reassesses their potential.
    """
    
    def __init__(self):
        super().__init__(
            agent_id="reviewer",
            name="Review Agent",
            description="Time to revisit a hidden gem from your archives.",
            version="1.0.0"
        )
        
        # Initialize AI service
        self.ai_service = AIService()
        
        # Review strategies
        self.review_strategies = {
            'time_based': self._review_by_time,
            'context_based': self._review_by_context,
            'pattern_based': self._review_by_patterns,
            'serendipity': self._review_by_serendipity,
            'priority_queue': self._review_priority_queue
        }
        
        # Review types
        self.review_types = {
            'daily': {'frequency': 'daily', 'max_ideas': 3, 'age_threshold': 1},
            'weekly': {'frequency': 'weekly', 'max_ideas': 5, 'age_threshold': 7},
            'monthly': {'frequency': 'monthly', 'max_ideas': 10, 'age_threshold': 30},
            'quarterly': {'frequency': 'quarterly', 'max_ideas': 20, 'age_threshold': 90},
            'priority': {'frequency': 'immediate', 'max_ideas': 1, 'age_threshold': 0}
        }
        
        # Context awareness factors
        self.context_factors = [
            'current_season',
            'time_of_day',
            'recent_activity_patterns',
            'project_completion_status',
            'available_resources',
            'mood_indicators'
        ]
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process review request"""
        review_type = data.get('review_type', 'daily')
        strategy = data.get('strategy', 'time_based')
        
        try:
            # Get review configuration
            config = self.review_types.get(review_type, self.review_types['daily'])
            
            # Execute review strategy
            strategy_func = self.review_strategies.get(strategy, self._review_by_time)
            candidates = await strategy_func(config)
            
            if not candidates:
                return {
                    'success': True,
                    'message': 'No ideas ready for review at this time',
                    'reviewed_count': 0,
                    'next_review': self._calculate_next_review(review_type)
                }
            
            # Process each candidate
            review_results = []
            for candidate in candidates:
                result = await self._process_candidate(candidate, review_type)
                if result:
                    review_results.append(result)
            
            # Update system metrics
            await self._update_review_metrics(review_type, len(review_results))
            
            return {
                'success': True,
                'review_type': review_type,
                'strategy': strategy,
                'reviewed_count': len(review_results),
                'results': review_results,
                'next_review': self._calculate_next_review(review_type),
                'message': f"Reviewed {len(review_results)} ideas using {strategy} strategy"
            }
            
        except Exception as e:
            self.logger.error(f"Error during {review_type} review: {e}")
            return {'error': f'Review failed: {str(e)}'}
    
    async def _review_by_time(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Review ideas based on age and dormancy"""
        try:
            with get_db() as db:
                age_threshold = config['age_threshold']
                max_ideas = config['max_ideas']
                
                # Get dormant ideas
                cutoff_date = datetime.now() - timedelta(days=age_threshold)
                
                ideas = IdeaCRUD.get_dormant_ideas(db, cutoff_date, max_ideas)
                
                candidates = []
                for idea in ideas:
                    # Calculate dormancy score
                    days_dormant = (datetime.now() - idea.created_at).days
                    dormancy_score = min(100, days_dormant * 2)  # 2 points per day
                    
                    candidates.append({
                        'idea': idea,
                        'dormancy_score': dormancy_score,
                        'reason': f"Dormant for {days_dormant} days",
                        'review_priority': dormancy_score
                    })
                
                # Sort by dormancy score
                candidates.sort(key=lambda x: x['dormancy_score'], reverse=True)
                
                return candidates
                
        except Exception as e:
            self.logger.error(f"Time-based review failed: {e}")
            return []
    
    async def _review_by_context(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Review ideas based on current context"""
        try:
            with get_db() as db:
                # Get current context
                current_context = await self._analyze_current_context()
                
                # Get all ideas that might match current context
                ideas = IdeaCRUD.get_ideas_for_context_review(db, limit=config['max_ideas'] * 3)
                
                candidates = []
                for idea in ideas:
                    # Score relevance to current context
                    context_score = await self._score_context_relevance(idea, current_context)
                    
                    if context_score > 60:  # Threshold for context relevance
                        candidates.append({
                            'idea': idea,
                            'context_score': context_score,
                            'reason': f"High relevance to current context ({context_score}%)",
                            'review_priority': context_score,
                            'context_factors': current_context
                        })
                
                # Sort by context score
                candidates.sort(key=lambda x: x['context_score'], reverse=True)
                
                return candidates[:config['max_ideas']]
                
        except Exception as e:
            self.logger.error(f"Context-based review failed: {e}")
            return []
    
    async def _review_by_patterns(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Review ideas based on user patterns and preferences"""
        try:
            with get_db() as db:
                # Analyze user patterns
                patterns = await self._analyze_user_patterns(db)
                
                # Get ideas that match successful patterns
                ideas = IdeaCRUD.get_ideas_by_patterns(db, patterns, config['max_ideas'])
                
                candidates = []
                for idea in ideas:
                    pattern_score = await self._score_pattern_match(idea, patterns)
                    
                    if pattern_score > 70:
                        candidates.append({
                            'idea': idea,
                            'pattern_score': pattern_score,
                            'reason': f"Matches successful patterns ({pattern_score}%)",
                            'review_priority': pattern_score,
                            'matching_patterns': patterns
                        })
                
                return candidates
                
        except Exception as e:
            self.logger.error(f"Pattern-based review failed: {e}")
            return []
    
    async def _review_by_serendipity(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Review random ideas for serendipitous discoveries"""
        try:
            with get_db() as db:
                # Get random sample of older ideas
                ideas = IdeaCRUD.get_random_ideas(db, config['max_ideas'] * 2)
                
                candidates = []
                for idea in ideas:
                    # Random serendipity score with some intelligence
                    base_score = random.randint(40, 90)
                    
                    # Boost score for interesting characteristics
                    if idea.novelty_score and idea.novelty_score > 80:
                        base_score += 10
                    if idea.category == 'metaphysical':
                        base_score += 5  # Boost for mystery
                    
                    candidates.append({
                        'idea': idea,
                        'serendipity_score': base_score,
                        'reason': "Serendipitous discovery - sometimes the best ideas come from unexpected places",
                        'review_priority': base_score
                    })
                
                # Sort by serendipity score
                candidates.sort(key=lambda x: x['serendipity_score'], reverse=True)
                
                return candidates[:config['max_ideas']]
                
        except Exception as e:
            self.logger.error(f"Serendipity-based review failed: {e}")
            return []
    
    async def _review_priority_queue(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Review high-priority items immediately"""
        try:
            with get_db() as db:
                # Get high-priority proposals or ideas
                priority_items = ProposalCRUD.get_priority_proposals(db, config['max_ideas'])
                
                candidates = []
                for item in priority_items:
                    candidates.append({
                        'idea': item.idea,
                        'proposal': item,
                        'priority_score': item.priority_score,
                        'reason': f"High-priority proposal ({item.priority_score}% priority)",
                        'review_priority': item.priority_score
                    })
                
                return candidates
                
        except Exception as e:
            self.logger.error(f"Priority queue review failed: {e}")
            return []
    
    async def _process_candidate(self, candidate: Dict[str, Any], review_type: str) -> Dict[str, Any]:
        """Process a review candidate"""
        try:
            idea = candidate['idea']
            
            # Generate review assessment
            assessment = await self._generate_review_assessment(idea, candidate, review_type)
            
            if not assessment:
                return None
            
            # Determine next actions
            next_actions = await self._determine_next_actions(idea, assessment)
            
            # Execute recommended actions
            action_results = await self._execute_actions(idea, next_actions)
            
            return {
                'idea_id': idea.id,
                'idea_content': idea.content_raw[:100] + "...",
                'review_reason': candidate['reason'],
                'assessment': assessment,
                'next_actions': next_actions,
                'action_results': action_results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error processing candidate {candidate.get('idea', {}).get('id', 'unknown')}: {e}")
            return None
    
    async def _generate_review_assessment(self, idea: Any, candidate: Dict[str, Any], review_type: str) -> Dict[str, Any]:
        """Generate AI-powered assessment of idea's current potential"""
        try:
            context_info = candidate.get('context_factors', {})
            
            prompt = f"""
            Reassess this idea that has been dormant in the system:
            
            Original idea: "{idea.content_raw}"
            Created: {idea.created_at}
            Category: {idea.category}
            Original urgency: {idea.urgency_score}
            Original novelty: {idea.novelty_score}
            
            Review context:
            - Review type: {review_type}
            - Reason for review: {candidate['reason']}
            - Current context: {context_info}
            
            Provide assessment in JSON format:
            {{
                "current_relevance": "high/medium/low",
                "relevance_score": 0-100,
                "status_change": "improved/declined/stable",
                "new_opportunities": ["opportunity1", "opportunity2"],
                "blocking_factors": ["factor1", "factor2"],
                "recommended_action": "resurrect/archive/modify/investigate",
                "urgency_update": 0-100,
                "reason_for_change": "explanation",
                "next_steps": ["step1", "step2"]
            }}
            
            Consider how time, context, and external factors might have changed the idea's potential.
            """
            
            response = await self.ai_service.get_completion(
                prompt=prompt,
                model="claude-3-sonnet",
                max_tokens=600,
                temperature=0.6
            )
            
            if response:
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    pass
            
            # Fallback assessment
            return {
                "current_relevance": "medium",
                "relevance_score": 65,
                "status_change": "stable",
                "new_opportunities": ["Further investigation needed"],
                "blocking_factors": ["Needs more research"],
                "recommended_action": "investigate",
                "urgency_update": idea.urgency_score or 50,
                "reason_for_change": "Requires detailed review",
                "next_steps": ["Research current market", "Assess resources"]
            }
            
        except Exception as e:
            self.logger.error(f"Assessment generation failed: {e}")
            return None
    
    async def _determine_next_actions(self, idea: Any, assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Determine next actions based on assessment"""
        actions = []
        
        recommended_action = assessment.get('recommended_action', 'investigate')
        
        if recommended_action == 'resurrect':
            actions.append({
                'type': 'resurrect',
                'description': 'Reactivate idea for immediate development',
                'priority': 'high'
            })
            actions.append({
                'type': 'expand',
                'description': 'Generate fresh expansion with current context',
                'priority': 'medium'
            })
            
        elif recommended_action == 'modify':
            actions.append({
                'type': 'modify',
                'description': 'Update idea based on new opportunities',
                'priority': 'medium'
            })
            
        elif recommended_action == 'investigate':
            actions.append({
                'type': 'research',
                'description': 'Gather more information about current viability',
                'priority': 'low'
            })
            
        elif recommended_action == 'archive':
            actions.append({
                'type': 'archive',
                'description': 'Archive idea with updated status',
                'priority': 'low'
            })
        
        # Add urgency update if needed
        if assessment.get('urgency_update', 0) != idea.urgency_score:
            actions.append({
                'type': 'update_urgency',
                'description': f'Update urgency score to {assessment.get("urgency_update")}',
                'priority': 'low'
            })
        
        return actions
    
    async def _execute_actions(self, idea: Any, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute recommended actions"""
        results = []
        
        for action in actions:
            try:
                result = await self._execute_single_action(idea, action)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Action execution failed: {e}")
                results.append({
                    'action': action['type'],
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    async def _execute_single_action(self, idea: Any, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single action"""
        action_type = action['type']
        
        if action_type == 'resurrect':
            # Trigger full processing pipeline
            await self.send_message(
                recipient="classifier",
                action="reclassify",
                data={'idea_id': idea.id, 'reason': 'resurrection'}
            )
            
            return {
                'action': 'resurrect',
                'success': True,
                'message': 'Idea sent for reclassification and processing'
            }
            
        elif action_type == 'expand':
            # Trigger expansion with current context
            await self.send_message(
                recipient="expander",
                action="expand_existing",
                data={'idea_id': idea.id, 'context': 'review_resurrection'}
            )
            
            return {
                'action': 'expand',
                'success': True,
                'message': 'Idea sent for fresh expansion'
            }
            
        elif action_type == 'update_urgency':
            # Update urgency score
            with get_db() as db:
                IdeaCRUD.update_idea_urgency(db, idea.id, action.get('new_urgency', 50))
            
            return {
                'action': 'update_urgency',
                'success': True,
                'message': 'Urgency score updated'
            }
            
        elif action_type == 'archive':
            # Archive idea
            with get_db() as db:
                IdeaCRUD.archive_idea(db, idea.id)
            
            return {
                'action': 'archive',
                'success': True,
                'message': 'Idea archived'
            }
        
        return {
            'action': action_type,
            'success': False,
            'message': 'Action not implemented'
        }
    
    async def _analyze_current_context(self) -> Dict[str, Any]:
        """Analyze current context for relevance scoring"""
        now = datetime.now()
        
        return {
            'season': self._get_season(now),
            'time_of_day': now.hour,
            'day_of_week': now.weekday(),
            'month': now.month,
            'is_weekend': now.weekday() >= 5,
            'is_evening': 18 <= now.hour <= 22,
            'is_morning': 6 <= now.hour <= 12
        }
    
    def _get_season(self, date: datetime) -> str:
        """Get current season"""
        month = date.month
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        else:
            return 'autumn'
    
    async def _score_context_relevance(self, idea: Any, context: Dict[str, Any]) -> int:
        """Score how relevant an idea is to current context"""
        try:
            # Basic context scoring
            score = 50  # Base score
            
            # Time-based relevance
            if context.get('is_weekend') and idea.category == 'personal':
                score += 15
            if context.get('is_evening') and idea.category == 'creative':
                score += 10
            if context.get('is_morning') and idea.category == 'business':
                score += 10
            
            # Seasonal relevance
            season = context.get('season', 'spring')
            if season == 'spring' and 'new' in idea.content_raw.lower():
                score += 10
            if season == 'winter' and 'cozy' in idea.content_raw.lower():
                score += 10
            
            # Category-specific boosts
            if idea.category == 'metaphysical' and context.get('is_evening'):
                score += 5
            
            return min(100, score)
            
        except Exception as e:
            self.logger.error(f"Context relevance scoring failed: {e}")
            return 50
    
    async def _analyze_user_patterns(self, db) -> Dict[str, Any]:
        """Analyze user patterns from historical data"""
        try:
            # Get successful ideas/proposals
            successful_ideas = IdeaCRUD.get_successful_ideas(db, limit=20)
            
            patterns = {
                'preferred_categories': {},
                'successful_times': [],
                'common_themes': [],
                'typical_urgency': 50
            }
            
            for idea in successful_ideas:
                # Category patterns
                if idea.category:
                    patterns['preferred_categories'][idea.category] = patterns['preferred_categories'].get(idea.category, 0) + 1
                
                # Time patterns
                patterns['successful_times'].append(idea.created_at.hour)
                
                # Common themes (simplified)
                if idea.content_raw:
                    words = idea.content_raw.lower().split()
                    for word in words:
                        if len(word) > 4:  # Only longer words
                            patterns['common_themes'].append(word)
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Pattern analysis failed: {e}")
            return {}
    
    async def _score_pattern_match(self, idea: Any, patterns: Dict[str, Any]) -> int:
        """Score how well an idea matches user patterns"""
        try:
            score = 50  # Base score
            
            # Category match
            preferred_categories = patterns.get('preferred_categories', {})
            if idea.category and idea.category in preferred_categories:
                score += min(20, preferred_categories[idea.category] * 2)
            
            # Theme match
            common_themes = patterns.get('common_themes', [])
            if idea.content_raw:
                words = idea.content_raw.lower().split()
                theme_matches = sum(1 for word in words if word in common_themes)
                score += min(15, theme_matches * 3)
            
            # Time pattern (simplified)
            successful_times = patterns.get('successful_times', [])
            if successful_times:
                avg_time = sum(successful_times) / len(successful_times)
                current_time = datetime.now().hour
                time_diff = abs(current_time - avg_time)
                if time_diff < 3:  # Within 3 hours
                    score += 10
            
            return min(100, score)
            
        except Exception as e:
            self.logger.error(f"Pattern matching failed: {e}")
            return 50
    
    def _calculate_next_review(self, review_type: str) -> str:
        """Calculate next review time"""
        now = datetime.now()
        
        if review_type == 'daily':
            next_review = now + timedelta(days=1)
        elif review_type == 'weekly':
            next_review = now + timedelta(weeks=1)
        elif review_type == 'monthly':
            next_review = now + timedelta(days=30)
        elif review_type == 'quarterly':
            next_review = now + timedelta(days=90)
        else:
            next_review = now + timedelta(days=1)
        
        return next_review.isoformat()
    
    async def _update_review_metrics(self, review_type: str, review_count: int):
        """Update system metrics for review activity"""
        try:
            with get_db() as db:
                SystemMetricsCRUD.create_metric(
                    db=db,
                    metric_name=f"review_{review_type}",
                    metric_value=review_count,
                    metric_type="counter",
                    labels=json.dumps({
                        "review_type": review_type,
                        "timestamp": datetime.now().isoformat()
                    })
                )
        except Exception as e:
            self.logger.error(f"Failed to update review metrics: {e}")
    
    async def schedule_review(self, review_type: str = 'daily', delay_hours: int = 0) -> Dict[str, Any]:
        """Schedule a future review"""
        try:
            # In a real implementation, this would use a task scheduler
            # For now, we'll just log the scheduled review
            
            review_time = datetime.now() + timedelta(hours=delay_hours)
            
            self.logger.info(f"Scheduled {review_type} review for {review_time}")
            
            return {
                'success': True,
                'review_type': review_type,
                'scheduled_for': review_time.isoformat(),
                'message': f"{review_type} review scheduled"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to schedule review: {e}")
            return {'error': f'Review scheduling failed: {str(e)}'}
    
    async def get_review_insights(self) -> Dict[str, Any]:
        """Get insights about review patterns and effectiveness"""
        try:
            with get_db() as db:
                # Get review metrics
                metrics = SystemMetricsCRUD.get_metrics_by_pattern(db, "review_%")
                
                # Analyze review effectiveness
                total_reviews = sum(metric.metric_value for metric in metrics)
                
                insights = {
                    'total_reviews_conducted': total_reviews,
                    'review_frequency': len(metrics),
                    'most_active_review_type': 'daily',  # Simplified
                    'resurrection_success_rate': 0.75,  # Mock data
                    'recommendations': [
                        "Continue daily reviews for best results",
                        "Serendipity reviews generate unexpected insights",
                        "Context-based reviews are most effective in evenings"
                    ]
                }
                
                return insights
                
        except Exception as e:
            self.logger.error(f"Failed to get review insights: {e}")
            return {'error': f'Insights generation failed: {str(e)}'}