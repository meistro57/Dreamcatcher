import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime
import whisper
import tempfile
import os

from .base_agent import BaseAgent
from ..database import get_db, IdeaCRUD, TagCRUD
from ..services.audio_service import AudioProcessor

class AgentListener(BaseAgent):
    """
    Agent responsible for capturing and processing raw input from users.
    Handles voice, text, and other input types with minimal friction.
    """
    
    def __init__(self):
        super().__init__(
            agent_id="listener",
            name="Capture Agent",
            description="I heard something. Logging it now.",
            version="1.0.0"
        )
        
        # Initialize audio processor
        self.audio_processor = AudioProcessor()
        
        # Initialize Whisper model for transcription
        self.whisper_model = None
        self._initialize_whisper()
    
    def _initialize_whisper(self):
        """Initialize Whisper model for voice transcription"""
        try:
            model_size = self.config.get('whisper_model', 'base')
            self.whisper_model = whisper.load_model(model_size)
            self.logger.info(f"Whisper model '{model_size}' loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load Whisper model: {e}")
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming capture request"""
        input_type = data.get('type', 'unknown')
        
        if input_type == 'voice':
            return await self._process_voice(data)
        elif input_type == 'text':
            return await self._process_text(data)
        elif input_type == 'dream':
            return await self._process_dream(data)
        elif input_type == 'image':
            return await self._process_image(data)
        else:
            self.logger.warning(f"Unknown input type: {input_type}")
            return {'error': f'Unsupported input type: {input_type}'}
    
    async def _process_voice(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process voice input"""
        try:
            audio_data = data.get('audio_data')
            audio_file = data.get('audio_file')
            device_info = data.get('device_info', {})
            location_data = data.get('location_data', {})
            
            if not audio_data and not audio_file:
                return {'error': 'No audio data provided'}
            
            # Transcribe audio
            transcription = await self._transcribe_audio(audio_data or audio_file)
            
            if not transcription or not transcription.strip():
                return {'error': 'Failed to transcribe audio or audio was empty'}
            
            # Create idea in database
            with get_db() as db:
                idea = IdeaCRUD.create_idea(
                    db=db,
                    content=transcription,
                    source_type='voice',
                    content_transcribed=transcription,
                    device_info=device_info,
                    location_data=location_data
                )
                
                # Auto-tag based on content
                await self._auto_tag_idea(db, idea.id, transcription)
            
            # Trigger downstream processing
            await self._trigger_processing(idea.id, transcription)
            
            return {
                'success': True,
                'idea_id': idea.id,
                'transcription': transcription,
                'message': 'Voice captured and transcribed successfully'
            }
            
        except Exception as e:
            self.logger.error(f"Error processing voice input: {e}")
            return {'error': f'Failed to process voice input: {str(e)}'}
    
    async def _process_text(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process text input"""
        try:
            content = data.get('content', '').strip()
            device_info = data.get('device_info', {})
            location_data = data.get('location_data', {})
            urgency_hint = data.get('urgency', 'normal')
            
            if not content:
                return {'error': 'No text content provided'}
            
            # Determine initial urgency score based on hint and content
            urgency_score = self._calculate_urgency_score(content, urgency_hint)
            
            # Create idea in database
            with get_db() as db:
                idea = IdeaCRUD.create_idea(
                    db=db,
                    content=content,
                    source_type='text',
                    content_transcribed=content,
                    device_info=device_info,
                    location_data=location_data,
                    urgency_score=urgency_score
                )
                
                # Auto-tag based on content
                await self._auto_tag_idea(db, idea.id, content)
            
            # Trigger downstream processing
            await self._trigger_processing(idea.id, content)
            
            return {
                'success': True,
                'idea_id': idea.id,
                'content': content,
                'urgency_score': urgency_score,
                'message': 'Text captured successfully'
            }
            
        except Exception as e:
            self.logger.error(f"Error processing text input: {e}")
            return {'error': f'Failed to process text input: {str(e)}'}
    
    async def _process_dream(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process dream log input"""
        try:
            content = data.get('content', '').strip()
            dream_type = data.get('dream_type', 'regular')  # 'regular', 'lucid', 'nightmare'
            sleep_stage = data.get('sleep_stage', 'unknown')
            
            if not content:
                return {'error': 'No dream content provided'}
            
            # Dreams get special handling
            with get_db() as db:
                idea = IdeaCRUD.create_idea(
                    db=db,
                    content=content,
                    source_type='dream',
                    content_transcribed=content,
                    category='metaphysical',
                    urgency_score=30.0,  # Dreams start with lower urgency
                    device_info={'dream_type': dream_type, 'sleep_stage': sleep_stage}
                )
                
                # Auto-tag dreams
                await self._auto_tag_dream(db, idea.id, content, dream_type)
            
            # Trigger dream-specific processing
            await self._trigger_dream_processing(idea.id, content, dream_type)
            
            return {
                'success': True,
                'idea_id': idea.id,
                'content': content,
                'dream_type': dream_type,
                'message': 'Dream logged successfully'
            }
            
        except Exception as e:
            self.logger.error(f"Error processing dream input: {e}")
            return {'error': f'Failed to process dream input: {str(e)}'}
    
    async def _process_image(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process image input with optional text description"""
        try:
            image_path = data.get('image_path')
            description = data.get('description', '').strip()
            
            if not image_path:
                return {'error': 'No image path provided'}
            
            # For now, we'll just store the image reference
            # Future: OCR, image analysis, etc.
            with get_db() as db:
                idea = IdeaCRUD.create_idea(
                    db=db,
                    content=description or f"Image uploaded: {os.path.basename(image_path)}",
                    source_type='image',
                    content_transcribed=description,
                    device_info={'image_path': image_path}
                )
            
            return {
                'success': True,
                'idea_id': idea.id,
                'image_path': image_path,
                'message': 'Image captured successfully'
            }
            
        except Exception as e:
            self.logger.error(f"Error processing image input: {e}")
            return {'error': f'Failed to process image input: {str(e)}'}
    
    async def _transcribe_audio(self, audio_data) -> str:
        """Transcribe audio using Whisper"""
        try:
            if not self.whisper_model:
                return ""
            
            # If audio_data is a file path, use it directly
            if isinstance(audio_data, str) and os.path.exists(audio_data):
                result = self.whisper_model.transcribe(audio_data)
                return result['text'].strip()
            
            # If audio_data is bytes, write to temp file
            elif isinstance(audio_data, bytes):
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                    tmp_file.write(audio_data)
                    tmp_file.flush()
                    
                    result = self.whisper_model.transcribe(tmp_file.name)
                    os.unlink(tmp_file.name)  # Clean up
                    return result['text'].strip()
            
            else:
                self.logger.error("Invalid audio data format")
                return ""
                
        except Exception as e:
            self.logger.error(f"Transcription failed: {e}")
            return ""
    
    def _calculate_urgency_score(self, content: str, urgency_hint: str) -> float:
        """Calculate urgency score based on content and hint"""
        base_score = 50.0
        
        # Adjust based on hint
        urgency_multipliers = {
            'low': 0.5,
            'normal': 1.0,
            'high': 1.5,
            'urgent': 2.0,
            'emergency': 3.0
        }
        
        multiplier = urgency_multipliers.get(urgency_hint, 1.0)
        
        # Adjust based on content keywords
        urgent_keywords = ['urgent', 'asap', 'immediately', 'emergency', 'critical', 'important']
        excitement_keywords = ['amazing', 'brilliant', 'genius', 'perfect', 'incredible', 'holy shit']
        
        for keyword in urgent_keywords:
            if keyword.lower() in content.lower():
                multiplier *= 1.3
        
        for keyword in excitement_keywords:
            if keyword.lower() in content.lower():
                multiplier *= 1.2
        
        # Cap at 100
        return min(base_score * multiplier, 100.0)
    
    async def _auto_tag_idea(self, db, idea_id: str, content: str):
        """Auto-tag idea based on content"""
        try:
            # Simple keyword-based tagging
            tag_keywords = {
                'app': ['app', 'application', 'mobile', 'software'],
                'business': ['business', 'startup', 'money', 'revenue', 'product'],
                'creative': ['art', 'design', 'creative', 'story', 'music'],
                'tech': ['ai', 'tech', 'code', 'programming', 'algorithm'],
                'spiritual': ['spiritual', 'meditation', 'consciousness', 'awakening'],
                'dream': ['dream', 'sleep', 'lucid', 'nightmare'],
                'urgent': ['urgent', 'asap', 'important', 'critical']
            }
            
            content_lower = content.lower()
            
            for tag_name, keywords in tag_keywords.items():
                if any(keyword in content_lower for keyword in keywords):
                    tag = TagCRUD.get_or_create_tag(db, tag_name)
                    # Associate tag with idea (simplified - would need proper many-to-many handling)
                    
        except Exception as e:
            self.logger.error(f"Auto-tagging failed: {e}")
    
    async def _auto_tag_dream(self, db, idea_id: str, content: str, dream_type: str):
        """Auto-tag dream with dream-specific tags"""
        try:
            # Always tag as dream
            dream_tag = TagCRUD.get_or_create_tag(db, 'dream')
            
            # Tag by dream type
            if dream_type != 'regular':
                type_tag = TagCRUD.get_or_create_tag(db, dream_type)
            
            # Look for metaphysical elements
            metaphysical_keywords = ['spirit', 'vision', 'prophecy', 'symbol', 'message']
            if any(keyword in content.lower() for keyword in metaphysical_keywords):
                meta_tag = TagCRUD.get_or_create_tag(db, 'metaphysical')
                
        except Exception as e:
            self.logger.error(f"Dream auto-tagging failed: {e}")
    
    async def _trigger_processing(self, idea_id: str, content: str):
        """Trigger downstream processing for the captured idea"""
        try:
            # Send message to classifier agent
            await self.send_message(
                recipient="classifier",
                action="classify_idea",
                data={
                    'idea_id': idea_id,
                    'content': content
                }
            )
            
            self.logger.info(f"Triggered processing for idea {idea_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to trigger processing: {e}")
    
    async def _trigger_dream_processing(self, idea_id: str, content: str, dream_type: str):
        """Trigger dream-specific processing"""
        try:
            # Send to dream analyzer agent (if exists)
            await self.send_message(
                recipient="dream_analyzer",
                action="analyze_dream",
                data={
                    'idea_id': idea_id,
                    'content': content,
                    'dream_type': dream_type
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to trigger dream processing: {e}")