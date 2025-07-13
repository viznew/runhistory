import os
import aiohttp
import asyncio
import logging
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)

class ElevenLabsService:
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            logger.warning("ELEVENLABS_API_KEY not found, will try TTSMaker as fallback")
        
        self.base_url = "https://api.elevenlabs.io/v1"
        self.voice_id = "21m00Tcm4TlvDq8ikWAM"  # Default voice ID
        
    async def generate_voiceover(self, text: str, output_path: Union[str, Path]) -> Path:
        """Generate voiceover audio from text"""
        output_path = Path(output_path)
        
        try:
            if self.api_key:
                return await self._generate_with_elevenlabs(text, output_path)
            else:
                return await self._generate_with_ttsmaker(text, output_path)
                
        except Exception as e:
            logger.error(f"Error generating voiceover: {str(e)}")
            # Fallback to TTSMaker if ElevenLabs fails
            if self.api_key:
                logger.info("Falling back to TTSMaker...")
                return await self._generate_with_ttsmaker(text, output_path)
            else:
                raise Exception(f"Failed to generate voiceover: {str(e)}")
    
    async def _generate_with_elevenlabs(self, text: str, output_path: Path) -> Path:
        """Generate voiceover using ElevenLabs API"""
        url = f"{self.base_url}/text-to-speech/{self.voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.8,
                "style": 0.0,
                "use_speaker_boost": True
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers) as response:
                if response.status == 200:
                    content = await response.read()
                    
                    # Save the audio file
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, 'wb') as f:
                        f.write(content)
                    
                    logger.info(f"Generated voiceover with ElevenLabs: {output_path}")
                    return output_path
                else:
                    error_text = await response.text()
                    raise Exception(f"ElevenLabs API error {response.status}: {error_text}")
    
    async def _generate_with_ttsmaker(self, text: str, output_path: Path) -> Path:
        """Generate voiceover using edge-tts (Microsoft Edge TTS) as fallback"""
        try:
            # Try using a different approach - directly use edge-tts if available
            import subprocess
            import tempfile
            
            # Create a temporary SSML file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(text)
                temp_text_file = f.name
            
            # Use edge-tts command line tool
            cmd = [
                'edge-tts',
                '--text', text,
                '--write-media', str(output_path),
                '--voice', 'en-US-JennyNeural'
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    logger.info(f"Generated voiceover with edge-tts: {output_path}")
                    return output_path
                else:
                    logger.error(f"edge-tts error: {result.stderr}")
                    raise Exception(f"edge-tts failed: {result.stderr}")
            except FileNotFoundError:
                # edge-tts not available, try a simpler approach
                logger.warning("edge-tts not available, using text-to-silence fallback")
                return await self._generate_silence_with_text(text, output_path)
            except subprocess.TimeoutExpired:
                raise Exception("TTS generation timed out")
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_text_file)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Error with edge-tts: {str(e)}")
            # Final fallback - create a silent audio file with text overlay
            return await self._generate_silence_with_text(text, output_path)
    
    async def _generate_silence_with_text(self, text: str, output_path: Path) -> Path:
        """Generate a silent audio file as final fallback"""
        try:
            import subprocess
            
            # Calculate duration based on text length (average reading speed)
            words = len(text.split())
            duration = max(10, words * 0.4)  # ~150 words per minute
            
            # Generate silent audio with ffmpeg
            cmd = [
                'ffmpeg',
                '-f', 'lavfi',
                '-i', f'anullsrc=channel_layout=stereo:sample_rate=44100',
                '-t', str(duration),
                '-acodec', 'mp3',
                '-y',
                str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                logger.info(f"Generated silent audio placeholder: {output_path}")
                return output_path
            else:
                raise Exception(f"FFmpeg error: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Error generating silent audio: {str(e)}")
            raise Exception(f"Failed to generate audio fallback: {str(e)}")
    
    async def get_available_voices(self) -> list:
        """Get available voices from ElevenLabs"""
        if not self.api_key:
            return []
        
        url = f"{self.base_url}/voices"
        headers = {"xi-api-key": self.api_key}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("voices", [])
                    else:
                        logger.error(f"Failed to get voices: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error getting voices: {str(e)}")
            return []
