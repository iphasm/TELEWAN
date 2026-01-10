"""
SynthClip Web Application
FastAPI backend for the SynthClip video generation web interface
"""
import os
import uuid
import asyncio
import aiofiles
import base64
import json
from typing import Dict, Any, Optional
from datetime import datetime, date
from pathlib import Path

# Translation imports
try:
    from deep_translator import GoogleTranslator
    from langdetect import detect
    TRANSLATION_AVAILABLE = True
    # Define exception for langdetect errors (langdetect doesn't export LangDetectError in some versions)
    LangDetectError = Exception
except ImportError as e:
    print(f"⚠️ Translation libraries import failed: {e}. Install with: pip install deep-translator langdetect")
    TRANSLATION_AVAILABLE = False
    GoogleTranslator = None
    detect = None
    LangDetectError = Exception

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks, Request
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from async_wavespeed import AsyncWavespeedAPI
from config import Config

# FastAPI app will be created later with lifespan

# Global variables
api_client = AsyncWavespeedAPI()
tasks: Dict[str, Dict[str, Any]] = {}

# Rate limiting configuration
USAGE_FILE = Path("usage_data.json")
DAILY_LIMIT = 5
SUSPICIOUS_THRESHOLD = 3  # Número de IPs diferentes antes de marcar como sospechoso

def load_usage_data() -> Dict[str, Any]:
    """Load usage data from file"""
    if USAGE_FILE.exists():
        try:
            with open(USAGE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        "daily_usage": {},
        "user_fingerprints": {},  # Maps fingerprint to usage data
        "ip_fingerprints": {},    # Maps IP to list of fingerprints
        "suspicious_users": {},   # Users flagged as suspicious
        "last_reset": str(date.today())
    }

