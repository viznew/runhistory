from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class VideoRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200, description="Historical topic for video generation")

class VideoResponse(BaseModel):
    session_id: str
    status: str
    video_url: Optional[str] = None
    script: Optional[str] = None
    assets: Optional[Dict[str, Any]] = None

class GenerationStatus(BaseModel):
    session_id: str
    status: str  # initializing, generating_script, generating_images, generating_voiceover, creating_video, completed, error
    progress: int = Field(0, ge=0, le=100)
    message: str = ""
    video_path: Optional[str] = None
    error: Optional[str] = None

class ScriptData(BaseModel):
    script: str
    image_prompts: List[str]
    duration: int

class ImageGenerationRequest(BaseModel):
    prompts: List[str]
    style: Optional[str] = None

class VoiceoverRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None
    speed: Optional[float] = 1.0
    volume: Optional[float] = 1.0

class VideoCreationRequest(BaseModel):
    image_paths: List[str]
    voiceover_path: str
    output_path: str
    duration: Optional[int] = 60

class AssetResponse(BaseModel):
    script: Optional[str] = None
    voiceover: Optional[str] = None
    images: List[str] = []
    video: Optional[str] = None
