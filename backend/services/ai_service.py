import os
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class AIService:
    """
    Service for interacting with AI models (Claude, GPT, local models)
    Handles API calls, rate limiting, and fallback logic
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ai_service")
        
        # Initialize clients
        self.claude_client = None
        self.openai_client = None
        
        # Configuration
        self.default_model = "claude"
        self.rate_limit_delay = 1.0  # seconds between requests
        self.max_retries = 3
        
        # Initialize available clients
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize AI service clients"""
        # Initialize Claude client
        if ANTHROPIC_AVAILABLE:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                try:
                    self.claude_client = anthropic.Anthropic(api_key=api_key)
                    self.logger.info("Claude client initialized")
                except Exception as e:
                    self.logger.error(f"Failed to initialize Claude client: {e}")
        
        # Initialize OpenAI client
        if OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                try:
                    self.openai_client = openai.OpenAI(api_key=api_key)
                    self.logger.info("OpenAI client initialized")
                except Exception as e:
                    self.logger.error(f"Failed to initialize OpenAI client: {e}")
    
    def is_available(self) -> bool:
        """Check if any AI service is available"""
        return self.claude_client is not None or self.openai_client is not None
    
    def get_available_models(self) -> List[str]:
        """Get list of available AI models"""
        models = []
        if self.claude_client:
            models.extend(["claude-3-haiku", "claude-3-sonnet", "claude-3-opus"])
        if self.openai_client:
            models.extend(["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"])
        return models
    
    async def get_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> Optional[str]:
        """Get completion from AI model with fallback logic"""
        
        # Determine which model to use
        if not model:
            model = self.default_model
        
        # Try Claude first if available
        if model.startswith("claude") and self.claude_client:
            result = await self._get_claude_completion(
                prompt, model, max_tokens, temperature, system_prompt
            )
            if result:
                return result
        
        # Try OpenAI if Claude fails or not available
        if model.startswith("gpt") and self.openai_client:
            result = await self._get_openai_completion(
                prompt, model, max_tokens, temperature, system_prompt
            )
            if result:
                return result
        
        # Fallback to any available model
        if self.claude_client:
            result = await self._get_claude_completion(
                prompt, "claude-3-haiku", max_tokens, temperature, system_prompt
            )
            if result:
                return result
        
        if self.openai_client:
            result = await self._get_openai_completion(
                prompt, "gpt-3.5-turbo", max_tokens, temperature, system_prompt
            )
            if result:
                return result
        
        self.logger.error("No AI models available for completion")
        return None
    
    async def _get_claude_completion(
        self,
        prompt: str,
        model: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str]
    ) -> Optional[str]:
        """Get completion from Claude"""
        try:
            # Map model names
            model_mapping = {
                "claude": "claude-3-haiku-20240307",
                "claude-3-haiku": "claude-3-haiku-20240307",
                "claude-3-sonnet": "claude-3-sonnet-20240229",
                "claude-3-opus": "claude-3-opus-20240229"
            }
            
            model_name = model_mapping.get(model, "claude-3-haiku-20240307")
            
            # Prepare messages
            messages = [{"role": "user", "content": prompt}]
            
            # Make API call
            response = await asyncio.to_thread(
                self.claude_client.messages.create,
                model=model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt or "You are a helpful AI assistant.",
                messages=messages
            )
            
            if response.content:
                return response.content[0].text
            
        except Exception as e:
            self.logger.error(f"Claude completion failed: {e}")
        
        return None
    
    async def _get_openai_completion(
        self,
        prompt: str,
        model: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str]
    ) -> Optional[str]:
        """Get completion from OpenAI"""
        try:
            # Prepare messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Make API call
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            if response.choices:
                return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"OpenAI completion failed: {e}")
        
        return None
    
    async def analyze_idea(self, content: str) -> Dict[str, Any]:
        """Analyze an idea and provide structured feedback"""
        prompt = f"""
        Analyze this idea comprehensively:
        
        Idea: "{content}"
        
        Please provide:
        1. Category (creative, business, personal, metaphysical, utility)
        2. Viability score (0-100)
        3. Novelty score (0-100)
        4. Potential challenges
        5. Next steps
        6. Related concepts
        
        Format as JSON:
        {{
            "category": "...",
            "viability_score": 0,
            "novelty_score": 0,
            "challenges": ["challenge1", "challenge2"],
            "next_steps": ["step1", "step2"],
            "related_concepts": ["concept1", "concept2"],
            "summary": "Brief analysis summary"
        }}
        """
        
        response = await self.get_completion(prompt, max_tokens=500)
        
        if response:
            try:
                # Extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except json.JSONDecodeError:
                self.logger.error("Failed to parse idea analysis response")
        
        return {}
    
    async def expand_idea(self, content: str, context: Optional[Dict] = None) -> str:
        """Expand an idea with additional context and possibilities"""
        context_info = ""
        if context:
            context_info = f"\nContext: {json.dumps(context, indent=2)}"
        
        prompt = f"""
        Expand on this idea with creative possibilities and practical applications:
        
        Original idea: "{content}"{context_info}
        
        Please provide:
        1. 3 different interpretations or applications
        2. Potential features or components
        3. Target audience or use cases
        4. Technical considerations (if applicable)
        5. Creative enhancements
        
        Write in an engaging, creative style that matches the original idea's energy.
        """
        
        response = await self.get_completion(prompt, max_tokens=800, temperature=0.8)
        return response or f"Could not expand idea: {content}"
    
    async def generate_proposal(self, idea_content: str, classification: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a project proposal for an idea"""
        prompt = f"""
        Create a structured project proposal for this idea:
        
        Idea: "{idea_content}"
        Classification: {json.dumps(classification, indent=2)}
        
        Generate a proposal with:
        1. Compelling title
        2. Problem statement
        3. Solution approach
        4. Key features
        5. Implementation plan (5-7 steps)
        6. Success metrics
        7. Potential challenges
        
        Format as JSON:
        {{
            "title": "...",
            "problem_statement": "...",
            "solution_approach": "...",
            "key_features": ["feature1", "feature2"],
            "implementation_plan": [
                {{"step": 1, "title": "...", "description": "...", "duration": "..."}},
                {{"step": 2, "title": "...", "description": "...", "duration": "..."}}
            ],
            "success_metrics": ["metric1", "metric2"],
            "challenges": ["challenge1", "challenge2"]
        }}
        """
        
        response = await self.get_completion(prompt, max_tokens=1000)
        
        if response:
            try:
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except json.JSONDecodeError:
                self.logger.error("Failed to parse proposal response")
        
        return {}
    
    async def generate_visual_prompt(self, idea_content: str, style_preference: str = "modern") -> str:
        """Generate a visual prompt for ComfyUI based on idea content"""
        prompt = f"""
        Create a detailed visual prompt for AI image generation based on this idea:
        
        Idea: "{idea_content}"
        Style preference: {style_preference}
        
        Generate a prompt that:
        1. Captures the essence of the idea visually
        2. Uses appropriate artistic style
        3. Includes relevant technical details
        4. Considers the intended use (poster, icon, illustration, etc.)
        
        Provide just the visual prompt, optimized for Stable Diffusion/ComfyUI.
        """
        
        response = await self.get_completion(prompt, max_tokens=300, temperature=0.8)
        return response or f"Abstract visualization of: {idea_content}"
    
    async def critique_and_improve(self, content: str, improvement_type: str = "general") -> str:
        """Provide critique and improvement suggestions"""
        prompt = f"""
        Provide constructive critique and improvement suggestions for this idea:
        
        Idea: "{content}"
        Focus area: {improvement_type}
        
        Please provide:
        1. What's working well
        2. Areas for improvement
        3. Specific enhancement suggestions
        4. Alternative approaches
        
        Be encouraging but honest, with a focus on actionable improvements.
        """
        
        response = await self.get_completion(prompt, max_tokens=600, temperature=0.7)
        return response or f"Could not provide critique for: {content}"
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get AI service usage statistics"""
        # This would track API calls, costs, etc.
        # For now, return placeholder data
        return {
            "claude_available": self.claude_client is not None,
            "openai_available": self.openai_client is not None,
            "default_model": self.default_model,
            "total_requests": 0,  # Would be tracked in real implementation
            "successful_requests": 0,
            "failed_requests": 0
        }