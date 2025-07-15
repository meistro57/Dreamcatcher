import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base_agent import BaseAgent
from ..database import get_db, IdeaCRUD, ExpansionCRUD
from ..services import AIService

class AgentExpander(BaseAgent):
    """
    Agent responsible for expanding ideas with AI assistance.
    Takes raw concepts and turns them into detailed explorations.
    """
    
    def __init__(self):
        super().__init__(
            agent_id="expander",
            name="Expansion Agent",
            description="Let me take that spark and turn it into a full flame.",
            version="1.0.0"
        )
        
        # Initialize AI service
        self.ai_service = AIService()
        
        # Expansion modes
        self.expansion_modes = {
            'creative': self._expand_creative,
            'business': self._expand_business,
            'technical': self._expand_technical,
            'personal': self._expand_personal,
            'metaphysical': self._expand_metaphysical
        }
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process idea expansion request"""
        idea_id = data.get('idea_id')
        content = data.get('content', '')
        classification = data.get('classification', {})
        
        if not idea_id or not content:
            return {'error': 'Missing idea_id or content'}
        
        try:
            # Get idea from database
            with get_db() as db:
                idea = IdeaCRUD.get_idea(db, idea_id)
                if not idea:
                    return {'error': f'Idea {idea_id} not found'}
                
                # Determine expansion approach
                category = classification.get('category', idea.category or 'utility')
                expansion_mode = self.expansion_modes.get(category, self._expand_general)
                
                # Generate multiple expansions
                expansions = []
                
                # Primary expansion using Claude
                claude_expansion = await self._expand_with_claude(content, category, classification)
                if claude_expansion:
                    expansions.append({
                        'content': claude_expansion,
                        'type': 'claude',
                        'mode': category
                    })
                
                # Alternative expansion using GPT
                gpt_expansion = await self._expand_with_gpt(content, category, classification)
                if gpt_expansion:
                    expansions.append({
                        'content': gpt_expansion,
                        'type': 'gpt',
                        'mode': category
                    })
                
                # Specialized expansion based on category
                specialized_expansion = await expansion_mode(content, classification)
                if specialized_expansion:
                    expansions.append({
                        'content': specialized_expansion,
                        'type': 'specialized',
                        'mode': category
                    })
                
                # Store expansions in database
                saved_expansions = []
                for expansion in expansions:
                    saved_expansion = ExpansionCRUD.create_expansion(
                        db=db,
                        idea_id=idea_id,
                        content=expansion['content'],
                        expansion_type=expansion['type'],
                        prompt_used=f"Mode: {expansion['mode']}, Type: {expansion['type']}",
                        agent_version=self.version
                    )
                    saved_expansions.append(saved_expansion)
                
                # Trigger next stage if expansions are substantial
                if len(saved_expansions) > 0:
                    await self._trigger_visualization(idea_id, content, expansions[0]['content'])
                
                return {
                    'success': True,
                    'idea_id': idea_id,
                    'expansions_count': len(saved_expansions),
                    'expansions': [exp.expanded_content for exp in saved_expansions],
                    'message': f"Generated {len(saved_expansions)} expansions for idea"
                }
                
        except Exception as e:
            self.logger.error(f"Error expanding idea {idea_id}: {e}")
            return {'error': f'Expansion failed: {str(e)}'}
    
    async def _expand_with_claude(self, content: str, category: str, classification: Dict[str, Any]) -> str:
        """Expand idea using Claude with category-specific prompting"""
        try:
            urgency = classification.get('urgency_score', 50)
            novelty = classification.get('novelty_score', 50)
            
            prompt = f"""
            Expand this {category} idea with depth and creativity:
            
            Original idea: "{content}"
            
            Context:
            - Urgency level: {urgency}/100
            - Novelty level: {novelty}/100
            - Category: {category}
            
            Please provide:
            1. A detailed exploration of the concept
            2. Three specific applications or use cases
            3. Potential challenges and solutions
            4. Next steps for development
            5. Why this idea matters
            
            Write in an engaging, visionary style that captures the excitement of the original idea while adding substantive depth.
            """
            
            response = await self.ai_service.get_completion(
                prompt=prompt,
                model="claude-3-sonnet",
                max_tokens=1000,
                temperature=0.8
            )
            
            return response or ""
            
        except Exception as e:
            self.logger.error(f"Claude expansion failed: {e}")
            return ""
    
    async def _expand_with_gpt(self, content: str, category: str, classification: Dict[str, Any]) -> str:
        """Expand idea using GPT with structured approach"""
        try:
            prompt = f"""
            Provide a structured expansion for this {category} idea:
            
            Idea: "{content}"
            
            Structure your response as:
            
            **Core Concept:**
            [Brief refinement of the core idea]
            
            **Implementation Approach:**
            [Step-by-step approach to building this]
            
            **Key Features:**
            [3-5 essential features or components]
            
            **Target Audience:**
            [Who would benefit from this]
            
            **Success Metrics:**
            [How to measure success]
            
            **Potential Obstacles:**
            [Challenges and mitigation strategies]
            
            Keep it practical and actionable while maintaining the creative spark.
            """
            
            response = await self.ai_service.get_completion(
                prompt=prompt,
                model="gpt-4",
                max_tokens=800,
                temperature=0.7
            )
            
            return response or ""
            
        except Exception as e:
            self.logger.error(f"GPT expansion failed: {e}")
            return ""
    
    async def _expand_creative(self, content: str, classification: Dict[str, Any]) -> str:
        """Expand creative ideas with artistic and innovative focus"""
        try:
            prompt = f"""
            Expand this creative idea with artistic vision:
            
            "{content}"
            
            Explore:
            - Artistic mediums and techniques
            - Emotional impact and storytelling
            - Visual or auditory elements
            - Cultural or personal significance
            - Collaborative possibilities
            - Exhibition or sharing opportunities
            
            Think like a visionary artist and curator combined.
            """
            
            response = await self.ai_service.get_completion(
                prompt=prompt,
                max_tokens=600,
                temperature=0.9
            )
            
            return response or ""
            
        except Exception as e:
            self.logger.error(f"Creative expansion failed: {e}")
            return ""
    
    async def _expand_business(self, content: str, classification: Dict[str, Any]) -> str:
        """Expand business ideas with commercial and strategic focus"""
        try:
            prompt = f"""
            Analyze this business idea from an entrepreneurial perspective:
            
            "{content}"
            
            Provide:
            - Market opportunity and target customers
            - Revenue model and pricing strategy
            - Competitive landscape analysis
            - Required resources and timeline
            - Growth and scaling potential
            - Risk factors and mitigation
            
            Think like a startup founder and investor combined.
            """
            
            response = await self.ai_service.get_completion(
                prompt=prompt,
                max_tokens=700,
                temperature=0.6
            )
            
            return response or ""
            
        except Exception as e:
            self.logger.error(f"Business expansion failed: {e}")
            return ""
    
    async def _expand_technical(self, content: str, classification: Dict[str, Any]) -> str:
        """Expand technical ideas with implementation focus"""
        try:
            prompt = f"""
            Expand this technical idea with implementation details:
            
            "{content}"
            
            Cover:
            - Technical architecture and components
            - Technology stack recommendations
            - Development phases and milestones
            - Performance and scalability considerations
            - Integration points and APIs
            - Testing and deployment strategy
            
            Think like a senior software architect.
            """
            
            response = await self.ai_service.get_completion(
                prompt=prompt,
                max_tokens=700,
                temperature=0.5
            )
            
            return response or ""
            
        except Exception as e:
            self.logger.error(f"Technical expansion failed: {e}")
            return ""
    
    async def _expand_personal(self, content: str, classification: Dict[str, Any]) -> str:
        """Expand personal development ideas with growth focus"""
        try:
            prompt = f"""
            Expand this personal development idea:
            
            "{content}"
            
            Explore:
            - Personal growth benefits
            - Habit formation and routines
            - Measurement and tracking methods
            - Potential obstacles and solutions
            - Community and support systems
            - Long-term life impact
            
            Think like a life coach and behavioral psychologist.
            """
            
            response = await self.ai_service.get_completion(
                prompt=prompt,
                max_tokens=600,
                temperature=0.7
            )
            
            return response or ""
            
        except Exception as e:
            self.logger.error(f"Personal expansion failed: {e}")
            return ""
    
    async def _expand_metaphysical(self, content: str, classification: Dict[str, Any]) -> str:
        """Expand metaphysical ideas with spiritual and consciousness focus"""
        try:
            prompt = f"""
            Expand this metaphysical/spiritual idea:
            
            "{content}"
            
            Explore:
            - Consciousness and awareness aspects
            - Spiritual practices and integration
            - Symbolic and archetypal meanings
            - Connection to ancient wisdom
            - Modern applications and relevance
            - Experiential and transformative potential
            
            Think like a mystic and consciousness researcher.
            """
            
            response = await self.ai_service.get_completion(
                prompt=prompt,
                max_tokens=600,
                temperature=0.8
            )
            
            return response or ""
            
        except Exception as e:
            self.logger.error(f"Metaphysical expansion failed: {e}")
            return ""
    
    async def _expand_general(self, content: str, classification: Dict[str, Any]) -> str:
        """General expansion for uncategorized ideas"""
        try:
            prompt = f"""
            Expand and explore this idea from multiple angles:
            
            "{content}"
            
            Consider:
            - Different interpretations and applications
            - Cross-disciplinary connections
            - Practical implementation possibilities
            - Creative variations and extensions
            - Potential impact and significance
            - Questions to explore further
            
            Be thorough and imaginative.
            """
            
            response = await self.ai_service.get_completion(
                prompt=prompt,
                max_tokens=700,
                temperature=0.8
            )
            
            return response or ""
            
        except Exception as e:
            self.logger.error(f"General expansion failed: {e}")
            return ""
    
    async def _trigger_visualization(self, idea_id: str, original_content: str, expanded_content: str):
        """Trigger visual generation for expanded ideas"""
        try:
            await self.send_message(
                recipient="visualizer",
                action="generate_visual",
                data={
                    'idea_id': idea_id,
                    'original_content': original_content,
                    'expanded_content': expanded_content
                }
            )
            
            self.logger.info(f"Triggered visualization for idea {idea_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to trigger visualization: {e}")
    
    async def expand_existing_idea(self, idea_id: str, expansion_type: str = 'general') -> Dict[str, Any]:
        """Expand an existing idea with a specific approach"""
        try:
            with get_db() as db:
                idea = IdeaCRUD.get_idea(db, idea_id)
                if not idea:
                    return {'error': f'Idea {idea_id} not found'}
                
                content = idea.content_transcribed or idea.content_raw
                classification = {
                    'category': idea.category,
                    'urgency_score': idea.urgency_score,
                    'novelty_score': idea.novelty_score
                }
                
                # Get expansion function
                expansion_func = self.expansion_modes.get(expansion_type, self._expand_general)
                
                # Generate expansion
                expansion = await expansion_func(content, classification)
                
                if expansion:
                    # Save expansion
                    saved_expansion = ExpansionCRUD.create_expansion(
                        db=db,
                        idea_id=idea_id,
                        content=expansion,
                        expansion_type=expansion_type,
                        prompt_used=f"Manual expansion: {expansion_type}",
                        agent_version=self.version
                    )
                    
                    return {
                        'success': True,
                        'idea_id': idea_id,
                        'expansion_id': saved_expansion.id,
                        'expansion': expansion,
                        'type': expansion_type
                    }
                else:
                    return {'error': f'Failed to generate {expansion_type} expansion'}
                    
        except Exception as e:
            self.logger.error(f"Error expanding existing idea {idea_id}: {e}")
            return {'error': f'Expansion failed: {str(e)}'}
    
    async def get_expansion_suggestions(self, idea_id: str) -> List[str]:
        """Get suggestions for how to expand an idea"""
        try:
            with get_db() as db:
                idea = IdeaCRUD.get_idea(db, idea_id)
                if not idea:
                    return []
                
                content = idea.content_transcribed or idea.content_raw
                
                # Generate expansion suggestions
                prompt = f"""
                Suggest 5 different ways to expand this idea:
                
                "{content}"
                
                Provide brief descriptions of different expansion approaches:
                1. [approach name]: [brief description]
                2. [approach name]: [brief description]
                ...
                
                Focus on diverse perspectives and methodologies.
                """
                
                response = await self.ai_service.get_completion(
                    prompt=prompt,
                    max_tokens=300,
                    temperature=0.7
                )
                
                if response:
                    # Parse suggestions from response
                    suggestions = []
                    lines = response.split('\n')
                    for line in lines:
                        if line.strip() and (line.strip().startswith(tuple('12345'))):
                            suggestions.append(line.strip())
                    
                    return suggestions
                
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting expansion suggestions: {e}")
            return []