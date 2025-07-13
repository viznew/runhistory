import os
import asyncio
import shutil
from pathlib import Path
from typing import Dict, Any
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import logging

from services.openai_service import OpenAIService
from services.elevenlabs_service import ElevenLabsService
from services.video_service import VideoService
from services.image_overlay_service import ImageOverlayService
from utils.file_manager import FileManager
from models.models import VideoRequest, VideoResponse, GenerationStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="RunHistory.log Generator", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize services
openai_service = OpenAIService()
elevenlabs_service = ElevenLabsService()
video_service = VideoService()
image_overlay_service = ImageOverlayService()
file_manager = FileManager()

# Global status tracking
generation_status: Dict[str, GenerationStatus] = {}

@app.get("/")
async def root():
    """Serve the main HTML page"""
    return FileResponse("static/index.html")

@app.get("/health")
async def health_check():
    """Health check endpoint for deployment"""
    try:
        # Minimal health check for faster response
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.post("/generate")
async def generate_video(request: VideoRequest, background_tasks: BackgroundTasks):
    """Start video generation process"""
    try:
        # Generate unique session ID
        session_id = file_manager.generate_session_id()
        
        # Initialize status
        generation_status[session_id] = GenerationStatus(
            session_id=session_id,
            status="initializing",
            progress=0,
            message="Starting video generation..."
        )
        
        # Start background task
        background_tasks.add_task(generate_video_task, session_id, request.topic)
        
        return {"session_id": session_id, "status": "started"}
        
    except Exception as e:
        logger.error(f"Error starting video generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start generation: {str(e)}")

@app.get("/status/{session_id}")
async def get_status(session_id: str):
    """Get generation status"""
    if session_id not in generation_status:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return generation_status[session_id]

@app.get("/download/{session_id}")
async def download_video(session_id: str):
    """Download generated video"""
    if session_id not in generation_status:
        raise HTTPException(status_code=404, detail="Session not found")
    
    status = generation_status[session_id]
    if status.status != "completed":
        raise HTTPException(status_code=400, detail="Video not ready for download")
    
    video_path = Path(f"generated/{session_id}/final_video.mp4")
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")
    
    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=f"history_{session_id}.mp4"
    )

@app.get("/assets/{session_id}")
async def get_assets(session_id: str):
    """Get all generated assets for a session"""
    if session_id not in generation_status:
        raise HTTPException(status_code=404, detail="Session not found")
    
    assets_dir = Path(f"generated/{session_id}")
    if not assets_dir.exists():
        raise HTTPException(status_code=404, detail="Assets not found")
    
    assets = {
        "script": None,
        "voiceover": None,
        "images": [],
        "video": None
    }
    
    # Get script
    script_path = assets_dir / "script.txt"
    if script_path.exists():
        assets["script"] = script_path.read_text()
    
    # Get voiceover path
    voiceover_path = assets_dir / "voiceover.mp3"
    if voiceover_path.exists():
        assets["voiceover"] = f"/download-asset/{session_id}/voiceover.mp3"
    
    # Get images
    for i in range(1, 17):  # Up to 16 images
        img_path = assets_dir / f"image_{i:02d}.png"
        if img_path.exists():
            assets["images"].append(f"/download-asset/{session_id}/image_{i:02d}.png")
    
    # Get video
    video_path = assets_dir / "final_video.mp4"
    if video_path.exists():
        assets["video"] = f"/download/{session_id}"
    
    return assets

@app.get("/download-asset/{session_id}/{filename}")
async def download_asset(session_id: str, filename: str):
    """Download individual asset"""
    if session_id not in generation_status:
        raise HTTPException(status_code=404, detail="Session not found")
    
    asset_path = Path(f"generated/{session_id}/{filename}")
    if not asset_path.exists():
        raise HTTPException(status_code=404, detail="Asset not found")
    
    return FileResponse(asset_path, filename=filename)

