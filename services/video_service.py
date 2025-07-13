import os
import asyncio
import logging
from pathlib import Path
from typing import List, Union
import subprocess
import json

logger = logging.getLogger(__name__)

class VideoService:
    def __init__(self):
        self.ffmpeg_path = "ffmpeg"  # Assume ffmpeg is in PATH
        
    async def create_video(
        self,
        image_paths: List[Path],
        voiceover_path: Path,
        output_path: Union[str, Path],
        script_duration: int = 60
    ) -> Path:
        """Create video from images and voiceover"""
        output_path = Path(output_path)
        
        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Get audio duration
            audio_duration = await self._get_audio_duration(voiceover_path)
            logger.info(f"Audio duration: {audio_duration} seconds")
            
            # Calculate image duration
            if len(image_paths) > 0:
                image_duration = audio_duration / len(image_paths)
            else:
                raise Exception("No images provided for video creation")
            
            # Create video with images and audio
            await self._create_video_with_ffmpeg(
                image_paths=image_paths,
                voiceover_path=voiceover_path,
                output_path=output_path,
                image_duration=image_duration,
                audio_duration=audio_duration
            )
            
            logger.info(f"Video created successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating video: {str(e)}")
            raise Exception(f"Failed to create video: {str(e)}")
    
    async def _get_audio_duration(self, audio_path: Path) -> float:
        """Get duration of audio file"""
        try:
            cmd = [
                self.ffmpeg_path, "-i", str(audio_path),
                "-f", "null", "-",
                "-hide_banner", "-loglevel", "error"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                # Try alternative method with ffprobe
                return await self._get_duration_with_ffprobe(audio_path)
            
            # Parse duration from stderr
            stderr_str = stderr.decode('utf-8')
            for line in stderr_str.split('\n'):
                if 'time=' in line:
                    time_part = line.split('time=')[1].split(' ')[0]
                    # Parse time format HH:MM:SS.ss
                    time_parts = time_part.split(':')
                    if len(time_parts) == 3:
                        hours = float(time_parts[0])
                        minutes = float(time_parts[1])
                        seconds = float(time_parts[2])
                        return hours * 3600 + minutes * 60 + seconds
            
            # Default duration if parsing fails
            return 60.0
            
        except Exception as e:
            logger.error(f"Error getting audio duration: {str(e)}")
            return 60.0  # Default duration
    
    async def _get_duration_with_ffprobe(self, audio_path: Path) -> float:
        """Get duration using ffprobe"""
        try:
            cmd = [
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_format", str(audio_path)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                data = json.loads(stdout.decode('utf-8'))
                duration = float(data['format']['duration'])
                return duration
            else:
                return 60.0  # Default
                
        except Exception as e:
            logger.error(f"Error with ffprobe: {str(e)}")
            return 60.0
    
    async def _create_video_with_ffmpeg(
        self,
        image_paths: List[Path],
        voiceover_path: Path,
        output_path: Path,
        image_duration: float,
        audio_duration: float
    ):
        """Create video using FFmpeg"""
        try:
            # Create a temporary file list for FFmpeg
            temp_list_path = output_path.parent / "temp_images.txt"
            
            with open(temp_list_path, 'w') as f:
                for img_path in image_paths:
                    f.write(f"file '{img_path.absolute()}'\n")
                    f.write(f"duration {image_duration}\n")
                # Add last image again for proper ending
                if image_paths:
                    f.write(f"file '{image_paths[-1].absolute()}'\n")
            
            # FFmpeg command with effects
            cmd = [
                self.ffmpeg_path,
                "-f", "concat",
                "-safe", "0",
                "-i", str(temp_list_path),
                "-i", str(voiceover_path),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "128k",
                "-vf", self._get_video_filters(),
                "-shortest",
                "-y",
                str(output_path)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                stderr_str = stderr.decode('utf-8')
                logger.error(f"FFmpeg error: {stderr_str}")
                raise Exception(f"FFmpeg failed: {stderr_str}")
            
            # Clean up temp file
            if temp_list_path.exists():
                temp_list_path.unlink()
            
        except Exception as e:
            logger.error(f"Error creating video with FFmpeg: {str(e)}")
            raise
    
    def _get_video_filters(self) -> str:
        """Get video filters for effects"""
        filters = []
        
        # Scale and crop to ensure consistent size
        filters.append("scale=1920:1080:force_original_aspect_ratio=increase")
        filters.append("crop=1920:1080")
        
        # Add subtle zoom effect
        filters.append("zoompan=z='min(zoom+0.0005,1.1)':d=125:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'")
        
        # Add scanlines effect
        filters.append("format=yuv420p")
        
        # Add slight color correction for cinematic look
        filters.append("eq=contrast=1.1:brightness=0.02:saturation=1.1")
        
        return ",".join(filters)
    
    async def add_subtitles(self, video_path: Path, subtitle_text: str, output_path: Path) -> Path:
        """Add subtitles to video"""
        try:
            # Create temporary subtitle file
            srt_path = video_path.parent / "temp_subtitles.srt"
            
            # Simple SRT format
            with open(srt_path, 'w') as f:
                f.write("1\n")
                f.write("00:00:00,000 --> 00:01:20,000\n")
                f.write(f"{subtitle_text}\n")
            
            cmd = [
                self.ffmpeg_path,
                "-i", str(video_path),
                "-vf", f"subtitles={srt_path}",
                "-c:a", "copy",
                "-y",
                str(output_path)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                stderr_str = stderr.decode('utf-8')
                raise Exception(f"FFmpeg subtitle error: {stderr_str}")
            
            # Clean up temp file
            if srt_path.exists():
                srt_path.unlink()
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error adding subtitles: {str(e)}")
            raise