def save_usage_data(data: Dict[str, Any]):
    """Save usage data to file"""
    try:
        with open(USAGE_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving usage data: {e}")

def reset_daily_usage_if_needed(usage_data: Dict[str, Any]) -> Dict[str, Any]:
    """Reset daily usage counters if it's a new day"""
    today = str(date.today())
    if usage_data.get("last_reset") != today:
        usage_data["daily_usage"] = {}
        usage_data["last_reset"] = today
        # Keep fingerprints and suspicious data across days
        save_usage_data(usage_data)
    return usage_data

def generate_fingerprint(client_ip: str, user_agent: str = "", fingerprint_data: Dict[str, Any] = None) -> str:
    """Generate a unique fingerprint for the user"""
    import hashlib

    # Create fingerprint from available data
    fingerprint_parts = [client_ip]

    if user_agent:
        fingerprint_parts.append(user_agent[:50])  # First 50 chars of user agent

    if fingerprint_data:
        # Add browser fingerprint data if available
        for key in ['canvas', 'webgl', 'screen', 'timezone']:
            if key in fingerprint_data:
                fingerprint_parts.append(str(fingerprint_data[key]))

    # Create hash
    fingerprint_string = "|".join(fingerprint_parts)
    return hashlib.sha256(fingerprint_string.encode()).hexdigest()[:16]

def associate_fingerprint_with_ip(usage_data: Dict[str, Any], client_ip: str, fingerprint: str):
    """Associate a fingerprint with an IP address for tracking"""
    ip_fingerprints = usage_data.setdefault("ip_fingerprints", {})
    if client_ip not in ip_fingerprints:
        ip_fingerprints[client_ip] = []

    if fingerprint not in ip_fingerprints[client_ip]:
        ip_fingerprints[client_ip].append(fingerprint)

def is_suspicious_user(usage_data: Dict[str, Any], fingerprint: str) -> bool:
    """Check if user is flagged as suspicious"""
    suspicious_users = usage_data.get("suspicious_users", {})
    return fingerprint in suspicious_users

def flag_suspicious_user(usage_data: Dict[str, Any], fingerprint: str, reason: str):
    """Flag a user as suspicious"""
    suspicious_users = usage_data.setdefault("suspicious_users", {})
    suspicious_users[fingerprint] = {
        "flagged_at": datetime.now().isoformat(),
        "reason": reason
    }
    save_usage_data(usage_data)

# Translation functions
def detect_language(text: str) -> str:
    """Detect the language of the given text"""
    if not TRANSLATION_AVAILABLE:
        return "en"  # Default to English if translation not available

    try:
        return detect(text)
    except Exception as e:
        print(f"⚠️ Language detection failed: {e}")
        return "en"  # Default to English on detection error

def translate_to_english(text: str) -> tuple[str, bool]:
    """
    Silently translate any non-English text to English for better AI results
    Returns: (translated_text, was_translated)
    """
    if not TRANSLATION_AVAILABLE:
        return text, False

    try:
        detected_lang = detect_language(text)

        if detected_lang == "en":
            return text, False

        # Translate from any detected language to English
        try:
            translator = GoogleTranslator(source=detected_lang, target='en')
            translated = translator.translate(text)
            print(f"🌐 Auto-translated from {detected_lang}: '{text[:50]}...' → '{translated[:50]}...'")
            return translated, True
        except:
            # If specific language detection fails, try auto-detection
            translator = GoogleTranslator(source='auto', target='en')
            translated = translator.translate(text)
            print(f"🌐 Auto-translated (auto-detect): '{text[:50]}...' → '{translated[:50]}...'")
            return translated, True

    except Exception as e:
        print(f"⚠️ Translation error: {e}")
        return text, False

def check_rate_limit_advanced(client_ip: str, fingerprint: str, user_agent: str = "") -> tuple[bool, int, int, bool]:
    """
    Advanced rate limiting using IP + fingerprint + behavior analysis
    Returns: (allowed: bool, used: int, remaining: int, is_suspicious: bool)
    """
    usage_data = load_usage_data()
    usage_data = reset_daily_usage_if_needed(usage_data)

    # Associate fingerprint with IP for tracking
    associate_fingerprint_with_ip(usage_data, client_ip, fingerprint)

    # Check if user is already flagged as suspicious
    if is_suspicious_user(usage_data, fingerprint):
        print(f"🚨 Suspicious user detected: {fingerprint}")
        return False, 0, 0, True

    # Check for VPN/abuse patterns
    ip_fingerprints = usage_data.get("ip_fingerprints", {}).get(client_ip, [])
    if len(ip_fingerprints) > SUSPICIOUS_THRESHOLD:
        flag_suspicious_user(usage_data, fingerprint, f"Multiple fingerprints from IP: {len(ip_fingerprints)}")
        return False, 0, 0, True

    # Get usage for this fingerprint (more restrictive than IP alone)
    user_fingerprints = usage_data.setdefault("user_fingerprints", {})
    if fingerprint not in user_fingerprints:
        user_fingerprints[fingerprint] = {"daily_usage": 0, "last_used": None}

    user_data = user_fingerprints[fingerprint]
    used_today = user_data.get("daily_usage", 0)
    remaining = max(0, DAILY_LIMIT - used_today)

    return used_today < DAILY_LIMIT, used_today, remaining, False

def increment_usage_advanced(client_ip: str, fingerprint: str) -> bool:
    """Increment usage counter for fingerprint (more restrictive)"""
    try:
        usage_data = load_usage_data()
        usage_data = reset_daily_usage_if_needed(usage_data)

        # Update fingerprint usage
        user_fingerprints = usage_data.setdefault("user_fingerprints", {})
        if fingerprint not in user_fingerprints:
            user_fingerprints[fingerprint] = {"daily_usage": 0, "last_used": None}

        user_data = user_fingerprints[fingerprint]
        user_data["daily_usage"] = user_data.get("daily_usage", 0) + 1
        user_data["last_used"] = datetime.now().isoformat()

        # Also track IP usage for compatibility
        daily_usage = usage_data.setdefault("daily_usage", {})
        daily_usage[client_ip] = daily_usage.get(client_ip, 0) + 1

        save_usage_data(usage_data)
        return True
    except Exception as e:
        print(f"Error incrementing usage: {e}")
        return False

# Ensure storage directory exists
storage_dir = Path(Config.VOLUME_PATH)
storage_dir.mkdir(exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application"""
    try:
        Config.validate()
        print("✅ SynthClip Web App initialized successfully")
        print(f"📁 Storage directory: {storage_dir.absolute()}")
        print(f"🎬 Using Wavespeed API: {Config.WAVESPEED_BASE_URL}")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        raise

    yield

    # Cleanup (if needed)
    pass

# Create FastAPI app with lifespan
app = FastAPI(
    title="SynthClip API",
    description="API for SynthClip video generation with AI",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    auto_optimize: bool = Form(False),
    add_audio: bool = Form(False),
    upscale_1080p: bool = Form(False),
    fingerprint: str = Form(""),  # Browser fingerprint
    request: Request = None  # For getting client IP
):
    """
    Start video generation process
    """
    try:
        # Get client IP and user agent for advanced rate limiting
        client_ip = request.client.host if request else "unknown"
        user_agent = request.headers.get("user-agent", "") if request else ""

        # Generate or use provided fingerprint
        if not fingerprint:
            fingerprint = generate_fingerprint(client_ip, user_agent)

        print(f"🎯 Request from IP: {client_ip}, Fingerprint: {fingerprint[:8]}...")

        # Check advanced rate limit
        allowed, used, remaining, is_suspicious = check_rate_limit_advanced(client_ip, fingerprint, user_agent)
        if not allowed:
            if is_suspicious:
                return {
                    "error": "Actividad sospechosa detectada",
                    "message": "Se ha detectado un patrón de uso inusual. Por favor, contacta con soporte si crees que esto es un error.",
                    "remaining": 0,
                    "suspicious": True,
                    "upgrade_message": "Contacta con soporte para resolver este problema."
                }
            else:
                return {
                    "error": "Límite diario excedido",
                    "message": f"Has alcanzado el límite de {DAILY_LIMIT} videos por día. Usaste {used} hoy.",
                    "remaining": remaining,
                    "reset_time": "mañana a las 00:00",
                    "upgrade_message": "Actualiza a un plan premium para más videos diarios."
                }

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
            "add_audio": add_audio,
            "upscale_1080p": upscale_1080p,
            "original_prompt": prompt,
            "optimized_prompt": None,
            "image_url": None,
            "video_url": None,
            "audio_video_url": None,
            "upscaled_video_url": None,
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
            base_url = os.getenv('BASE_URL', 'http://localhost:8000').rstrip('/')
            image_url = f"{base_url}/images/{image_path.name}"

        print(f"🎯 Processing request: model={model}, has_image={image is not None}, image_url={image_url is not None}")

        # Increment usage counter (advanced system)
        increment_usage_advanced(client_ip, fingerprint)

        # Start background processing
        background_tasks.add_task(
            process_video_generation,
            task_id,
            prompt,
            image_url,
            model,
            auto_optimize,
            add_audio,
            upscale_1080p
        )

        return {
            "task_id": task_id,
            "status": "processing",
            "message": "Video generation started",
            "usage_today": used + 1,
            "remaining_today": remaining - 1
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
            "prompt_used": task["optimized_prompt"] or task["translated_prompt"] or task["original_prompt"],
            "model": task["model"],
            "was_optimized": bool(task.get("optimized_prompt"))
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
    auto_optimize: bool,
    add_audio: bool,
    upscale_1080p: bool
):
    """
    Background task to process video generation
    """
    try:
        task = tasks[task_id]
        task["progress"] = 10
        if model == "text_to_video":
            task["message"] = "Preparando generación de video desde texto..."
        else:
            task["message"] = "Preparando generación de video desde imagen..."

        # Step 1: Silently translate to English if needed, then optimize if requested
        final_prompt = prompt
        original_language = detect_language(prompt)
        was_translated = False

        # Silently auto-translate any non-English prompts to English for better AI results
        if original_language != "en":
            translated_prompt, was_translated = translate_to_english(prompt)
            if was_translated:
                final_prompt = translated_prompt
                task["translated_prompt"] = final_prompt
                task["original_prompt"] = prompt  # Keep original for reference
                task["original_language"] = original_language

        # Determine progress message based on content type
        is_text_only = (model == "text_to_video")

        if auto_optimize:
            if is_text_only:
                task["progress"] = 20
                task["message"] = "Optimizando descripción con IA..."

                try:
                    # Use text-only optimization for T2V
                    optimize_result = await api_client.optimize_prompt_text_only(
                        text=prompt,
                        mode="video",
                        style="default"
                    )

                    # For text-only, the result should be direct
                    if "optimized_prompt" in optimize_result:
                        optimized = optimize_result["optimized_prompt"]
                        if optimized and len(optimized.strip()) > len(prompt):
                            final_prompt = optimized
                            task["optimized_prompt"] = final_prompt
                            print(f"✅ Text-only prompt optimized: {len(optimized)} chars")
                    elif "result" in optimize_result:
                        # Some APIs return result directly
                        optimized = optimize_result["result"]
                        if optimized and len(optimized.strip()) > len(prompt):
                            final_prompt = optimized
                            task["optimized_prompt"] = final_prompt
                            print(f"✅ Text-only prompt optimized: {len(optimized)} chars")

                except Exception as e:
                    print(f"⚠️  Text-only prompt optimization failed: {e}")
                    # Continue with original prompt

            elif image_url:
                task["progress"] = 20
                task["message"] = "Analizando imagen y optimizando descripción..."

                try:
                    optimize_result = await api_client.optimize_prompt_v3(
                        image_url=image_url,
                        text=prompt,
                        mode="video",
                        style="default"
                    )

                    # Poll for optimization result with timeout
                    task_id = optimize_result["id"]
                    max_attempts = 10
                    attempt = 0

                    while attempt < max_attempts:
                        try:
                            opt_status = await api_client.get_prompt_optimizer_result(task_id)

                            if opt_status.get("status") == "completed":
                                if "optimized_prompt" in opt_status:
                                    optimized = opt_status["optimized_prompt"]
                                    if optimized and len(optimized.strip()) > len(prompt):
                                        final_prompt = optimized
                                        task["optimized_prompt"] = final_prompt
                                        print(f"✅ Image-based prompt optimized: {len(optimized)} chars")
                                break
                            elif opt_status.get("status") == "failed":
                                print(f"⚠️  Prompt optimization failed on server side")
                                break

                            # Wait before next attempt
                            await asyncio.sleep(1)
                            attempt += 1

                        except Exception as poll_error:
                            print(f"⚠️  Error polling prompt optimization: {poll_error}")
                            break

                    if attempt >= max_attempts:
                        print(f"⚠️  Prompt optimization timed out after {max_attempts} attempts")

                except Exception as e:
                    print(f"⚠️  Image-based prompt optimization failed: {e}")
                    # Continue with original prompt
            else:
                print(f"📝 Using original prompt (auto_optimize={auto_optimize}, model={model})")

        print(f"🎬 Final prompt: {final_prompt[:100]}...")

        task["progress"] = 30
        if model == "text_to_video":
            task["message"] = "Generando video desde descripción textual..."
        else:
            task["message"] = "Generando video desde imagen..."

        # Step 2: Generate video
        try:
            print(f"🎬 Starting video generation with model: {model}")
            print(f"📝 Prompt: {final_prompt[:100]}...")
            print(f"🖼️  Image URL: {image_url}")

            video_result = await api_client.generate_video(
                prompt=final_prompt,
                image_url=image_url,
                model=model
            )

            print(f"✅ Video generation API response: {video_result}")

            if not video_result:
                raise Exception("Empty response from video generation API")

            task["progress"] = 50
            task["message"] = "Video generation in progress..."

            # Step 3: Poll for completion
            # Handle nested response structure from Wavespeed API
            request_id = None
            if video_result.get("data") and video_result["data"].get("id"):
                request_id = video_result["data"]["id"]
            elif video_result.get("id"):
                request_id = video_result["id"]
            elif video_result.get("request_id"):
                request_id = video_result["request_id"]

            if not request_id:
                print(f"❌ No request ID in response: {video_result}")
                raise Exception("No request ID received from API")

            print(f"🔄 Starting polling for request_id: {request_id}")
            print(f"📊 Full initial response: {video_result}")

            # Poll for status
            max_attempts = 240  # ~4 minutes (back to original)
            for attempt in range(max_attempts):
                try:
                    print(f"🔍 Checking status (attempt {attempt + 1}/{max_attempts}) for request_id: {request_id}")
                    status_result = await api_client.get_video_status(request_id)
                    print(f"📋 Raw status result: {status_result}")

                    if not status_result:
                        print(f"⚠️  Empty status result, retrying...")
                        await asyncio.sleep(1)
                        continue

                    # Handle nested response structure like the original bot
                    if status_result.get('data'):
                        task_data = status_result['data']
                        status = task_data.get('status')
                        print(f"📊 Using nested status: {status}")
                    else:
                        status = status_result.get("status")
                        print(f"📊 Using direct status: {status}")

                    if status is None:
                        print(f"⚠️  Status is None, response: {status_result}")
                        await asyncio.sleep(1)
                        continue

                    if status == "completed":
                        # Check for video URL in nested structure (like original bot)
                        if status_result.get('data') and status_result['data'].get('outputs'):
                            task_data = status_result['data']
                            if len(task_data['outputs']) > 0:
                                video_url = task_data['outputs'][0]
                                print(f"🎬 Video URL found in nested outputs: {video_url[:50]}...")
                        else:
                            # Fallback to direct fields
                            video_url = (status_result.get("video_url") or
                                       status_result.get("video") or
                                       status_result.get("output") or
                                       status_result.get("result"))
                            print(f"🎬 Video URL found in direct fields: {video_url[:50] if video_url else 'None'}...")

                        if not video_url:
                            print(f"❌ No video URL found in response: {status_result}")
                            raise Exception("No video URL received from completed API response")

                        if video_url:
                            # Download and save video
                            task["progress"] = 70
                            task["message"] = "Descargando video base..."

                            video_content = await api_client.download_video(video_url)

                            # Save video file
                            video_filename = f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.mp4"
                            video_path = storage_dir / video_filename

                            async with aiofiles.open(video_path, "wb") as f:
                                await f.write(video_content)

                            task["video_url"] = f"/videos/{video_filename}"
                            print(f"✅ Video base generated successfully: {video_filename}")

                            # If no additional processing is needed, mark as completed immediately
                            if not add_audio and not upscale_1080p:
                                task["progress"] = 100
                                task["status"] = "completed"
                                task["message"] = "¡Video completado!"
                                print(f"🎉 Video processing completed for task {task_id}")
                                return

                            # Process additional stages
                            final_video_url = task['video_url']
                            final_video_path = video_path

                            # Stage 1: Audio processing (if requested)
                            if add_audio:
                                print("🎵 Starting audio generation...")
                                task["progress"] = 80
                                task["message"] = "Generando audio ambiental..."

                                # Create a URL for the generated video so audio API can access it
                                video_file_url = f"{os.getenv('BASE_URL', 'http://localhost:8000')}{task['video_url']}"

                                try:
                                    # Pass the final prompt (optimized or original) to audio generation
                                    final_prompt = task.get("optimized_prompt") or task["original_prompt"]
                                    audio_video_url = await api_client.add_audio_to_video(video_file_url, final_prompt)
                                    if audio_video_url:
                                        # Download the video with audio and replace the original
                                        audio_video_content = await api_client.download_video(audio_video_url)

                                        # Save the video with audio, replacing the original
                                        async with aiofiles.open(video_path, "wb") as f:
                                            await f.write(audio_video_content)

                                        task["audio_video_url"] = task["video_url"]  # Same URL, new content
                                        print(f"✅ Audio added successfully, video updated")
                                    else:
                                        print("⚠️  Audio generation failed, keeping original video")
                                except Exception as e:
                                    print(f"⚠️  Audio generation error: {e}, keeping original video")

                            # Stage 2: 1080P upscale (if requested)
                            if upscale_1080p:
                                print("⬆️ Starting 1080P upscale...")
                                task["progress"] = 95
                                task["message"] = "Escalando a 1080P premium..."

                                # Create a URL for the current video (with or without audio)
                                video_file_url = f"{os.getenv('BASE_URL', 'http://localhost:8000')}{task['video_url']}"

                                try:
                                    upscaled_video_url = await api_client.upscale_video_to_1080p(video_file_url)
                                    if upscaled_video_url:
                                        # Download the upscaled video and replace the original
                                        upscaled_video_content = await api_client.download_video(upscaled_video_url)

                                        # Save the upscaled video, replacing the original
                                        async with aiofiles.open(video_path, "wb") as f:
                                            await f.write(upscaled_video_content)

                                        task["upscaled_video_url"] = task["video_url"]  # Same URL, new content
                                        print(f"✅ Video upscaled to 1080P successfully")
                                    else:
                                        print("⚠️  1080P upscale failed, keeping original video")
                                except Exception as e:
                                    print(f"⚠️  1080P upscale error: {e}, keeping original video")

                            # All stages completed - mark as done
                            task["progress"] = 100
                            task["status"] = "completed"

                            # Set final message based on what was processed
                            if add_audio and upscale_1080p:
                                task["message"] = "¡Video Ultimate completado!"
                            elif add_audio:
                                task["message"] = "¡Video con audio completado!"
                            elif upscale_1080p:
                                task["message"] = "¡Video 1080P completado!"
                            else:
                                task["message"] = "¡Video completado!"

                            print(f"🎉 All processing stages completed for task {task_id}")
                            return

                    elif status == "failed":
                        # Check for error in nested structure too
                        if status_result.get('data'):
                            error_msg = status_result['data'].get("error", "Video generation failed on API side")
                        else:
                            error_msg = status_result.get("error", "Video generation failed on API side")
                        print(f"❌ Video generation failed: {error_msg}")
                        raise Exception(f"Video generation failed: {error_msg}")

                    elif status == "processing":
                        pass  # Still processing, continue polling

                    else:
                        print(f"🤔 Unknown status: {status}")

                    # Update progress
                    progress = 50 + (attempt / max_attempts) * 30
                    task["progress"] = min(progress, 90)
                    task["message"] = f"Generating video... ({attempt + 1}/{max_attempts})"

                    await asyncio.sleep(1)  # Check every 1 second

                except Exception as e:
                    print(f"❌ Status check failed (attempt {attempt + 1}): {type(e).__name__}: {e}")
                    if attempt < max_attempts - 1:  # Don't sleep on last attempt
                        await asyncio.sleep(2)  # Wait longer on error
                    else:
                        raise Exception(f"Status polling failed after {max_attempts} attempts: {e}")

            # If we get here, polling timed out
            print(f"⏰ Polling timeout after {max_attempts} attempts")
            raise Exception(f"Video generation timeout after {max_attempts} attempts")

        except Exception as e:
            print(f"❌ Video generation failed: {type(e).__name__}: {e}")
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

# Usage check endpoint
@app.get("/usage")
async def check_usage(request: Request = None):
    """Check daily usage with advanced fingerprinting"""
    client_ip = request.client.host if request else "unknown"
    user_agent = request.headers.get("user-agent", "") if request else ""

    # For usage checking, we create a temporary fingerprint
    # In production, this would come from browser fingerprinting
    temp_fingerprint = generate_fingerprint(client_ip, user_agent)
    allowed, used, remaining, is_suspicious = check_rate_limit_advanced(client_ip, temp_fingerprint, user_agent)

    return {
        "ip": client_ip,
        "fingerprint": temp_fingerprint[:8],
        "used_today": used,
        "remaining_today": remaining,
        "daily_limit": DAILY_LIMIT,
        "allowed": allowed and not is_suspicious,
        "suspicious": is_suspicious,
        "reset_time": "mañana a las 00:00"
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