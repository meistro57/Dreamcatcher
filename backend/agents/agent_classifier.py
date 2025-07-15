import asyncio
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from .base_agent import BaseAgent
from ..database import get_db, IdeaCRUD, TagCRUD
from ..services.ai_service import AIService

class AgentClassifier(BaseAgent):
    """
    Agent responsible for analyzing and classifying captured ideas.
    Tags, categorizes, and scores ideas for further processing.
    """
    
    def __init__(self):
        super().__init__(
            agent_id="classifier",
            name="Analysis Agent",
            description="I'm not saying this is another ADHD thought spiral, but... yeah it is. Categorized under 'You Might Actually Build This.'",
            version="1.0.0"
        )
        
        # Initialize AI service
        self.ai_service = AIService()
        
        # Classification categories
        self.categories = {
            'creative': ['art', 'design', 'story', 'music', 'creative', 'visual'],
            'business': ['business', 'startup', 'money', 'revenue', 'product', 'market'],
            'personal': ['personal', 'habit', 'routine', 'self', 'improvement'],
            'metaphysical': ['spiritual', 'consciousness', 'awakening', 'meditation', 'energy'],
            'utility': ['app', 'tool', 'utility', 'helper', 'automation', 'system']
        }
        
        # Urgency keywords
        self.urgency_indicators = {
            'high': ['urgent', 'asap', 'critical', 'important', 'emergency'],
            'medium': ['soon', 'needed', 'should', 'priority'],
            'excitement': ['amazing', 'brilliant', 'genius', 'perfect', 'incredible', 'holy shit', 'this is it']
        }
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process idea classification request"""
        idea_id = data.get('idea_id')
        content = data.get('content', '')
        
        if not idea_id or not content:
            return {'error': 'Missing idea_id or content'}
        
        try:
            # Get idea from database
            with get_db() as db:
                idea = IdeaCRUD.get_idea(db, idea_id)
                if not idea:
                    return {'error': f'Idea {idea_id} not found'}
                
                # Perform classification
                classification_result = await self._classify_idea(content)
                
                # Update idea with classification results
                IdeaCRUD.update_idea(
                    db=db,
                    idea_id=idea_id,
                    category=classification_result['category'],
                    urgency_score=classification_result['urgency_score'],
                    novelty_score=classification_result['novelty_score'],
                    processing_status='completed'
                )
                
                # Add tags
                await self._add_tags(db, idea_id, classification_result['tags'])
                
                # Trigger next stage if worthy
                if classification_result['should_expand']:
                    await self._trigger_expansion(idea_id, content, classification_result)
                
                return {
                    'success': True,
                    'idea_id': idea_id,
                    'classification': classification_result,
                    'message': f"Idea classified as {classification_result['category']} with {classification_result['urgency_score']:.1f} urgency"
                }
                
        except Exception as e:
            self.logger.error(f"Error classifying idea {idea_id}: {e}")
            return {'error': f'Classification failed: {str(e)}'}
    
    async def _classify_idea(self, content: str) -> Dict[str, Any]:
        """Classify idea using AI and rule-based analysis"""
        try:
            # Basic rule-based classification
            basic_classification = self._rule_based_classification(content)
            
            # Enhanced AI classification if available
            ai_classification = await self._ai_classification(content)
            
            # Combine results
            result = {
                'category': ai_classification.get('category', basic_classification['category']),
                'urgency_score': max(basic_classification['urgency_score'], ai_classification.get('urgency_score', 0)),
                'novelty_score': ai_classification.get('novelty_score', basic_classification['novelty_score']),
                'tags': list(set(basic_classification['tags'] + ai_classification.get('tags', []))),
                'reasoning': ai_classification.get('reasoning', 'Rule-based classification'),
                'should_expand': False
            }
            
            # Determine if idea should be expanded
            result['should_expand'] = (
                result['urgency_score'] > 60 or 
                result['novelty_score'] > 70 or 
                'urgent' in result['tags']
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Classification failed: {e}")
            # Fallback to basic classification
            return self._rule_based_classification(content)
    
    def _rule_based_classification(self, content: str) -> Dict[str, Any]:
        """Basic rule-based classification"""
        content_lower = content.lower()
        
        # Determine category
        category = 'utility'  # default
        category_scores = {}
        
        for cat, keywords in self.categories.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            category_scores[cat] = score
        
        if category_scores:
            category = max(category_scores, key=category_scores.get)
        
        # Calculate urgency score
        urgency_score = 50.0  # baseline
        
        for level, keywords in self.urgency_indicators.items():
            for keyword in keywords:
                if keyword in content_lower:
                    if level == 'high':
                        urgency_score += 20
                    elif level == 'medium':
                        urgency_score += 10
                    elif level == 'excitement':
                        urgency_score += 25
        
        # Cap urgency score
        urgency_score = min(urgency_score, 100.0)
        
        # Calculate novelty score (basic)
        novelty_indicators = ['new', 'innovative', 'never', 'first', 'unique', 'original']
        novelty_score = 50.0
        
        for indicator in novelty_indicators:
            if indicator in content_lower:
                novelty_score += 10
        
        novelty_score = min(novelty_score, 100.0)
        
        # Extract basic tags
        tags = []
        for tag_name, keywords in self.categories.items():
            if any(keyword in content_lower for keyword in keywords):
                tags.append(tag_name)
        
        # Add urgency tags
        if urgency_score > 80:
            tags.append('urgent')
        elif urgency_score > 65:
            tags.append('high-priority')
        
        return {
            'category': category,
            'urgency_score': urgency_score,
            'novelty_score': novelty_score,
            'tags': tags,
            'reasoning': 'Rule-based keyword matching'
        }
    
    async def _ai_classification(self, content: str) -> Dict[str, Any]:
        """AI-powered classification using Claude/GPT"""
        try:
            if not self.ai_service.is_available():
                return {}
            
            prompt = f"""
            Analyze this idea and provide classification:
            
            Idea: "{content}"
            
            Please provide:
            1. Category (creative, business, personal, metaphysical, utility)
            2. Urgency score (0-100) based on tone and content
            3. Novelty score (0-100) based on uniqueness
            4. Relevant tags (max 5)
            5. Brief reasoning
            
            Respond in JSON format:
            {{
                "category": "...",
                "urgency_score": 0,
                "novelty_score": 0,
                "tags": ["tag1", "tag2"],
                "reasoning": "..."
            }}
            """
            
            response = await self.ai_service.get_completion(prompt, max_tokens=300)
            
            if response:
                try:
                    # Extract JSON from response
                    json_match = re.search(r'\{.*\}', response, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                        return result
                except json.JSONDecodeError:
                    self.logger.error("Failed to parse AI classification response")
            
            return {}
            
        except Exception as e:
            self.logger.error(f"AI classification failed: {e}")
            return {}
    
    async def _add_tags(self, db, idea_id: str, tag_names: List[str]):
        """Add tags to idea"""
        try:
            for tag_name in tag_names:
                if tag_name and tag_name.strip():
                    TagCRUD.get_or_create_tag(db, tag_name.strip())
                    # In a real implementation, you'd associate the tag with the idea
                    # This would require proper many-to-many relationship handling
                    
        except Exception as e:
            self.logger.error(f"Failed to add tags: {e}")
    
    async def _trigger_expansion(self, idea_id: str, content: str, classification: Dict[str, Any]):
        """Trigger idea expansion for promising ideas"""
        try:
            await self.send_message(
                recipient="expander",
                action="expand_idea",
                data={
                    'idea_id': idea_id,
                    'content': content,
                    'classification': classification
                }
            )
            
            self.logger.info(f"Triggered expansion for idea {idea_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to trigger expansion: {e}")
    
    async def analyze_batch(self, idea_ids: List[str]) -> Dict[str, Any]:
        """Analyze multiple ideas in batch"""
        results = []
        
        for idea_id in idea_ids:
            with get_db() as db:
                idea = IdeaCRUD.get_idea(db, idea_id)
                if idea:
                    result = await self.process({
                        'idea_id': idea_id,
                        'content': idea.content_raw or idea.content_transcribed
                    })
                    results.append(result)
        
        return {
            'batch_results': results,
            'total_processed': len(results),
            'success_count': len([r for r in results if r.get('success')])
        }
    
    async def reclassify_idea(self, idea_id: str, force_ai: bool = False) -> Dict[str, Any]:
        """Reclassify an existing idea"""
        try:
            with get_db() as db:
                idea = IdeaCRUD.get_idea(db, idea_id)
                if not idea:
                    return {'error': f'Idea {idea_id} not found'}
                
                content = idea.content_raw or idea.content_transcribed
                
                if force_ai:
                    # Force AI classification
                    classification = await self._ai_classification(content)
                    if not classification:
                        return {'error': 'AI classification failed'}
                else:
                    # Use normal classification
                    classification = await self._classify_idea(content)
                
                # Update idea
                IdeaCRUD.update_idea(
                    db=db,
                    idea_id=idea_id,
                    category=classification['category'],
                    urgency_score=classification['urgency_score'],
                    novelty_score=classification['novelty_score']
                )
                
                return {
                    'success': True,
                    'idea_id': idea_id,
                    'classification': classification,
                    'message': 'Idea reclassified successfully'
                }
                
        except Exception as e:
            self.logger.error(f"Error reclassifying idea {idea_id}: {e}")
            return {'error': f'Reclassification failed: {str(e)}'}
    
    def get_classification_stats(self) -> Dict[str, Any]:
        """Get classification statistics"""
        try:
            with get_db() as db:
                ideas = IdeaCRUD.get_ideas(db, limit=1000)
                
                category_counts = {}
                urgency_distribution = {'low': 0, 'medium': 0, 'high': 0}
                
                for idea in ideas:
                    # Count categories
                    if idea.category:
                        category_counts[idea.category] = category_counts.get(idea.category, 0) + 1
                    
                    # Count urgency distribution
                    if idea.urgency_score:
                        if idea.urgency_score < 40:
                            urgency_distribution['low'] += 1
                        elif idea.urgency_score < 70:
                            urgency_distribution['medium'] += 1
                        else:
                            urgency_distribution['high'] += 1
                
                return {
                    'total_ideas': len(ideas),
                    'category_counts': category_counts,
                    'urgency_distribution': urgency_distribution,
                    'avg_urgency': sum(i.urgency_score or 0 for i in ideas) / len(ideas) if ideas else 0
                }
                
        except Exception as e:
            self.logger.error(f"Error getting classification stats: {e}")
            return {'error': 'Failed to get statistics'}