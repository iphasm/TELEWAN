"""
SynthClip Web Application
FastAPI backend for the SynthClip video generation web interface
"""
import os
import uuid
import asyncio
import aiofiles
import base64
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from async_wavespeed import AsyncWavespeedAPI
from config import Config

# Initialize FastAPI app
app = FastAPI(
    title="SynthClip API",
    description="API for SynthClip video generation with AI",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
api_client = AsyncWavespeedAPI()
tasks: Dict[str, Dict[str, Any]] = {}

# Ensure storage directory exists
storage_dir = Path(Config.VOLUME_PATH)
storage_dir.mkdir(exist_ok=True)

@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    try:
        Config.validate()
        print("✅ SynthClip Web App initialized successfully")
        print(f"📁 Storage directory: {storage_dir.absolute()}")
        print(f"🎬 Using Wavespeed API: {Config.WAVESPEED_BASE_URL}")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        raise

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web interface"""
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="index.html not found")

@app.post("/generate")
async def generate_video(
    background_tasks: BackgroundTasks,
    image: Optional[UploadFile] = File(None),
    prompt: str = Form(...),
    model: str = Form("ultra_fast"),
    auto_optimize: bool = Form(False)
):
    """
    Start video generation process
    """
    try:
        # Validate inputs
        if model not in Config.AVAILABLE_MODELS:
            raise HTTPException(status_code=400, detail=f"Modelo no válido: {model}")

        if model != "text_to_video" and not image:
            raise HTTPException(status_code=400, detail="Imagen requerida para este modelo")

        if not prompt.strip():
            raise HTTPException(status_code=400, detail="Prompt es requerido")

        # Generate task ID
        task_id = str(uuid.uuid4())

        # Initialize task
        tasks[task_id] = {
            "status": "processing",
            "progress": 0,
            "created_at": datetime.now(),
            "model": model,
            "auto_optimize": auto_optimize,
            "original_prompt": prompt,
            "optimized_prompt": None,
            "image_url": None,
            "video_url": None,
            "error": None
        }

        # Save uploaded image if provided and create accessible URL
        image_url = None
        if image:
            image_path = storage_dir / f"input_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.jpg"
            async with aiofiles.open(image_path, "wb") as f:
                content = await image.read()
                await f.write(content)

            # Create a full URL that can be accessed by Wavespeed API
            # Get the base URL from environment or request
            base_url = os.getenv('BASE_URL', 'http://localhost:8000')
            image_url = f"{base_url}/images/{image_path.name}"

        # Start background processing
        background_tasks.add_task(
            process_video_generation,
            task_id,
            prompt,
            image_url,
            model,
            auto_optimize
        )

        return {
            "task_id": task_id,
            "status": "processing",
            "message": "Video generation started"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Get the status of a video generation task
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = tasks[task_id]

    # If completed, return final result
    if task["status"] == "completed":
        return {
            "status": "completed",
            "video_url": task["video_url"],
            "prompt_used": task["optimized_prompt"] or task["original_prompt"],
            "model": task["model"]
        }
    elif task["status"] == "failed":
        return {
            "status": "failed",
            "error": task["error"]
        }
    else:
        # Still processing
        return {
            "status": "processing",
            "progress": task.get("progress", 0),
            "message": task.get("message", "Processing...")
        }

async def process_video_generation(
    task_id: str,
    prompt: str,
    image_url: Optional[str],
    model: str,
    auto_optimize: bool
):
    """
    Background task to process video generation
    """
    try:
        task = tasks[task_id]
        task["progress"] = 10
        task["message"] = "Initializing..."

        # Step 1: Optimize prompt if requested
        final_prompt = prompt
        if auto_optimize and image_url:
            task["progress"] = 20
            task["message"] = "Optimizing prompt with AI..."

            try:
                optimize_result = await api_client.optimize_prompt_v3(
                    image_url=image_url,
                    text=prompt,
                    mode="video",
                    style="default"
                )

                # Wait for optimization to complete
                await asyncio.sleep(2)  # Brief wait
                opt_status = await api_client.get_prompt_optimizer_result(optimize_result["id"])

                if "optimized_prompt" in opt_status:
                    optimized = opt_status["optimized_prompt"]
                    if optimized and len(optimized.strip()) > len(prompt):
                        final_prompt = optimized
                        task["optimized_prompt"] = final_prompt
                        print(f"✅ Prompt optimized: {len(optimized)} chars")

            except Exception as e:
                print(f"⚠️  Prompt optimization failed: {e}")
                # Continue with original prompt

        task["progress"] = 30
        task["message"] = "Starting video generation..."

        # Step 2: Generate video
        try:
            video_result = await api_client.generate_video(
                prompt=final_prompt,
                image_url=image_url,
                model=model
            )

            task["progress"] = 50
            task["message"] = "Video generation in progress..."

            # Step 3: Poll for completion
            request_id = video_result.get("id") or video_result.get("request_id")
            if not request_id:
                raise Exception("No request ID received from API")

            print(f"🔄 Starting polling for request_id: {request_id}")
            print(f"📊 Initial video result: {video_result}")

            # Poll for status
            max_attempts = 120  # ~2 minutes (reduced for faster debugging)
            for attempt in range(max_attempts):
                try:
                    print(f"🔍 Checking status (attempt {attempt + 1}/{max_attempts})")
                    status_result = await api_client.get_video_status(request_id)
                    print(f"📋 Status result: {status_result}")

                    if not status_result:
                        print(f"⚠️  Empty status result, retrying...")
                        await asyncio.sleep(1)
                        continue

                    status = status_result.get("status")
                    if status == "completed":
                        # Check for video in different possible fields
                        video_url = (status_result.get("video_url") or
                                   status_result.get("video") or
                                   status_result.get("output") or
                                   status_result.get("result"))
                        print(f"🎬 Video URL found: {video_url}")
                        if video_url:
                            # Download and save video
                            task["progress"] = 80
                            task["message"] = "Downloading video..."

                            video_content = await api_client.download_video(video_url)

                            # Save video file
                            video_filename = f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.mp4"
                            video_path = storage_dir / video_filename

                            async with aiofiles.open(video_path, "wb") as f:
                                await f.write(video_content)

                            task["progress"] = 100
                            task["message"] = "Video completed!"
                            task["status"] = "completed"
                            task["video_url"] = f"/videos/{video_filename}"

                            print(f"✅ Video generated successfully: {video_filename}")
                            return

                    elif status == "failed":
                        error_msg = status_result.get("error", "Video generation failed on API side")
                        print(f"❌ Video generation failed: {error_msg}")
                        raise Exception(f"Video generation failed: {error_msg}")

                    elif status == "processing":
                        print(f"⚙️  Still processing...")

                    else:
                        print(f"🤔 Unknown status: {status}")

                    # Update progress
                    progress = 50 + (attempt / max_attempts) * 30
                    task["progress"] = min(progress, 90)
                    task["message"] = f"Generating video... ({attempt + 1}/{max_attempts})"

                    await asyncio.sleep(1)  # Check every 1 second

                except Exception as e:
                    print(f"❌ Status check failed (attempt {attempt + 1}): {e}")
                    # Continue polling even if one check fails
                    await asyncio.sleep(1)

            # If we get here, polling timed out
            print(f"⏰ Polling timeout after {max_attempts} attempts")
            raise Exception(f"Video generation timeout after {max_attempts} attempts")

        except Exception as e:
            raise Exception(f"Video generation failed: {str(e)}")

    except Exception as e:
        error_msg = str(e)
        print(f"❌ Video generation failed for task {task_id}: {error_msg}")

        task["status"] = "failed"
        task["error"] = error_msg

# Serve video files
@app.get("/videos/{filename}")
async def get_video(filename: str):
    """Serve generated video files"""
    video_path = storage_dir / filename
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")

    return FileResponse(
        path=video_path,
        media_type="video/mp4",
        filename=filename
    )

# Serve uploaded images (temporary workaround for Wavespeed API)
@app.get("/images/{filename}")
async def get_image(filename: str):
    """Serve uploaded images temporarily"""
    image_path = storage_dir / filename
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(
        path=image_path,
        media_type="image/jpeg",
        filename=filename
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Starting SynthClip Web App on port {port}")
    uvicorn.run(
        "web_app:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )