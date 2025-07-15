import os
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import re
from dataclasses import dataclass
from enum import Enum

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

class AIServiceError(Exception):
    """Base exception for AI service errors"""
    pass

class AIServiceUnavailableError(AIServiceError):
    """Raised when no AI services are available"""
    pass

class AIServiceRateLimitError(AIServiceError):
    """Raised when API rate limits are exceeded"""
    pass

class AIServiceAuthenticationError(AIServiceError):
    """Raised when API authentication fails"""
    pass

class AIServiceQuotaError(AIServiceError):
    """Raised when API quota is exceeded"""
    pass

@dataclass
class AIResponse:
    """Structured AI response with metadata"""
    response: str
    model: str
    tokens_used: int
    input_tokens: int
    timestamp: str
    context: Optional[Dict[str, Any]] = None
    fallback_used: bool = False
    original_model: Optional[str] = None
    response_time: float = 0.0

class AIService:
    """
    Enhanced AI service with comprehensive error handling and fallback logic
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ai_service")
        
        # Initialize clients
        self.claude_client = None
        self.openai_client = None
        
        # Configuration
        self.default_model = "claude-3-haiku"
        self.rate_limit_delay = 1.0  # seconds between requests
        self.max_retries = 3
        self.timeout = 30.0  # seconds
        
        # Usage tracking
        self.usage_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "claude_requests": 0,
            "openai_requests": 0,
            "fallback_used": 0
        }
        
        # Initialize available clients
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize AI service clients with proper error handling"""
        # Initialize Claude client
        if ANTHROPIC_AVAILABLE:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                try:
                    self.claude_client = anthropic.Anthropic(api_key=api_key)
                    self.logger.info("Claude client initialized successfully")
                except Exception as e:
                    self.logger.error(f"Failed to initialize Claude client: {e}")
                    self.claude_client = None
            else:
                self.logger.warning("ANTHROPIC_API_KEY not found - Claude client disabled")
        else:
            self.logger.warning("Anthropic library not available - install with: pip install anthropic")
        
        # Initialize OpenAI client
        if OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                try:
                    self.openai_client = openai.OpenAI(api_key=api_key)
                    self.logger.info("OpenAI client initialized successfully")
                except Exception as e:
                    self.logger.error(f"Failed to initialize OpenAI client: {e}")
                    self.openai_client = None
            else:
                self.logger.warning("OPENAI_API_KEY not found - OpenAI client disabled")
        else:
            self.logger.warning("OpenAI library not available - install with: pip install openai")
        
        # Check if any service is available
        if not self.is_available():
            self.logger.error("No AI services available - please configure API keys")
    
    def is_available(self) -> bool:
        """Check if any AI service is available"""
        return (self.claude_client is not None) or (self.openai_client is not None)
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        models = []
        if self.claude_client:
            models.extend(["claude-3-haiku", "claude-3-sonnet", "claude-3-opus"])
        if self.openai_client:
            models.extend(["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"])
        return models
    
    def _validate_inputs(self, prompt: str, max_tokens: int, temperature: float):
        """Validate inputs with descriptive error messages"""
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty or whitespace-only")
        
        if len(prompt) > 50000:  # Reasonable limit
            raise ValueError("Prompt too long - maximum 50,000 characters")
        
        if max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        
        if max_tokens > 4096:
            raise ValueError("max_tokens cannot exceed 4096")
        
        if not (0.0 <= temperature <= 1.0):
            raise ValueError("temperature must be between 0.0 and 1.0")
    
    def _handle_api_error(self, e: Exception, service: str) -> None:
        """Handle API errors with specific error types"""
        error_msg = str(e).lower()
        
        if "authentication" in error_msg or "api key" in error_msg:
            raise AIServiceAuthenticationError(f"{service} authentication failed: {e}")
        elif "rate limit" in error_msg or "too many requests" in error_msg:
            raise AIServiceRateLimitError(f"{service} rate limit exceeded: {e}")
        elif "quota" in error_msg or "insufficient" in error_msg:
            raise AIServiceQuotaError(f"{service} quota exceeded: {e}")
        else:
            raise AIServiceError(f"{service} API error: {e}")
    
    async def generate_response(
        self, 
        prompt: str, 
        model: Optional[str] = None, 
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AIResponse:
        """
        Generate response from AI model with comprehensive error handling
        """
        start_time = datetime.utcnow()
        
        # Check availability
        if not self.is_available():
            self.usage_stats["failed_requests"] += 1
            raise AIServiceUnavailableError("No AI services available")
        
        # Validate inputs
        try:
            self._validate_inputs(prompt, max_tokens, temperature)
        except ValueError as e:
            self.usage_stats["failed_requests"] += 1
            raise
        
        # Determine model to use
        if not model:
            model = self._get_default_model()
        
        # Track request
        self.usage_stats["total_requests"] += 1
        
        # Attempt generation with retries
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                # Add exponential backoff for retries
                if attempt > 0:
                    delay = self.rate_limit_delay * (2 ** attempt)
                    self.logger.info(f"Retrying after {delay}s delay (attempt {attempt + 1}/{self.max_retries})")
                    await asyncio.sleep(delay)
                
                result = await self._generate_with_model(
                    prompt=prompt,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system_prompt=system_prompt,
                    context=context
                )
                
                # Calculate response time
                response_time = (datetime.utcnow() - start_time).total_seconds()
                result.response_time = response_time
                
                # Log successful generation
                self.usage_stats["successful_requests"] += 1
                self.logger.info(
                    f"AI response generated: model={model}, "
                    f"tokens={result.tokens_used}, time={response_time:.2f}s"
                )
                return result
                
            except (AIServiceRateLimitError, AIServiceQuotaError) as e:
                last_exception = e
                self.logger.warning(f"Rate limit/quota error on attempt {attempt + 1}: {e}")
                # For rate limits, wait longer before retry
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.rate_limit_delay * 3)
                
            except (AIServiceAuthenticationError, AIServiceUnavailableError) as e:
                # These errors won't be fixed by retrying
                self.usage_stats["failed_requests"] += 1
                raise
                
            except Exception as e:
                last_exception = e
                self.logger.warning(f"AI generation attempt {attempt + 1} failed: {e}")
        
        # All retries failed, try fallback
        try:
            fallback_result = await self._try_fallback_model(
                prompt=prompt,
                original_model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system_prompt=system_prompt,
                context=context
            )
            
            if fallback_result:
                self.usage_stats["successful_requests"] += 1
                self.usage_stats["fallback_used"] += 1
                response_time = (datetime.utcnow() - start_time).total_seconds()
                fallback_result.response_time = response_time
                return fallback_result
                
        except Exception as e:
            self.logger.error(f"Fallback also failed: {e}")
        
        # All attempts failed
        self.usage_stats["failed_requests"] += 1
        self.logger.error(f"All AI generation attempts failed. Last error: {last_exception}")
        raise AIServiceError(f"AI generation failed after {self.max_retries} attempts: {last_exception}")
    
    def _get_default_model(self) -> str:
        """Get default model based on availability"""
        if self.claude_client:
            return "claude-3-haiku"
        elif self.openai_client:
            return "gpt-3.5-turbo"
        else:
            raise AIServiceUnavailableError("No AI clients available")
    
    async def _generate_with_model(
        self,
        prompt: str,
        model: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AIResponse:
        """Generate response with specific model"""
        
        if model.startswith("claude"):
            if not self.claude_client:
                raise AIServiceUnavailableError("Claude client not available")
            return await self._generate_claude_response(
                prompt, model, max_tokens, temperature, system_prompt, context
            )
        elif model.startswith("gpt"):
            if not self.openai_client:
                raise AIServiceUnavailableError("OpenAI client not available")
            return await self._generate_openai_response(
                prompt, model, max_tokens, temperature, system_prompt, context
            )
        else:
            raise ValueError(f"Unsupported model: {model}")
    
    async def _generate_claude_response(
        self,
        prompt: str,
        model: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AIResponse:
        """Generate response using Claude with proper error handling"""
        
        # Map model names to exact API names
        model_mapping = {
            "claude-3-haiku": "claude-3-haiku-20240307",
            "claude-3-sonnet": "claude-3-sonnet-20240229",
            "claude-3-opus": "claude-3-opus-20240229"
        }
        
        api_model = model_mapping.get(model, "claude-3-haiku-20240307")
        
        try:
            messages = [{"role": "user", "content": prompt}]
            system = system_prompt or "You are a helpful AI assistant."
            
            # Use timeout for the API call
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.claude_client.messages.create,
                    model=api_model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system,
                    messages=messages
                ),
                timeout=self.timeout
            )
            
            self.usage_stats["claude_requests"] += 1
            
            return AIResponse(
                response=response.content[0].text,
                model=model,
                tokens_used=response.usage.output_tokens,
                input_tokens=response.usage.input_tokens,
                timestamp=datetime.utcnow().isoformat(),
                context=context
            )
            
        except asyncio.TimeoutError:
            raise AIServiceError(f"Claude API request timed out after {self.timeout}s")
        except Exception as e:
            self._handle_api_error(e, "Claude")
    
    async def _generate_openai_response(
        self,
        prompt: str,
        model: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AIResponse:
        """Generate response using OpenAI with proper error handling"""
        
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            # Use timeout for the API call
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.openai_client.chat.completions.create,
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                ),
                timeout=self.timeout
            )
            
            self.usage_stats["openai_requests"] += 1
            
            return AIResponse(
                response=response.choices[0].message.content,
                model=model,
                tokens_used=response.usage.total_tokens,
                input_tokens=response.usage.prompt_tokens,
                timestamp=datetime.utcnow().isoformat(),
                context=context
            )
            
        except asyncio.TimeoutError:
            raise AIServiceError(f"OpenAI API request timed out after {self.timeout}s")
        except Exception as e:
            self._handle_api_error(e, "OpenAI")
    
    async def _try_fallback_model(
        self,
        prompt: str,
        original_model: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[AIResponse]:
        """Try fallback model if primary fails"""
        fallback_models = self._get_fallback_models(original_model)
        
        for fallback_model in fallback_models:
            try:
                self.logger.info(f"Trying fallback model: {fallback_model}")
                
                result = await self._generate_with_model(
                    prompt=prompt,
                    model=fallback_model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system_prompt=system_prompt,
                    context=context
                )
                
                result.fallback_used = True
                result.original_model = original_model
                
                self.logger.info(f"Fallback successful: {fallback_model}")
                return result
                
            except Exception as e:
                self.logger.warning(f"Fallback model {fallback_model} failed: {e}")
                continue
        
        return None
    
    def _get_fallback_models(self, original_model: str) -> List[str]:
        """Get fallback models prioritized by reliability and cost"""
        fallback_map = {
            "claude-3-opus": ["claude-3-sonnet", "claude-3-haiku", "gpt-4"],
            "claude-3-sonnet": ["claude-3-haiku", "gpt-4-turbo", "gpt-3.5-turbo"],
            "claude-3-haiku": ["claude-3-sonnet", "gpt-3.5-turbo", "gpt-4"],
            "gpt-4": ["gpt-4-turbo", "claude-3-sonnet", "gpt-3.5-turbo"],
            "gpt-4-turbo": ["gpt-4", "claude-3-sonnet", "gpt-3.5-turbo"],
            "gpt-3.5-turbo": ["gpt-4", "claude-3-haiku", "claude-3-sonnet"]
        }
        
        fallbacks = fallback_map.get(original_model, [])
        available_models = self.get_available_models()
        
        return [model for model in fallbacks if model in available_models]
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to AI services"""
        results = {}
        
        # Test Claude
        if self.claude_client:
            try:
                start_time = datetime.utcnow()
                test_result = await self.generate_response(
                    "Say 'Hello' in one word.",
                    model="claude-3-haiku",
                    max_tokens=10
                )
                response_time = (datetime.utcnow() - start_time).total_seconds()
                
                results['claude'] = {
                    'available': True,
                    'response_time': response_time,
                    'model': test_result.model,
                    'tokens_used': test_result.tokens_used
                }
            except Exception as e:
                results['claude'] = {
                    'available': False,
                    'error': str(e)
                }
        else:
            results['claude'] = {
                'available': False,
                'error': 'Client not initialized'
            }
        
        # Test OpenAI
        if self.openai_client:
            try:
                start_time = datetime.utcnow()
                test_result = await self.generate_response(
                    "Say 'Hello' in one word.",
                    model="gpt-3.5-turbo",
                    max_tokens=10
                )
                response_time = (datetime.utcnow() - start_time).total_seconds()
                
                results['openai'] = {
                    'available': True,
                    'response_time': response_time,
                    'model': test_result.model,
                    'tokens_used': test_result.tokens_used
                }
            except Exception as e:
                results['openai'] = {
                    'available': False,
                    'error': str(e)
                }
        else:
            results['openai'] = {
                'available': False,
                'error': 'Client not initialized'
            }
        
        return results
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get comprehensive usage statistics"""
        stats = self.usage_stats.copy()
        
        # Add calculated metrics
        if stats["total_requests"] > 0:
            stats["success_rate"] = stats["successful_requests"] / stats["total_requests"]
            stats["failure_rate"] = stats["failed_requests"] / stats["total_requests"]
            stats["fallback_rate"] = stats["fallback_used"] / stats["total_requests"]
        else:
            stats["success_rate"] = 0.0
            stats["failure_rate"] = 0.0
            stats["fallback_rate"] = 0.0
        
        # Add service availability
        stats["claude_available"] = self.claude_client is not None
        stats["openai_available"] = self.openai_client is not None
        stats["default_model"] = self.default_model
        stats["available_models"] = self.get_available_models()
        
        return stats
    
    # High-level convenience methods with error handling
    async def analyze_idea(self, content: str) -> Dict[str, Any]:
        """Analyze an idea with error handling"""
        try:
            prompt = f"""
            Analyze this idea comprehensively:
            
            Idea: "{content}"
            
            Provide analysis in JSON format:
            {{
                "category": "one of: creative, business, personal, metaphysical, utility",
                "viability_score": 0-100,
                "novelty_score": 0-100,
                "challenges": ["challenge1", "challenge2"],
                "next_steps": ["step1", "step2"],
                "related_concepts": ["concept1", "concept2"],
                "summary": "Brief analysis summary"
            }}
            """
            
            response = await self.generate_response(prompt, max_tokens=500)
            
            # Extract and parse JSON
            json_match = re.search(r'\{.*\}', response.response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            self.logger.error(f"Idea analysis failed: {e}")
            # Return default analysis
            return {
                "category": "unknown",
                "viability_score": 50,
                "novelty_score": 50,
                "challenges": ["Analysis failed"],
                "next_steps": ["Manual review required"],
                "related_concepts": [],
                "summary": f"Analysis failed: {str(e)}"
            }
    
    async def expand_idea(self, content: str, context: Optional[Dict] = None) -> str:
        """Expand an idea with error handling"""
        try:
            context_info = ""
            if context:
                context_info = f"\nContext: {json.dumps(context, indent=2)}"
            
            prompt = f"""
            Expand on this idea with creative possibilities:
            
            Original idea: "{content}"{context_info}
            
            Provide:
            1. Three different interpretations
            2. Potential features or components
            3. Target audience or use cases
            4. Technical considerations
            5. Creative enhancements
            
            Write in an engaging, creative style.
            """
            
            response = await self.generate_response(prompt, max_tokens=800, temperature=0.8)
            return response.response
            
        except Exception as e:
            self.logger.error(f"Idea expansion failed: {e}")
            return f"Could not expand idea due to error: {str(e)}"
    
    async def generate_visual_prompt(self, idea_content: str, style_preference: str = "modern") -> str:
        """Generate visual prompt with error handling"""
        try:
            prompt = f"""
            Create a detailed visual prompt for AI image generation:
            
            Idea: "{idea_content}"
            Style: {style_preference}
            
            Generate a prompt optimized for Stable Diffusion that:
            1. Captures the essence visually
            2. Uses appropriate artistic style
            3. Includes technical details
            4. Considers intended use
            
            Provide just the visual prompt.
            """
            
            response = await self.generate_response(prompt, max_tokens=300, temperature=0.8)
            return response.response
            
        except Exception as e:
            self.logger.error(f"Visual prompt generation failed: {e}")
            return f"Abstract visualization of: {idea_content}"