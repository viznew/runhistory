import os
import uuid
import aiohttp
import asyncio
from pathlib import Path
from typing import List, Union
import logging

logger = logging.getLogger(__name__)

class FileManager:
    def __init__(self, base_dir: str = "generated"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
    
    def generate_session_id(self) -> str:
        """Generate unique session ID"""
        return str(uuid.uuid4())
    
    def create_session_directory(self, session_id: str) -> Path:
        """Create directory for session files"""
        session_dir = self.base_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir
    
    async def download_image(self, url: str, directory: Path, filename: str) -> Path:
        """Download image from URL"""
        image_path = directory / filename
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        # Save image
                        with open(image_path, 'wb') as f:
                            f.write(content)
                        
                        logger.info(f"Downloaded image: {image_path}")
                        return image_path
                    else:
                        raise Exception(f"Failed to download image: HTTP {response.status}")
        except Exception as e:
            logger.error(f"Error downloading image: {str(e)}")
            raise
    
    async def download_images(self, urls: List[str], directory: Path) -> List[Path]:
        """Download multiple images concurrently"""
        tasks = []
        
        for i, url in enumerate(urls):
            filename = f"image_{i+1:02d}.png"
            task = asyncio.create_task(self.download_image(url, directory, filename))
            tasks.append(task)
        
        try:
            image_paths = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions
            valid_paths = []
            for i, result in enumerate(image_paths):
                if isinstance(result, Exception):
                    logger.error(f"Failed to download image {i+1}: {str(result)}")
                    continue
                valid_paths.append(result)
            
            return valid_paths
            
        except Exception as e:
            logger.error(f"Error downloading images: {str(e)}")
            return []
    
    def save_text_file(self, content: str, path: Union[str, Path]) -> Path:
        """Save text content to file"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Saved text file: {path}")
        return path
    
    def get_session_files(self, session_id: str) -> dict:
        """Get all files for a session"""
        session_dir = self.base_dir / session_id
        
        if not session_dir.exists():
            return {}
        
        files = {
            'script': None,
            'voiceover': None,
            'images': [],
            'video': None
        }
        
        # Check for script
        script_path = session_dir / "script.txt"
        if script_path.exists():
            files['script'] = script_path
        
        # Check for voiceover
        voiceover_path = session_dir / "voiceover.mp3"
        if voiceover_path.exists():
            files['voiceover'] = voiceover_path
        
        # Check for images
        for img_file in session_dir.glob("image_*.png"):
            files['images'].append(img_file)
        
        # Sort images by number
        files['images'].sort()
        
        # Check for video
        video_path = session_dir / "final_video.mp4"
        if video_path.exists():
            files['video'] = video_path
        
        return files
    
    def cleanup_session(self, session_id: str) -> bool:
        """Clean up session files"""
        session_dir = self.base_dir / session_id
        
        if not session_dir.exists():
            return False
        
        try:
            # Remove all files in session directory
            for file_path in session_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
            
            # Remove directory
            session_dir.rmdir()
            
            logger.info(f"Cleaned up session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up session {session_id}: {str(e)}")
            return False
    
    def get_file_size(self, path: Union[str, Path]) -> int:
        """Get file size in bytes"""
        path = Path(path)
        if path.exists():
            return path.stat().st_size
        return 0
    
    def ensure_directory(self, path: Union[str, Path]) -> Path:
        """Ensure directory exists"""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path
