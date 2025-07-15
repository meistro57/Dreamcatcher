import asyncio
import json
import requests
import base64
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import os

from .base_agent import BaseAgent
from ..database import get_db, IdeaCRUD, VisualizationCRUD
from ..services import AIService

class AgentVisualizer(BaseAgent):
    """
    Agent responsible for generating visual representations of ideas using ComfyUI.
    Creates adaptive visuals based on idea content and category.
    """
    
    def __init__(self):
        super().__init__(
            agent_id="visualizer",
            name="Visual Agent",
            description="Darling, that idea needs a visual. Let me handle it.",
            version="1.0.0"
        )
        
        # ComfyUI configuration
        self.comfyui_url = os.getenv('COMFYUI_URL', 'http://localhost:8188')
        self.comfyui_enabled = os.getenv('COMFYUI_ENABLED', 'true').lower() == 'true'
        
        # AI service for prompt generation
        self.ai_service = AIService()
        
        # Visual styles by category
        self.visual_styles = {
            'creative': {
                'style': 'artistic, abstract, vibrant colors, creative composition',
                'negative': 'boring, conventional, monochrome',
                'sampler': 'euler',
                'steps': 25,
                'cfg_scale': 7.5
            },
            'business': {
                'style': 'professional, modern, clean, corporate, sleek design',
                'negative': 'chaotic, unprofessional, messy',
                'sampler': 'dpmpp_2m',
                'steps': 20,
                'cfg_scale': 7.0
            },
            'technical': {
                'style': 'technical diagram, blueprint, schematic, clean lines, precise',
                'negative': 'artistic, abstract, imprecise',
                'sampler': 'euler',
                'steps': 20,
                'cfg_scale': 8.0
            },
            'personal': {
                'style': 'warm, personal, lifestyle, comfortable, natural lighting',
                'negative': 'cold, impersonal, harsh',
                'sampler': 'dpmpp_2m',
                'steps': 25,
                'cfg_scale': 7.0
            },
            'metaphysical': {
                'style': 'ethereal, mystical, cosmic, spiritual, otherworldly',
                'negative': 'mundane, ordinary, earthly',
                'sampler': 'euler',
                'steps': 30,
                'cfg_scale': 8.5
            }
        }
        
        # Default workflow template
        self.default_workflow = {
            "1": {
                "inputs": {
                    "ckpt_name": "sd_xl_base_1.0.safetensors"
                },
                "class_type": "CheckpointLoaderSimple"
            },
            "2": {
                "inputs": {
                    "width": 1024,
                    "height": 1024,
                    "batch_size": 1
                },
                "class_type": "EmptyLatentImage"
            },
            "3": {
                "inputs": {
                    "seed": 42,
                    "steps": 20,
                    "cfg": 7.0,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1.0,
                    "model": ["1", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["2", 0]
                },
                "class_type": "KSampler"
            },
            "4": {
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["1", 2]
                },
                "class_type": "VAEDecode"
            },
            "5": {
                "inputs": {
                    "filename_prefix": "dreamcatcher_idea",
                    "images": ["4", 0]
                },
                "class_type": "SaveImage"
            },
            "6": {
                "inputs": {
                    "text": "PLACEHOLDER_POSITIVE",
                    "clip": ["1", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            "7": {
                "inputs": {
                    "text": "PLACEHOLDER_NEGATIVE",
                    "clip": ["1", 1]
                },
                "class_type": "CLIPTextEncode"
            }
        }
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process visualization request"""
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
                
                # Generate visual prompt
                visual_prompt = await self._generate_visual_prompt(
                    original_content, 
                    expanded_content, 
                    idea.category
                )
                
                if not visual_prompt:
                    return {'error': 'Failed to generate visual prompt'}
                
                # Generate multiple visual variations
                visualizations = []
                
                # Primary style based on category
                primary_visual = await self._generate_visual(
                    visual_prompt, 
                    idea.category or 'creative',
                    'primary'
                )
                
                if primary_visual:
                    visualizations.append(primary_visual)
                
                # Alternative style for variety
                alt_category = self._get_alternative_category(idea.category)
                alt_visual = await self._generate_visual(
                    visual_prompt, 
                    alt_category,
                    'alternative'
                )
                
                if alt_visual:
                    visualizations.append(alt_visual)
                
                # Abstract interpretation
                abstract_prompt = await self._generate_abstract_prompt(original_content)
                if abstract_prompt:
                    abstract_visual = await self._generate_visual(
                        abstract_prompt, 
                        'creative',
                        'abstract'
                    )
                    if abstract_visual:
                        visualizations.append(abstract_visual)
                
                # Save visualizations to database
                saved_visuals = []
                for viz in visualizations:
                    saved_viz = VisualizationCRUD.create_visualization(
                        db=db,
                        idea_id=idea_id,
                        image_path=viz.get('image_path', ''),
                        prompt_used=viz.get('prompt', ''),
                        style_config=json.dumps(viz.get('style_config', {})),
                        generation_params=json.dumps(viz.get('params', {})),
                        visualization_type=viz.get('type', 'primary'),
                        agent_version=self.version
                    )
                    saved_visuals.append(saved_viz)
                
                # Trigger next stage if visuals were generated
                if len(saved_visuals) > 0:
                    await self._trigger_proposal_generation(idea_id, original_content, expanded_content)
                
                return {
                    'success': True,
                    'idea_id': idea_id,
                    'visualizations_count': len(saved_visuals),
                    'visualizations': [
                        {
                            'id': viz.id,
                            'image_path': viz.image_path,
                            'type': viz.visualization_type,
                            'created_at': viz.created_at.isoformat()
                        } for viz in saved_visuals
                    ],
                    'message': f"Generated {len(saved_visuals)} visualizations for idea"
                }
                
        except Exception as e:
            self.logger.error(f"Error generating visuals for idea {idea_id}: {e}")
            return {'error': f'Visualization failed: {str(e)}'}
    
    async def _generate_visual_prompt(self, original: str, expanded: str, category: str) -> str:
        """Generate visual prompt using AI"""
        try:
            prompt = f"""
            Create a detailed visual prompt for generating an image that represents this idea:
            
            Original idea: "{original}"
            Expanded description: "{expanded}"
            Category: {category}
            
            Generate a detailed prompt that includes:
            - Visual style appropriate for {category} ideas
            - Composition and framing suggestions
            - Color palette and mood
            - Specific visual elements that represent the concept
            - Artistic techniques or approaches
            
            Make it vivid and specific enough for AI image generation.
            Focus on visual elements, not text or words in the image.
            """
            
            response = await self.ai_service.get_completion(
                prompt=prompt,
                model="claude-3-sonnet",
                max_tokens=400,
                temperature=0.8
            )
            
            return response or ""
            
        except Exception as e:
            self.logger.error(f"Failed to generate visual prompt: {e}")
            return ""
    
    async def _generate_abstract_prompt(self, original: str) -> str:
        """Generate abstract visual interpretation"""
        try:
            prompt = f"""
            Create an abstract visual prompt for this idea:
            
            "{original}"
            
            Generate a prompt for an abstract, artistic interpretation focusing on:
            - Shapes, colors, and forms that represent the essence
            - Emotional qualities and energy
            - Symbolic elements
            - Abstract composition and flow
            
            Make it artistic and non-literal.
            """
            
            response = await self.ai_service.get_completion(
                prompt=prompt,
                max_tokens=200,
                temperature=0.9
            )
            
            return response or ""
            
        except Exception as e:
            self.logger.error(f"Failed to generate abstract prompt: {e}")
            return ""
    
    async def _generate_visual(self, prompt: str, category: str, variant_type: str) -> Optional[Dict[str, Any]]:
        """Generate visual using ComfyUI"""
        try:
            if not self.comfyui_enabled:
                # Mock generation for testing
                return {
                    'image_path': f'/mock/visuals/{hashlib.md5(prompt.encode()).hexdigest()}.png',
                    'prompt': prompt,
                    'style_config': self.visual_styles.get(category, self.visual_styles['creative']),
                    'params': {'steps': 20, 'cfg': 7.0, 'sampler': 'euler'},
                    'type': variant_type
                }
            
            # Get style configuration
            style_config = self.visual_styles.get(category, self.visual_styles['creative'])
            
            # Create workflow with prompts
            workflow = self._create_workflow(prompt, style_config)
            
            # Generate unique seed for variety
            seed = hash(prompt + variant_type) % 1000000
            workflow["3"]["inputs"]["seed"] = seed
            
            # Send request to ComfyUI
            response = await self._send_comfyui_request(workflow)
            
            if response and response.get('success'):
                return {
                    'image_path': response.get('image_path', ''),
                    'prompt': prompt,
                    'style_config': style_config,
                    'params': {
                        'seed': seed,
                        'steps': style_config['steps'],
                        'cfg': style_config['cfg_scale'],
                        'sampler': style_config['sampler']
                    },
                    'type': variant_type
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Visual generation failed: {e}")
            return None
    
    def _create_workflow(self, prompt: str, style_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create ComfyUI workflow with prompt and style"""
        workflow = self.default_workflow.copy()
        
        # Build full positive prompt
        positive_prompt = f"{prompt}, {style_config['style']}"
        negative_prompt = style_config['negative']
        
        # Update workflow with prompts
        workflow["6"]["inputs"]["text"] = positive_prompt
        workflow["7"]["inputs"]["text"] = negative_prompt
        
        # Update sampler settings
        workflow["3"]["inputs"]["steps"] = style_config['steps']
        workflow["3"]["inputs"]["cfg"] = style_config['cfg_scale']
        workflow["3"]["inputs"]["sampler_name"] = style_config['sampler']
        
        return workflow
    
    async def _send_comfyui_request(self, workflow: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send request to ComfyUI API"""
        try:
            # Queue the workflow
            queue_response = requests.post(
                f"{self.comfyui_url}/prompt",
                json={"prompt": workflow},
                timeout=30
            )
            
            if queue_response.status_code != 200:
                self.logger.error(f"ComfyUI queue failed: {queue_response.status_code}")
                return None
            
            prompt_id = queue_response.json().get('prompt_id')
            if not prompt_id:
                return None
            
            # Wait for completion (simplified - in production, use websockets)
            await asyncio.sleep(10)  # Basic wait - should be replaced with proper polling
            
            # Get result
            history_response = requests.get(f"{self.comfyui_url}/history/{prompt_id}")
            if history_response.status_code != 200:
                return None
            
            history = history_response.json()
            if prompt_id not in history:
                return None
            
            # Extract image path (simplified)
            outputs = history[prompt_id].get('outputs', {})
            if '5' in outputs and 'images' in outputs['5']:
                image_info = outputs['5']['images'][0]
                image_path = f"/opt/dreamcatcher/storage/visuals/{image_info['filename']}"
                
                return {
                    'success': True,
                    'image_path': image_path,
                    'filename': image_info['filename']
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"ComfyUI request failed: {e}")
            return None
    
    def _get_alternative_category(self, category: str) -> str:
        """Get alternative category for variety"""
        alternatives = {
            'creative': 'personal',
            'business': 'technical',
            'technical': 'business',
            'personal': 'creative',
            'metaphysical': 'creative'
        }
        return alternatives.get(category, 'creative')
    
    async def _trigger_proposal_generation(self, idea_id: str, original_content: str, expanded_content: str):
        """Trigger proposal generation after successful visualization"""
        try:
            await self.send_message(
                recipient="proposer",
                action="generate_proposal",
                data={
                    'idea_id': idea_id,
                    'original_content': original_content,
                    'expanded_content': expanded_content
                }
            )
            
            self.logger.info(f"Triggered proposal generation for idea {idea_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to trigger proposal generation: {e}")
    
    async def regenerate_visual(self, idea_id: str, style_type: str = 'primary') -> Dict[str, Any]:
        """Regenerate visual for an existing idea"""
        try:
            with get_db() as db:
                idea = IdeaCRUD.get_idea(db, idea_id)
                if not idea:
                    return {'error': f'Idea {idea_id} not found'}
                
                # Get existing expansion if available
                expanded_content = ""
                if hasattr(idea, 'expansions') and idea.expansions:
                    expanded_content = idea.expansions[0].expanded_content
                
                # Generate new visual prompt
                visual_prompt = await self._generate_visual_prompt(
                    idea.content_transcribed or idea.content_raw,
                    expanded_content,
                    idea.category
                )
                
                if not visual_prompt:
                    return {'error': 'Failed to generate visual prompt'}
                
                # Generate new visual
                new_visual = await self._generate_visual(
                    visual_prompt,
                    idea.category or 'creative',
                    style_type
                )
                
                if new_visual:
                    # Save to database
                    saved_viz = VisualizationCRUD.create_visualization(
                        db=db,
                        idea_id=idea_id,
                        image_path=new_visual.get('image_path', ''),
                        prompt_used=new_visual.get('prompt', ''),
                        style_config=json.dumps(new_visual.get('style_config', {})),
                        generation_params=json.dumps(new_visual.get('params', {})),
                        visualization_type=style_type,
                        agent_version=self.version
                    )
                    
                    return {
                        'success': True,
                        'idea_id': idea_id,
                        'visualization': {
                            'id': saved_viz.id,
                            'image_path': saved_viz.image_path,
                            'type': saved_viz.visualization_type,
                            'created_at': saved_viz.created_at.isoformat()
                        }
                    }
                else:
                    return {'error': 'Failed to generate visual'}
                    
        except Exception as e:
            self.logger.error(f"Error regenerating visual for idea {idea_id}: {e}")
            return {'error': f'Visual regeneration failed: {str(e)}'}
    
    async def get_style_suggestions(self, idea_id: str) -> List[Dict[str, Any]]:
        """Get style suggestions for an idea"""
        try:
            with get_db() as db:
                idea = IdeaCRUD.get_idea(db, idea_id)
                if not idea:
                    return []
                
                # Return available styles with descriptions
                suggestions = []
                for style_name, style_config in self.visual_styles.items():
                    suggestions.append({
                        'name': style_name,
                        'description': style_config['style'],
                        'suitable_for': self._get_style_suitability(style_name, idea.category)
                    })
                
                return suggestions
                
        except Exception as e:
            self.logger.error(f"Error getting style suggestions: {e}")
            return []
    
    def _get_style_suitability(self, style_name: str, idea_category: str) -> str:
        """Get suitability description for a style"""
        if style_name == idea_category:
            return "Perfect match for this idea category"
        
        suitability_map = {
            'creative': "Great for artistic and innovative ideas",
            'business': "Professional and polished presentation",
            'technical': "Clear and precise visualization",
            'personal': "Warm and relatable imagery",
            'metaphysical': "Mystical and ethereal representation"
        }
        
        return suitability_map.get(style_name, "Alternative visual interpretation")