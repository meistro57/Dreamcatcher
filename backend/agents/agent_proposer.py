import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid

from .base_agent import BaseAgent
from ..database import get_db, IdeaCRUD, ProposalCRUD
from ..services import AIService

class AgentProposer(BaseAgent):
    """
    Agent responsible for generating structured project proposals from expanded ideas.
    Creates actionable plans with timelines, resources, and success metrics.
    """
    
    def __init__(self):
        super().__init__(
            agent_id="proposer",
            name="Proposal Agent",
            description="Proposal generated. Here's a structured plan with bullet points, deadlines, and passive income streams.",
            version="1.0.0"
        )
        
        # Initialize AI service
        self.ai_service = AIService()
        
        # Proposal templates by category
        self.proposal_templates = {
            'creative': {
                'sections': ['concept', 'artistic_vision', 'execution_plan', 'resources', 'timeline', 'monetization'],
                'focus': 'artistic merit, creative expression, audience engagement'
            },
            'business': {
                'sections': ['executive_summary', 'market_analysis', 'business_model', 'implementation', 'financials', 'risk_analysis'],
                'focus': 'market opportunity, revenue potential, competitive advantage'
            },
            'technical': {
                'sections': ['technical_overview', 'architecture', 'development_phases', 'testing_strategy', 'deployment', 'maintenance'],
                'focus': 'technical feasibility, scalability, maintainability'
            },
            'personal': {
                'sections': ['goals', 'benefits', 'action_steps', 'habits', 'tracking', 'support_system'],
                'focus': 'personal growth, sustainable habits, measurable outcomes'
            },
            'metaphysical': {
                'sections': ['spiritual_foundation', 'practices', 'integration', 'community', 'growth_path', 'wisdom_sharing'],
                'focus': 'spiritual development, consciousness expansion, authentic expression'
            }
        }
        
        # Viability criteria
        self.viability_criteria = {
            'feasibility': 'Technical and practical possibility',
            'market_demand': 'Evidence of need or interest',
            'resource_requirements': 'Realistic resource availability',
            'timeline': 'Achievable timeframe',
            'uniqueness': 'Competitive differentiation',
            'scalability': 'Growth potential',
            'sustainability': 'Long-term viability',
            'alignment': 'Fit with personal/business goals'
        }
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process proposal generation request"""
        idea_id = data.get('idea_id')
        original_content = data.get('original_content', '')
        expanded_content = data.get('expanded_content', '')
        
        if not idea_id:
            return {'error': 'Missing idea_id'}
        
        try:
            # Get idea from database
            with get_db() as db:
                idea = IdeaCRUD.get_idea(db, idea_id)
                if not idea:
                    return {'error': f'Idea {idea_id} not found'}
                
                # Analyze viability first
                viability_analysis = await self._analyze_viability(
                    original_content, 
                    expanded_content, 
                    idea.category
                )
                
                if not viability_analysis:
                    return {'error': 'Failed to analyze viability'}
                
                # Check if idea meets minimum viability threshold
                viability_score = viability_analysis.get('overall_score', 0)
                if viability_score < 60:  # Configurable threshold
                    # Still create proposal but mark as low viability
                    proposal_status = 'low_viability'
                else:
                    proposal_status = 'pending'
                
                # Generate structured proposal
                proposal_content = await self._generate_proposal(
                    original_content,
                    expanded_content,
                    idea.category,
                    viability_analysis
                )
                
                if not proposal_content:
                    return {'error': 'Failed to generate proposal'}
                
                # Generate timeline
                timeline = await self._generate_timeline(
                    proposal_content,
                    idea.category
                )
                
                # Generate resource requirements
                resources = await self._generate_resources(
                    proposal_content,
                    idea.category
                )
                
                # Generate success metrics
                success_metrics = await self._generate_success_metrics(
                    proposal_content,
                    idea.category
                )
                
                # Create proposal in database
                proposal = ProposalCRUD.create_proposal(
                    db=db,
                    idea_id=idea_id,
                    title=f"Proposal for: {original_content[:100]}...",
                    content=proposal_content,
                    viability_analysis=json.dumps(viability_analysis),
                    timeline=json.dumps(timeline),
                    resource_requirements=json.dumps(resources),
                    success_metrics=json.dumps(success_metrics),
                    estimated_effort=viability_analysis.get('estimated_effort', 'medium'),
                    priority_score=viability_analysis.get('priority_score', 50),
                    status=proposal_status,
                    agent_version=self.version
                )
                
                # Trigger review if high viability
                if viability_score >= 80:
                    await self._trigger_high_priority_review(idea_id, proposal.id)
                
                return {
                    'success': True,
                    'idea_id': idea_id,
                    'proposal_id': proposal.id,
                    'viability_score': viability_score,
                    'status': proposal_status,
                    'summary': {
                        'title': proposal.title,
                        'effort': proposal.estimated_effort,
                        'priority': proposal.priority_score,
                        'next_steps': timeline.get('immediate_actions', [])
                    },
                    'message': f"Generated proposal with {viability_score}% viability score"
                }
                
        except Exception as e:
            self.logger.error(f"Error generating proposal for idea {idea_id}: {e}")
            return {'error': f'Proposal generation failed: {str(e)}'}
    
    async def _analyze_viability(self, original: str, expanded: str, category: str) -> Dict[str, Any]:
        """Analyze idea viability using AI"""
        try:
            criteria_list = '\n'.join([f"- {k}: {v}" for k, v in self.viability_criteria.items()])
            
            prompt = f"""
            Analyze the viability of this {category} idea:
            
            Original: "{original}"
            Expanded: "{expanded}"
            
            Evaluate each criterion (1-10 scale):
            {criteria_list}
            
            Provide your analysis in this JSON format:
            {{
                "feasibility": {{"score": X, "reasoning": "explanation"}},
                "market_demand": {{"score": X, "reasoning": "explanation"}},
                "resource_requirements": {{"score": X, "reasoning": "explanation"}},
                "timeline": {{"score": X, "reasoning": "explanation"}},
                "uniqueness": {{"score": X, "reasoning": "explanation"}},
                "scalability": {{"score": X, "reasoning": "explanation"}},
                "sustainability": {{"score": X, "reasoning": "explanation"}},
                "alignment": {{"score": X, "reasoning": "explanation"}},
                "overall_score": X,
                "estimated_effort": "low/medium/high",
                "priority_score": X,
                "key_challenges": ["challenge1", "challenge2"],
                "success_factors": ["factor1", "factor2"],
                "recommendation": "proceed/modify/defer/abandon"
            }}
            
            Be realistic but constructive in your analysis.
            """
            
            response = await self.ai_service.get_completion(
                prompt=prompt,
                model="claude-3-sonnet",
                max_tokens=1000,
                temperature=0.3
            )
            
            if response:
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    return self._create_fallback_viability(original, expanded)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Viability analysis failed: {e}")
            return None
    
    def _create_fallback_viability(self, original: str, expanded: str) -> Dict[str, Any]:
        """Create fallback viability analysis"""
        return {
            "feasibility": {"score": 7, "reasoning": "Appears technically feasible"},
            "market_demand": {"score": 6, "reasoning": "Potential market interest"},
            "resource_requirements": {"score": 5, "reasoning": "Moderate resources needed"},
            "timeline": {"score": 6, "reasoning": "Reasonable timeframe"},
            "uniqueness": {"score": 7, "reasoning": "Novel approach"},
            "scalability": {"score": 5, "reasoning": "Some scaling potential"},
            "sustainability": {"score": 6, "reasoning": "Moderate sustainability"},
            "alignment": {"score": 8, "reasoning": "Aligns with goals"},
            "overall_score": 63,
            "estimated_effort": "medium",
            "priority_score": 65,
            "key_challenges": ["Resource allocation", "Market validation"],
            "success_factors": ["Strong execution", "User feedback"],
            "recommendation": "proceed"
        }
    
    async def _generate_proposal(self, original: str, expanded: str, category: str, viability: Dict[str, Any]) -> str:
        """Generate structured proposal content"""
        try:
            template = self.proposal_templates.get(category, self.proposal_templates['creative'])
            
            prompt = f"""
            Create a detailed project proposal for this {category} idea:
            
            Original: "{original}"
            Expanded: "{expanded}"
            
            Viability Score: {viability.get('overall_score', 'N/A')}
            Key Challenges: {viability.get('key_challenges', [])}
            Success Factors: {viability.get('success_factors', [])}
            
            Structure the proposal with these sections:
            {', '.join(template['sections'])}
            
            Focus on: {template['focus']}
            
            Make it comprehensive yet actionable. Include:
            - Clear objectives and deliverables
            - Specific action items
            - Risk mitigation strategies
            - Success criteria
            - Monetization/value creation opportunities
            
            Write in a professional but engaging tone.
            """
            
            response = await self.ai_service.get_completion(
                prompt=prompt,
                model="claude-3-sonnet",
                max_tokens=1200,
                temperature=0.6
            )
            
            return response or ""
            
        except Exception as e:
            self.logger.error(f"Proposal generation failed: {e}")
            return ""
    
    async def _generate_timeline(self, proposal: str, category: str) -> Dict[str, Any]:
        """Generate project timeline"""
        try:
            prompt = f"""
            Based on this proposal, create a realistic timeline:
            
            "{proposal}"
            
            Provide a JSON timeline with:
            {{
                "immediate_actions": ["action1", "action2"],
                "week_1": ["task1", "task2"],
                "month_1": ["milestone1", "milestone2"],
                "quarter_1": ["deliverable1", "deliverable2"],
                "long_term": ["goal1", "goal2"],
                "total_duration": "X weeks/months",
                "key_milestones": [
                    {{"milestone": "name", "date": "relative_date", "description": "details"}}
                ]
            }}
            
            Be realistic about timeframes for {category} projects.
            """
            
            response = await self.ai_service.get_completion(
                prompt=prompt,
                model="gpt-4",
                max_tokens=600,
                temperature=0.4
            )
            
            if response:
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    pass
            
            # Fallback timeline
            return {
                "immediate_actions": ["Research and planning", "Resource assessment"],
                "week_1": ["Initial setup", "Requirements gathering"],
                "month_1": ["First prototype", "User feedback"],
                "quarter_1": ["MVP completion", "Initial testing"],
                "long_term": ["Scale and optimize", "Market expansion"],
                "total_duration": "3-6 months",
                "key_milestones": [
                    {"milestone": "Project Start", "date": "Week 1", "description": "Kick off and planning"},
                    {"milestone": "First Prototype", "date": "Month 1", "description": "Working prototype"},
                    {"milestone": "MVP Launch", "date": "Quarter 1", "description": "Minimum viable product"}
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Timeline generation failed: {e}")
            return {}
    
    async def _generate_resources(self, proposal: str, category: str) -> Dict[str, Any]:
        """Generate resource requirements"""
        try:
            prompt = f"""
            Based on this proposal, identify resource requirements:
            
            "{proposal}"
            
            Provide JSON with:
            {{
                "human_resources": ["skill1", "skill2"],
                "technology": ["tool1", "tool2"],
                "financial": {{"budget_estimate": "range", "key_costs": ["cost1", "cost2"]}},
                "time_investment": "hours per week",
                "external_dependencies": ["dependency1", "dependency2"],
                "learning_requirements": ["skill_to_learn1", "skill_to_learn2"]
            }}
            
            Be specific and realistic for {category} projects.
            """
            
            response = await self.ai_service.get_completion(
                prompt=prompt,
                model="gpt-4",
                max_tokens=500,
                temperature=0.4
            )
            
            if response:
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    pass
            
            # Fallback resources
            return {
                "human_resources": ["Project management", "Technical skills"],
                "technology": ["Development tools", "Testing environment"],
                "financial": {"budget_estimate": "$1,000-$5,000", "key_costs": ["Software licenses", "Hosting"]},
                "time_investment": "10-20 hours per week",
                "external_dependencies": ["Third-party APIs", "User feedback"],
                "learning_requirements": ["New frameworks", "Best practices"]
            }
            
        except Exception as e:
            self.logger.error(f"Resource generation failed: {e}")
            return {}
    
    async def _generate_success_metrics(self, proposal: str, category: str) -> Dict[str, Any]:
        """Generate success metrics"""
        try:
            prompt = f"""
            Define success metrics for this {category} project:
            
            "{proposal}"
            
            Provide JSON with:
            {{
                "primary_metrics": ["metric1", "metric2"],
                "secondary_metrics": ["metric3", "metric4"],
                "milestones": [
                    {{"name": "milestone1", "target": "value", "timeframe": "when"}}
                ],
                "kpis": [
                    {{"name": "kpi1", "target": "value", "measurement": "how"}}
                ],
                "success_criteria": "definition of success",
                "failure_indicators": ["warning1", "warning2"]
            }}
            
            Make metrics specific and measurable.
            """
            
            response = await self.ai_service.get_completion(
                prompt=prompt,
                model="claude-3-sonnet",
                max_tokens=400,
                temperature=0.4
            )
            
            if response:
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    pass
            
            # Fallback metrics
            return {
                "primary_metrics": ["User engagement", "Goal achievement"],
                "secondary_metrics": ["User satisfaction", "Time efficiency"],
                "milestones": [
                    {"name": "First milestone", "target": "50% completion", "timeframe": "Month 1"}
                ],
                "kpis": [
                    {"name": "Progress rate", "target": "Weekly goals met", "measurement": "Task completion"}
                ],
                "success_criteria": "Project objectives achieved within timeline and budget",
                "failure_indicators": ["Missing deadlines", "Budget overruns"]
            }
            
        except Exception as e:
            self.logger.error(f"Success metrics generation failed: {e}")
            return {}
    
    async def _trigger_high_priority_review(self, idea_id: str, proposal_id: str):
        """Trigger immediate review for high-priority proposals"""
        try:
            await self.send_message(
                recipient="reviewer",
                action="priority_review",
                data={
                    'idea_id': idea_id,
                    'proposal_id': proposal_id,
                    'priority': 'high'
                }
            )
            
            self.logger.info(f"Triggered high priority review for proposal {proposal_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to trigger priority review: {e}")
    
    async def regenerate_proposal(self, idea_id: str, focus_area: str = None) -> Dict[str, Any]:
        """Regenerate proposal with different focus"""
        try:
            with get_db() as db:
                idea = IdeaCRUD.get_idea(db, idea_id)
                if not idea:
                    return {'error': f'Idea {idea_id} not found'}
                
                # Get expanded content if available
                expanded_content = ""
                if hasattr(idea, 'expansions') and idea.expansions:
                    expanded_content = idea.expansions[0].expanded_content
                
                # Re-analyze with focus
                viability_analysis = await self._analyze_viability(
                    idea.content_transcribed or idea.content_raw,
                    expanded_content,
                    idea.category
                )
                
                if not viability_analysis:
                    return {'error': 'Failed to analyze viability'}
                
                # Generate new proposal
                if focus_area:
                    # Modify category temporarily for focused generation
                    original_category = idea.category
                    focused_category = focus_area
                else:
                    focused_category = idea.category
                
                proposal_content = await self._generate_proposal(
                    idea.content_transcribed or idea.content_raw,
                    expanded_content,
                    focused_category,
                    viability_analysis
                )
                
                if proposal_content:
                    # Create new proposal
                    proposal = ProposalCRUD.create_proposal(
                        db=db,
                        idea_id=idea_id,
                        title=f"Revised Proposal: {idea.content_raw[:100]}...",
                        content=proposal_content,
                        viability_analysis=json.dumps(viability_analysis),
                        timeline=json.dumps(await self._generate_timeline(proposal_content, focused_category)),
                        resource_requirements=json.dumps(await self._generate_resources(proposal_content, focused_category)),
                        success_metrics=json.dumps(await self._generate_success_metrics(proposal_content, focused_category)),
                        estimated_effort=viability_analysis.get('estimated_effort', 'medium'),
                        priority_score=viability_analysis.get('priority_score', 50),
                        status='pending',
                        agent_version=self.version
                    )
                    
                    return {
                        'success': True,
                        'idea_id': idea_id,
                        'proposal_id': proposal.id,
                        'focus_area': focus_area,
                        'viability_score': viability_analysis.get('overall_score', 0)
                    }
                else:
                    return {'error': 'Failed to generate revised proposal'}
                    
        except Exception as e:
            self.logger.error(f"Error regenerating proposal for idea {idea_id}: {e}")
            return {'error': f'Proposal regeneration failed: {str(e)}'}
    
    async def get_proposal_suggestions(self, idea_id: str) -> List[Dict[str, Any]]:
        """Get suggestions for proposal improvements"""
        try:
            with get_db() as db:
                idea = IdeaCRUD.get_idea(db, idea_id)
                if not idea:
                    return []
                
                # Get existing proposal if any
                existing_proposal = None
                if hasattr(idea, 'proposals') and idea.proposals:
                    existing_proposal = idea.proposals[0]
                
                suggestions = []
                
                # Category-based suggestions
                for category in self.proposal_templates.keys():
                    if category != idea.category:
                        template = self.proposal_templates[category]
                        suggestions.append({
                            'type': 'category_focus',
                            'category': category,
                            'description': f"Approach from {category} perspective",
                            'focus': template['focus'],
                            'sections': template['sections']
                        })
                
                # Improvement suggestions based on viability
                if existing_proposal:
                    try:
                        viability = json.loads(existing_proposal.viability_analysis)
                        overall_score = viability.get('overall_score', 0)
                        
                        if overall_score < 70:
                            suggestions.append({
                                'type': 'viability_improvement',
                                'description': 'Focus on addressing key challenges',
                                'recommendations': viability.get('key_challenges', [])
                            })
                        
                        if overall_score > 85:
                            suggestions.append({
                                'type': 'expansion',
                                'description': 'Explore scaling and advanced features',
                                'recommendations': ['Market expansion', 'Feature enhancement', 'Platform integration']
                            })
                            
                    except json.JSONDecodeError:
                        pass
                
                return suggestions
                
        except Exception as e:
            self.logger.error(f"Error getting proposal suggestions: {e}")
            return []