async def generate_video_task(session_id: str, topic: str):
    """Background task for video generation"""
    try:
        # Create session directory
        session_dir = file_manager.create_session_directory(session_id)
        
        # Step 1: Generate script
        generation_status[session_id].status = "generating_script"
        generation_status[session_id].progress = 10
        generation_status[session_id].message = "Generating script with AI..."
        
        script_data = await openai_service.generate_script(topic)
        script_path = session_dir / "script.txt"
        script_path.write_text(script_data["script"])
        
        # Step 2: Generate images (optimized for deployment)
        generation_status[session_id].status = "generating_images"
        generation_status[session_id].progress = 30
        generation_status[session_id].message = "Generating images with DALL-E..."
        
        # Use batch processing for better deployment performance
        image_paths = []
        batch_size = int(os.environ.get("BATCH_SIZE", "3"))
        
        for i in range(0, len(script_data["image_prompts"]), batch_size):
            batch_prompts = script_data["image_prompts"][i:i + batch_size]
            
            try:
                # Generate batch of images
                batch_urls = await openai_service.generate_multiple_images(batch_prompts)
                
                # Download images from batch
                for j, image_url in enumerate(batch_urls):
                    try:
                        image_path = await file_manager.download_image(
                            image_url, session_dir, f"image_{i+j+1:02d}.png"
                        )
                        image_paths.append(image_path)
                        
                        # Update progress
                        total_processed = len(image_paths)
                        progress = 30 + total_processed * 25 // len(script_data["image_prompts"])
                        generation_status[session_id].progress = progress
                        generation_status[session_id].message = f"Generated image {total_processed}/{len(script_data['image_prompts'])}"
                        
                    except Exception as e:
                        logger.error(f"Error downloading image {i+j+1}: {str(e)}")
                        continue
                
            except Exception as e:
                logger.error(f"Error generating batch {i//batch_size + 1}: {str(e)}")
                continue
        
        # Step 2.5: Add text overlays to images
        generation_status[session_id].status = "adding_overlays"
        generation_status[session_id].progress = 55
        generation_status[session_id].message = "Adding text overlays to images..."
        
        if image_paths and 'text_overlays' in script_data:
            try:
                overlays_dir = session_dir / "overlays"
                overlay_paths = await image_overlay_service.add_multiple_overlays(
                    image_paths, 
                    script_data['text_overlays'], 
                    overlays_dir
                )
                # Use overlay images instead of original images
                image_paths = overlay_paths
                generation_status[session_id].message = "Text overlays added successfully"
            except Exception as e:
                logger.error(f"Error adding text overlays: {str(e)}")
                # Continue with original images if overlay fails
                generation_status[session_id].message = "Continuing without text overlays"
        
        # Step 3: Generate voiceover
        generation_status[session_id].status = "generating_voiceover"
        generation_status[session_id].progress = 70
        generation_status[session_id].message = "Generating voiceover..."
        
        voiceover_path = await elevenlabs_service.generate_voiceover(
            script_data["script"], 
            session_dir / "voiceover.mp3"
        )
        
        # Step 4: Create video
        generation_status[session_id].status = "creating_video"
        generation_status[session_id].progress = 85
        generation_status[session_id].message = "Assembling final video..."
        
        video_path = await video_service.create_video(
            image_paths=image_paths,
            voiceover_path=voiceover_path,
            output_path=session_dir / "final_video.mp4",
            script_duration=script_data.get("duration", 60)
        )
        
        # Memory optimization: cleanup temporary files
        try:
            import gc
            gc.collect()
        except Exception:
            pass
        
        # Complete
        generation_status[session_id].status = "completed"
        generation_status[session_id].progress = 100
        generation_status[session_id].message = "Video generation completed!"
        generation_status[session_id].video_path = str(video_path)
        
    except Exception as e:
        logger.error(f"Error in video generation task: {str(e)}")
        generation_status[session_id].status = "error"
        generation_status[session_id].message = f"Error: {str(e)}"

if __name__ == "__main__":
    # Ensure directories exist at startup
    Path("generated").mkdir(exist_ok=True)
    Path("static").mkdir(exist_ok=True)
    
    # Get port from environment variable or default to 8000
    port = int(os.environ.get("PORT", 8000))
    
    logger.info(f"Starting server on host=0.0.0.0, port={port}")
    logger.info(f"Environment: {os.environ.get('DEPLOYMENT_ENV', 'development')}")
    logger.info(f"Health check available at: http://0.0.0.0:{port}/health")
    
    try:
        # Simple server configuration for deployment
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=port,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        raise
