import asyncio
import json
import logging
import os
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import aiohttp
import websockets
from dataclasses import dataclass
from enum import Enum

class ComfyUIError(Exception):
    """Base exception for ComfyUI service errors"""
    pass

class ComfyUIConnectionError(ComfyUIError):
    """Raised when ComfyUI connection fails"""
    pass

class ComfyUIGenerationError(ComfyUIError):
    """Raised when image generation fails"""
    pass

class ComfyUITimeoutError(ComfyUIError):
    """Raised when generation times out"""
    pass

class GenerationStatus(Enum):
    QUEUED = "queued"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class GenerationResult:
    """Result of image generation"""
    success: bool
    image_path: Optional[str] = None
    filename: Optional[str] = None
    prompt_id: Optional[str] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    queue_position: int = 0

class ComfyUIService:
    """
    Enhanced ComfyUI service with comprehensive error handling and WebSocket support
    """
    
    def __init__(self):
        self.logger = logging.getLogger("comfy_service")
        
        # Configuration
        self.base_url = os.getenv('COMFYUI_URL', 'http://localhost:8188')
        self.ws_url = self.base_url.replace('http', 'ws') + '/ws'
        self.enabled = os.getenv('COMFYUI_ENABLED', 'true').lower() == 'true'
        self.timeout = int(os.getenv('COMFYUI_TIMEOUT', '300'))  # 5 minutes
        self.max_retries = 3
        self.retry_delay = 2.0
        
        # Storage configuration
        self.storage_path = os.getenv('COMFYUI_STORAGE_PATH', '/opt/dreamcatcher/storage/visuals')
        self.output_dir = os.getenv('COMFYUI_OUTPUT_DIR', 'output')
        
        # Connection state
        self.is_connected = False
        self.last_health_check = None
        self.health_check_interval = 60  # seconds
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_generations': 0,
            'failed_generations': 0,
            'average_generation_time': 0.0,
            'connection_errors': 0
        }
        
        # Initialize storage directory
        self._ensure_storage_directory()
    
    def _ensure_storage_directory(self):
        """Ensure storage directory exists"""
        try:
            os.makedirs(self.storage_path, exist_ok=True)
            self.logger.info(f"Storage directory ready: {self.storage_path}")
        except Exception as e:
            self.logger.error(f"Failed to create storage directory: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check ComfyUI service health"""
        if not self.enabled:
            return {
                'status': 'disabled',
                'available': False,
                'message': 'ComfyUI service is disabled'
            }
        
        try:
            async with aiohttp.ClientSession() as session:
                # Check if ComfyUI is running
                async with session.get(f"{self.base_url}/system_stats", timeout=10) as response:
                    if response.status == 200:
                        stats = await response.json()
                        
                        # Check queue status
                        async with session.get(f"{self.base_url}/queue") as queue_response:
                            queue_info = await queue_response.json() if queue_response.status == 200 else {}
                        
                        self.is_connected = True
                        self.last_health_check = datetime.utcnow()
                        
                        return {
                            'status': 'healthy',
                            'available': True,
                            'url': self.base_url,
                            'system_stats': stats,
                            'queue_info': queue_info,
                            'last_check': self.last_health_check.isoformat()
                        }
                    else:
                        raise ComfyUIConnectionError(f"ComfyUI returned status {response.status}")
        
        except Exception as e:
            self.is_connected = False
            self.stats['connection_errors'] += 1
            self.logger.error(f"ComfyUI health check failed: {e}")
            
            return {
                'status': 'unhealthy',
                'available': False,
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }
    
    async def generate_image(
        self,
        workflow: Dict[str, Any],
        prompt_id: Optional[str] = None,
        priority: int = 0
    ) -> GenerationResult:
        """
        Generate image using ComfyUI workflow with comprehensive error handling
        """
        if not self.enabled:
            return GenerationResult(
                success=False,
                error="ComfyUI service is disabled"
            )
        
        start_time = time.time()
        self.stats['total_requests'] += 1
        
        # Validate workflow
        if not workflow or not isinstance(workflow, dict):
            return GenerationResult(
                success=False,
                error="Invalid workflow provided"
            )
        
        # Check service health
        health = await self.health_check()
        if not health['available']:
            return GenerationResult(
                success=False,
                error=f"ComfyUI service unavailable: {health.get('error', 'Unknown error')}"
            )
        
        # Attempt generation with retries
        for attempt in range(self.max_retries):
            try:
                result = await self._generate_with_retry(workflow, prompt_id, priority)
                
                if result.success:
                    execution_time = time.time() - start_time
                    result.execution_time = execution_time
                    
                    # Update statistics
                    self.stats['successful_generations'] += 1
                    self._update_average_time(execution_time)
                    
                    self.logger.info(f"Image generated successfully in {execution_time:.2f}s")
                    return result
                else:
                    # If specific error, don't retry
                    if "timeout" in result.error.lower():
                        raise ComfyUITimeoutError(result.error)
                    elif "connection" in result.error.lower():
                        raise ComfyUIConnectionError(result.error)
                    else:
                        raise ComfyUIGenerationError(result.error)
                        
            except (ComfyUITimeoutError, ComfyUIConnectionError) as e:
                if attempt == self.max_retries - 1:
                    self.stats['failed_generations'] += 1
                    return GenerationResult(
                        success=False,
                        error=f"Generation failed after {self.max_retries} attempts: {str(e)}"
                    )
                
                # Wait before retry
                await asyncio.sleep(self.retry_delay * (attempt + 1))
                self.logger.warning(f"Retrying generation (attempt {attempt + 1}/{self.max_retries})")
                
            except Exception as e:
                self.stats['failed_generations'] += 1
                self.logger.error(f"Generation failed: {e}")
                return GenerationResult(
                    success=False,
                    error=f"Generation error: {str(e)}"
                )
        
        # All retries failed
        self.stats['failed_generations'] += 1
        return GenerationResult(
            success=False,
            error=f"Generation failed after {self.max_retries} attempts"
        )
    
    async def _generate_with_retry(
        self,
        workflow: Dict[str, Any],
        prompt_id: Optional[str],
        priority: int
    ) -> GenerationResult:
        """Generate image with single attempt"""
        try:
            async with aiohttp.ClientSession() as session:
                # Queue the workflow
                queue_payload = {
                    "prompt": workflow,
                    "client_id": prompt_id or f"dreamcatcher_{int(time.time())}"
                }
                
                if priority > 0:
                    queue_payload["front"] = priority > 5
                
                async with session.post(
                    f"{self.base_url}/prompt",
                    json=queue_payload,
                    timeout=30
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ComfyUIGenerationError(f"Queue failed: {response.status} - {error_text}")
                    
                    queue_result = await response.json()
                    actual_prompt_id = queue_result.get('prompt_id')
                    
                    if not actual_prompt_id:
                        raise ComfyUIGenerationError("No prompt ID returned from queue")
                
                # Monitor execution progress
                result = await self._monitor_generation(actual_prompt_id, session)
                return result
                
        except asyncio.TimeoutError:
            raise ComfyUITimeoutError("Generation request timed out")
        except Exception as e:
            raise ComfyUIGenerationError(f"Generation failed: {str(e)}")
    
    async def _monitor_generation(self, prompt_id: str, session: aiohttp.ClientSession) -> GenerationResult:
        """Monitor generation progress using WebSocket or polling"""
        try:
            # Try WebSocket monitoring first
            try:
                return await self._monitor_via_websocket(prompt_id)
            except Exception as e:
                self.logger.warning(f"WebSocket monitoring failed, falling back to polling: {e}")
                return await self._monitor_via_polling(prompt_id, session)
                
        except Exception as e:
            raise ComfyUIGenerationError(f"Monitoring failed: {str(e)}")
    
    async def _monitor_via_websocket(self, prompt_id: str) -> GenerationResult:
        """Monitor generation via WebSocket"""
        try:
            async with websockets.connect(self.ws_url) as websocket:
                start_time = time.time()
                
                while time.time() - start_time < self.timeout:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        data = json.loads(message)
                        
                        # Check for completion
                        if data.get('type') == 'executing':
                            node_id = data.get('data', {}).get('node')
                            if node_id is None:  # Execution finished
                                return await self._get_generation_result(prompt_id)
                        
                        # Check for errors
                        elif data.get('type') == 'execution_error':
                            error_info = data.get('data', {})
                            raise ComfyUIGenerationError(f"Execution error: {error_info}")
                            
                    except asyncio.TimeoutError:
                        continue  # Continue monitoring
                    except websockets.exceptions.ConnectionClosed:
                        raise ComfyUIConnectionError("WebSocket connection closed")
                
                raise ComfyUITimeoutError(f"Generation timed out after {self.timeout}s")
                
        except Exception as e:
            raise ComfyUIConnectionError(f"WebSocket error: {str(e)}")
    
    async def _monitor_via_polling(self, prompt_id: str, session: aiohttp.ClientSession) -> GenerationResult:
        """Monitor generation via polling"""
        start_time = time.time()
        poll_interval = 2.0  # seconds
        
        while time.time() - start_time < self.timeout:
            try:
                async with session.get(f"{self.base_url}/queue") as response:
                    if response.status == 200:
                        queue_info = await response.json()
                        
                        # Check if prompt is still in queue
                        running = queue_info.get('queue_running', [])
                        pending = queue_info.get('queue_pending', [])
                        
                        prompt_in_queue = any(
                            item[1] == prompt_id for item in running + pending
                        )
                        
                        if not prompt_in_queue:
                            # Generation completed or failed
                            return await self._get_generation_result(prompt_id)
                
                await asyncio.sleep(poll_interval)
                
            except Exception as e:
                self.logger.warning(f"Polling error: {e}")
                await asyncio.sleep(poll_interval)
        
        raise ComfyUITimeoutError(f"Generation timed out after {self.timeout}s")
    
    async def _get_generation_result(self, prompt_id: str) -> GenerationResult:
        """Get the final generation result"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/history/{prompt_id}") as response:
                    if response.status != 200:
                        raise ComfyUIGenerationError(f"Failed to get history: {response.status}")
                    
                    history = await response.json()
                    
                    if prompt_id not in history:
                        raise ComfyUIGenerationError("Generation result not found in history")
                    
                    result_data = history[prompt_id]
                    
                    # Check for errors
                    if result_data.get('status', {}).get('status_str') == 'error':
                        error_info = result_data.get('status', {})
                        raise ComfyUIGenerationError(f"Generation error: {error_info}")
                    
                    # Extract image information
                    outputs = result_data.get('outputs', {})
                    
                    # Look for SaveImage node output (typically node 5)
                    for node_id, node_output in outputs.items():
                        if 'images' in node_output:
                            images = node_output['images']
                            if images:
                                image_info = images[0]
                                filename = image_info.get('filename')
                                
                                if filename:
                                    # Construct full path
                                    image_path = os.path.join(self.storage_path, filename)
                                    
                                    return GenerationResult(
                                        success=True,
                                        image_path=image_path,
                                        filename=filename,
                                        prompt_id=prompt_id
                                    )
                    
                    raise ComfyUIGenerationError("No image output found in generation result")
                    
        except Exception as e:
            raise ComfyUIGenerationError(f"Failed to get result: {str(e)}")
    
    def _update_average_time(self, execution_time: float):
        """Update average generation time"""
        current_avg = self.stats['average_generation_time']
        successful_count = self.stats['successful_generations']
        
        if successful_count == 1:
            self.stats['average_generation_time'] = execution_time
        else:
            # Calculate weighted average
            self.stats['average_generation_time'] = (
                (current_avg * (successful_count - 1) + execution_time) / successful_count
            )
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/queue") as response:
                    if response.status == 200:
                        queue_info = await response.json()
                        return {
                            'success': True,
                            'running': len(queue_info.get('queue_running', [])),
                            'pending': len(queue_info.get('queue_pending', [])),
                            'queue_info': queue_info
                        }
                    else:
                        return {
                            'success': False,
                            'error': f"Failed to get queue status: {response.status}"
                        }
        except Exception as e:
            return {
                'success': False,
                'error': f"Queue status error: {str(e)}"
            }
    
    async def cancel_generation(self, prompt_id: str) -> Dict[str, Any]:
        """Cancel a queued generation"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/queue",
                    json={"delete": [prompt_id]}
                ) as response:
                    if response.status == 200:
                        return {
                            'success': True,
                            'message': f"Generation {prompt_id} cancelled"
                        }
                    else:
                        return {
                            'success': False,
                            'error': f"Failed to cancel: {response.status}"
                        }
        except Exception as e:
            return {
                'success': False,
                'error': f"Cancel error: {str(e)}"
            }
    
    async def get_available_models(self) -> List[str]:
        """Get available models from ComfyUI"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/object_info") as response:
                    if response.status == 200:
                        object_info = await response.json()
                        
                        # Extract checkpoint models
                        models = []
                        checkpoint_loader = object_info.get('CheckpointLoaderSimple', {})
                        inputs = checkpoint_loader.get('input', {})
                        
                        if 'ckpt_name' in inputs:
                            models = inputs['ckpt_name'][0]  # First element is the list
                        
                        return models
                    else:
                        self.logger.error(f"Failed to get models: {response.status}")
                        return []
        except Exception as e:
            self.logger.error(f"Error getting models: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics"""
        stats = self.stats.copy()
        
        # Add calculated metrics
        if stats['total_requests'] > 0:
            stats['success_rate'] = stats['successful_generations'] / stats['total_requests']
            stats['failure_rate'] = stats['failed_generations'] / stats['total_requests']
        else:
            stats['success_rate'] = 0.0
            stats['failure_rate'] = 0.0
        
        stats['service_enabled'] = self.enabled
        stats['service_url'] = self.base_url
        stats['is_connected'] = self.is_connected
        stats['last_health_check'] = self.last_health_check.isoformat() if self.last_health_check else None
        
        return stats
    
    def create_basic_workflow(
        self,
        positive_prompt: str,
        negative_prompt: str = "",
        model: str = "sd_xl_base_1.0.safetensors",
        width: int = 1024,
        height: int = 1024,
        steps: int = 20,
        cfg_scale: float = 7.0,
        sampler: str = "euler",
        scheduler: str = "normal",
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a basic workflow with common parameters"""
        
        if seed is None:
            seed = int(time.time()) % 1000000
        
        workflow = {
            "1": {
                "inputs": {
                    "ckpt_name": model
                },
                "class_type": "CheckpointLoaderSimple"
            },
            "2": {
                "inputs": {
                    "width": width,
                    "height": height,
                    "batch_size": 1
                },
                "class_type": "EmptyLatentImage"
            },
            "3": {
                "inputs": {
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg_scale,
                    "sampler_name": sampler,
                    "scheduler": scheduler,
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
                    "filename_prefix": f"dreamcatcher_{int(time.time())}",
                    "images": ["4", 0]
                },
                "class_type": "SaveImage"
            },
            "6": {
                "inputs": {
                    "text": positive_prompt,
                    "clip": ["1", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            "7": {
                "inputs": {
                    "text": negative_prompt,
                    "clip": ["1", 1]
                },
                "class_type": "CLIPTextEncode"
            }
        }
        
        return workflow