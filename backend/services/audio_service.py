import os
import tempfile
import asyncio
import logging
from typing import Optional, Dict, Any
import wave
import json

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import webrtcvad
    VAD_AVAILABLE = True
except ImportError:
    VAD_AVAILABLE = False

class AudioProcessor:
    """
    Service for processing audio input from various sources
    Handles voice activity detection, noise reduction, and format conversion
    """
    
    def __init__(self):
        self.logger = logging.getLogger("audio_processor")
        
        # Configuration
        self.sample_rate = 16000  # Standard for speech recognition
        self.chunk_duration = 0.02  # 20ms chunks
        self.vad_mode = 2  # Aggressiveness (0-3)
        
        # Initialize VAD if available
        self.vad = None
        if VAD_AVAILABLE:
            try:
                self.vad = webrtcvad.Vad(self.vad_mode)
                self.logger.info("Voice Activity Detection initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize VAD: {e}")
    
    async def process_audio_file(self, file_path: str) -> Dict[str, Any]:
        """Process an audio file and return metadata"""
        try:
            if not os.path.exists(file_path):
                return {'error': f'Audio file not found: {file_path}'}
            
            # Get audio info
            audio_info = await self._get_audio_info(file_path)
            
            # Detect speech segments if VAD is available
            speech_segments = []
            if self.vad and NUMPY_AVAILABLE:
                speech_segments = await self._detect_speech_segments(file_path)
            
            # Calculate audio quality metrics
            quality_metrics = await self._calculate_quality_metrics(file_path)
            
            return {
                'file_path': file_path,
                'audio_info': audio_info,
                'speech_segments': speech_segments,
                'quality_metrics': quality_metrics,
                'processed_at': asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            self.logger.error(f"Error processing audio file {file_path}: {e}")
            return {'error': f'Audio processing failed: {str(e)}'}
    
    async def process_audio_data(self, audio_data: bytes, format_hint: str = 'wav') -> Dict[str, Any]:
        """Process raw audio data"""
        try:
            # Write to temporary file
            with tempfile.NamedTemporaryFile(suffix=f'.{format_hint}', delete=False) as tmp_file:
                tmp_file.write(audio_data)
                tmp_file.flush()
                
                # Process the temporary file
                result = await self.process_audio_file(tmp_file.name)
                
                # Clean up
                os.unlink(tmp_file.name)
                
                return result
                
        except Exception as e:
            self.logger.error(f"Error processing audio data: {e}")
            return {'error': f'Audio data processing failed: {str(e)}'}
    
    async def _get_audio_info(self, file_path: str) -> Dict[str, Any]:
        """Get basic audio file information"""
        try:
            # Try to read as WAV file first
            with wave.open(file_path, 'rb') as wav_file:
                frames = wav_file.getnframes()
                sample_rate = wav_file.getframerate()
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                duration = frames / sample_rate
                
                return {
                    'format': 'wav',
                    'duration': duration,
                    'sample_rate': sample_rate,
                    'channels': channels,
                    'sample_width': sample_width,
                    'frames': frames
                }
        except Exception as e:
            self.logger.error(f"Failed to read audio info: {e}")
            return {
                'format': 'unknown',
                'duration': 0,
                'sample_rate': 0,
                'channels': 0,
                'error': str(e)
            }
    
    async def _detect_speech_segments(self, file_path: str) -> list:
        """Detect speech segments using VAD"""
        if not self.vad or not NUMPY_AVAILABLE:
            return []
        
        try:
            speech_segments = []
            
            with wave.open(file_path, 'rb') as wav_file:
                sample_rate = wav_file.getframerate()
                
                # VAD works best with 16kHz
                if sample_rate not in [8000, 16000, 32000, 48000]:
                    self.logger.warning(f"Unsupported sample rate for VAD: {sample_rate}")
                    return []
                
                # Read audio data
                frames = wav_file.readframes(wav_file.getnframes())
                
                # Convert to numpy array
                audio_data = np.frombuffer(frames, dtype=np.int16)
                
                # Process in chunks
                chunk_size = int(sample_rate * self.chunk_duration)
                current_segment = None
                
                for i in range(0, len(audio_data), chunk_size):
                    chunk = audio_data[i:i + chunk_size]
                    
                    # Ensure chunk is the right size
                    if len(chunk) < chunk_size:
                        chunk = np.pad(chunk, (0, chunk_size - len(chunk)))
                    
                    # Convert to bytes
                    chunk_bytes = chunk.tobytes()
                    
                    # Check if speech is detected
                    is_speech = self.vad.is_speech(chunk_bytes, sample_rate)
                    
                    timestamp = i / sample_rate
                    
                    if is_speech:
                        if current_segment is None:
                            current_segment = {'start': timestamp, 'end': timestamp}
                        else:
                            current_segment['end'] = timestamp
                    else:
                        if current_segment is not None:
                            speech_segments.append(current_segment)
                            current_segment = None
                
                # Close any remaining segment
                if current_segment is not None:
                    speech_segments.append(current_segment)
            
            return speech_segments
            
        except Exception as e:
            self.logger.error(f"Speech detection failed: {e}")
            return []
    
    async def _calculate_quality_metrics(self, file_path: str) -> Dict[str, Any]:
        """Calculate audio quality metrics"""
        try:
            with wave.open(file_path, 'rb') as wav_file:
                frames = wav_file.readframes(wav_file.getnframes())
                sample_rate = wav_file.getframerate()
                
                if not NUMPY_AVAILABLE:
                    return {'error': 'NumPy not available for quality analysis'}
                
                # Convert to numpy array
                audio_data = np.frombuffer(frames, dtype=np.int16)
                
                # Calculate RMS (Root Mean Square) for volume
                rms = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
                
                # Calculate signal-to-noise ratio estimate
                # This is a simplified approach
                sorted_data = np.sort(np.abs(audio_data))
                noise_floor = np.mean(sorted_data[:len(sorted_data) // 10])  # Bottom 10%
                signal_peak = np.mean(sorted_data[-len(sorted_data) // 10:])  # Top 10%
                
                snr_estimate = 20 * np.log10(signal_peak / max(noise_floor, 1))
                
                # Calculate clipping detection
                max_value = np.max(np.abs(audio_data))
                clipping_ratio = np.sum(np.abs(audio_data) == max_value) / len(audio_data)
                
                # Calculate silence ratio
                silence_threshold = rms * 0.1
                silence_ratio = np.sum(np.abs(audio_data) < silence_threshold) / len(audio_data)
                
                return {
                    'rms_level': float(rms),
                    'snr_estimate': float(snr_estimate),
                    'clipping_ratio': float(clipping_ratio),
                    'silence_ratio': float(silence_ratio),
                    'quality_score': self._calculate_quality_score(rms, snr_estimate, clipping_ratio, silence_ratio)
                }
                
        except Exception as e:
            self.logger.error(f"Quality metrics calculation failed: {e}")
            return {'error': f'Quality analysis failed: {str(e)}'}
    
    def _calculate_quality_score(self, rms: float, snr: float, clipping: float, silence: float) -> float:
        """Calculate overall quality score (0-100)"""
        try:
            score = 100.0
            
            # Penalize low volume
            if rms < 100:
                score -= 20
            
            # Penalize poor SNR
            if snr < 10:
                score -= 30
            elif snr < 20:
                score -= 15
            
            # Penalize clipping
            if clipping > 0.01:  # More than 1% clipping
                score -= 25
            
            # Penalize too much silence
            if silence > 0.5:  # More than 50% silence
                score -= 15
            
            return max(0.0, min(100.0, score))
            
        except Exception:
            return 50.0  # Default score if calculation fails
    
    async def convert_to_standard_format(self, input_path: str, output_path: Optional[str] = None) -> str:
        """Convert audio to standard format for processing"""
        try:
            if not output_path:
                output_path = input_path.replace('.', '_converted.')
            
            # For now, just copy the file
            # In a real implementation, you'd use ffmpeg or similar
            import shutil
            shutil.copy2(input_path, output_path)
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Audio conversion failed: {e}")
            return input_path
    
    async def enhance_audio(self, file_path: str) -> str:
        """Apply audio enhancement (noise reduction, normalization)"""
        try:
            # This is a placeholder for audio enhancement
            # In a real implementation, you'd use librosa, noisereduce, etc.
            
            self.logger.info(f"Audio enhancement requested for {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"Audio enhancement failed: {e}")
            return file_path
    
    def get_supported_formats(self) -> list:
        """Get list of supported audio formats"""
        return ['wav', 'mp3', 'ogg', 'flac', 'm4a', 'webm']
    
    def validate_audio_file(self, file_path: str) -> Dict[str, Any]:
        """Validate audio file format and quality"""
        try:
            if not os.path.exists(file_path):
                return {'valid': False, 'error': 'File not found'}
            
            # Check file extension
            ext = os.path.splitext(file_path)[1].lower().lstrip('.')
            if ext not in self.get_supported_formats():
                return {'valid': False, 'error': f'Unsupported format: {ext}'}
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return {'valid': False, 'error': 'Empty file'}
            
            if file_size > 100 * 1024 * 1024:  # 100MB limit
                return {'valid': False, 'error': 'File too large'}
            
            # Try to read audio info
            audio_info = asyncio.run(self._get_audio_info(file_path))
            if 'error' in audio_info:
                return {'valid': False, 'error': audio_info['error']}
            
            return {
                'valid': True,
                'format': ext,
                'size': file_size,
                'duration': audio_info.get('duration', 0),
                'sample_rate': audio_info.get('sample_rate', 0)
            }
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}