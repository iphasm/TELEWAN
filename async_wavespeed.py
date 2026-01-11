"""
Async WaveSpeed API Client
Reemplaza la implementación síncrona con aiohttp para arquitectura event-driven
"""
import aiohttp
import asyncio
import json
from typing import Dict, Optional, Any
from config import Config
import logging

logger = logging.getLogger(__name__)

class AsyncWavespeedAPI:
    """
    Async client for WaveSpeed AI APIs
    Reemplaza WavespeedAPI para arquitectura event-driven
    """

    def __init__(self):
        self.api_key = Config.WAVESPEED_API_KEY
        self.base_url = Config.WAVESPEED_BASE_URL
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    async def generate_video(self, prompt: str, image_url: str = None, model: str = None) -> Dict[str, Any]:
        """
        Genera un video usando diferentes modelos de Wavespeed AI (async)

        Args:
            prompt: Descripción del video a generar
            image_url: URL de la imagen de referencia (opcional para text-to-video)
            model: Modelo a usar ('ultra_fast', 'fast', 'quality', 'text_to_video')
        """
        if model is None or model not in Config.AVAILABLE_MODELS:
            model = Config.DEFAULT_MODEL

        model_endpoint = Config.AVAILABLE_MODELS[model]
        endpoint = f"{self.base_url}/api/v3/wavespeed-ai/{model_endpoint}"

        # Configuración específica por modelo
        model_config = {
            'ultra_fast': {'duration': Config.MAX_VIDEO_DURATION, 'resolution': '480p'},
            'fast': {'duration': Config.MAX_VIDEO_DURATION, 'resolution': '480p'},
            'quality': {'duration': Config.MAX_VIDEO_DURATION, 'resolution': '720p'},
            'text_to_video': {'duration': Config.MAX_VIDEO_DURATION, 'resolution': '480p'}
        }

        config = model_config.get(model, model_config['ultra_fast'])

        payload = {
            "duration": config['duration'],
            "prompt": prompt,
            "negative_prompt": Config.NEGATIVE_PROMPT,
            "seed": -1
        }

        # Solo incluir imagen si no es text-to-video o si se proporciona
        if image_url and model != 'text_to_video':
            payload["image"] = image_url
            payload["last_image"] = ""
        elif model == 'text_to_video' and image_url:
            # Para text-to-video con imagen de referencia opcional
            payload["image"] = image_url
            payload["last_image"] = ""

        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                logger.info(f"🚀 Iniciando generación de video con modelo: {model}")
                async with session.post(endpoint, json=payload) as response:
                    response.raise_for_status()
                    result = await response.json()
                    logger.info("✅ Video generation request submitted successfully")
                    # Return the data object directly as shown in the official API example
                    return result.get("data", result)
            except aiohttp.ClientError as e:
                logger.error(f"❌ Error en la API de Wavespeed: {e}")
                raise

    async def get_video_status(self, request_id: str) -> Dict[str, Any]:
        """
        Obtiene el estado de una tarea de generación de video (async)
        """
        endpoint = f"{self.base_url}/api/v3/predictions/{request_id}/result"

        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.get(endpoint) as response:
                    response.raise_for_status()
                    result = await response.json()
                    # Return the data object directly as shown in the official API example
                    return result.get("data", result)
            except aiohttp.ClientError as e:
                logger.error(f"❌ Error obteniendo estado del video: {e}")
                raise

    async def download_video(self, video_url: str, timeout: int = 30) -> bytes:
        """
        Descarga el video generado con mejor manejo de errores (async)
        """
        try:
            logger.info(f"📥 Iniciando descarga de video desde: {video_url[:50]}...")
            logger.info(f"   Timeout configurado: {timeout} segundos")

            # Headers para la descarga
            headers = {
                'User-Agent': 'TELEWAN-Bot/1.0',
                'Accept': 'video/mp4,video/*,*/*'
            }

            timeout_config = aiohttp.ClientTimeout(total=timeout)

            async with aiohttp.ClientSession(headers=headers, timeout=timeout_config) as session:
                async with session.get(video_url) as response:
                    response.raise_for_status()

                    # Verificar el tipo de contenido
                    content_type = response.headers.get('content-type', '')
                    logger.info(f"   Content-Type: {content_type}")
                    logger.info(f"   Content-Length: {response.headers.get('content-length', 'unknown')}")

                    # Verificar que sea un video
                    if not content_type.startswith('video/'):
                        logger.warning(f"⚠️  Content-Type inesperado: {content_type}")

                    # Descargar el contenido
                    content = await response.read()
                    logger.info(f"✅ Video descargado exitosamente: {len(content)} bytes")

                    return content

        except asyncio.TimeoutError as e:
            logger.error(f"⏰ Timeout descargando video ({timeout}s): {e}")
            raise
        except aiohttp.ClientError as e:
            logger.error(f"🌐 Error de conexión descargando video: {e}")
            raise
        except Exception as e:
            logger.error(f"💥 Error inesperado descargando video: {e}")
            raise

    async def optimize_prompt_v3(self, image_url: str, text: str, mode: str = "video", style: str = "default") -> Dict[str, Any]:
        """
        Optimiza un prompt usando la nueva API v3 de WaveSpeedAI (async)

        Args:
            image_url: URL de la imagen a analizar
            text: Texto del prompt a optimizar
            mode: Modo de optimización ('video' o 'image')
            style: Estilo de optimización ('default', 'realistic', 'cinematic')
        """
        endpoint = f"{self.base_url}/api/v3/wavespeed-ai/prompt-optimizer"

        payload = {
            "enable_sync_mode": False,
            "image": image_url,
            "mode": mode,
            "style": style,
            "text": text
        }

        logger.info(f"🤖 Calling prompt optimizer v3: image={image_url[:50]}..., text='{text}', mode={mode}, style={style}")

        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.post(endpoint, json=payload) as response:
                    response.raise_for_status()
                    result = await response.json()
                    logger.info(f"✅ Prompt optimization request submitted successfully: {result}")

                    # Extract the task ID from the response (can be nested in data)
                    task_id = (result.get("data", {}).get("id") or
                              result.get("id") or
                              result.get("request_id") or
                              result.get("task_id"))
                    if not task_id:
                        logger.error(f"❌ No task ID found in response: {result}")
                        raise ValueError("No task ID in prompt optimization response")

                    return {"id": task_id, "result": result}
            except aiohttp.ClientError as e:
                logger.error(f"❌ Error en nuevo prompt optimizer v3: {e}")
                raise

    async def get_prompt_optimizer_result(self, request_id: str) -> Dict[str, Any]:
        """
        Obtiene el resultado de una tarea de optimización de prompt (async)
        Normaliza la respuesta para incluir 'optimized_prompt' directamente
        """
        endpoint = f"{self.base_url}/api/v3/predictions/{request_id}/result"

        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.get(endpoint) as response:
                    response.raise_for_status()
                    raw_result = await response.json()
                    
                    # Log raw response for debugging
                    print(f"📋 Raw optimizer result: {raw_result}")
                    
                    # Extract data from response (API wraps in 'data' object)
                    data = raw_result.get("data", raw_result)
                    
                    # Normalize the response
                    normalized = {
                        "status": data.get("status"),
                        "raw_response": raw_result
                    }
                    
                    # Extract optimized prompt from outputs array (like other APIs)
                    if data.get("outputs") and len(data["outputs"]) > 0:
                        normalized["optimized_prompt"] = data["outputs"][0]
                        print(f"✅ Found optimized prompt in outputs: '{normalized['optimized_prompt'][:50]}...'")
                    elif data.get("result"):
                        # Alternative field name
                        normalized["optimized_prompt"] = data["result"]
                        print(f"✅ Found optimized prompt in result: '{normalized['optimized_prompt'][:50]}...'")
                    
                    return normalized
                    
            except aiohttp.ClientError as e:
                logger.error(f"❌ Error obteniendo resultado del prompt optimizer: {e}")
                raise

    def _format_download_error(self, error: Exception, video_url: str) -> str:
        """
        Formatea un mensaje de error detallado para problemas de descarga
        """
        error_type = type(error).__name__

        base_message = "❌ Error al descargar el video después de múltiples intentos.\n\n"

        if isinstance(error, asyncio.TimeoutError):
            base_message += "⏰ **Error de timeout**\n"
            base_message += "El servidor tardó demasiado en responder.\n\n"
        elif isinstance(error, aiohttp.ClientError):
            base_message += "🌐 **Error de conexión**\n"
            base_message += "No se pudo conectar al servidor de videos.\n\n"
        else:
            base_message += "📡 **Error desconocido**\n"
            base_message += f"Tipo: `{error_type}`\n\n"

        base_message += f"🔗 **URL del video:**\n{video_url}\n\n"
        base_message += "💡 Contacta al administrador si el problema persiste."

        return base_message

    async def optimize_prompt_text_only(self, text: str, mode: str = "video", style: str = "default") -> Dict[str, Any]:
        """
        Optimiza un prompt de texto solo (sin imagen) usando WaveSpeedAI
        Ahora usa modo asíncrono para consistencia y mejor manejo de timeouts
        """
        try:
            endpoint = f"{self.base_url}/api/v3/wavespeed-ai/prompt-optimizer"

            payload = {
                "enable_sync_mode": False,  # Cambiar a modo asíncrono para consistencia
                "image": "",  # Sin imagen
                "mode": mode,
                "style": style,
                "text": text
            }

            print(f"🤖 Optimizing text-only prompt: {text[:50]}...")
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.post(endpoint, json=payload) as response:
                    response.raise_for_status()
                    result = await response.json()
                    print("✅ Text-only prompt optimization request submitted")

                    # Extract the task ID from the response (can be nested in data)
                    task_id = (result.get("data", {}).get("id") or
                              result.get("id") or
                              result.get("request_id") or
                              result.get("task_id"))
                    if not task_id:
                        logger.error(f"❌ No task ID found in text-only optimization response: {result}")
                        raise ValueError("No task ID in text-only prompt optimization response")

                    # Poll for result immediately (text-only should be fast)
                    max_attempts = 10
                    for attempt in range(max_attempts):
                        try:
                            status_result = await self.get_prompt_optimizer_result(task_id)

                            if status_result.get("status") == "completed":
                                print("✅ Text-only prompt optimization completed")
                                return status_result
                            elif status_result.get("status") == "failed":
                                print("⚠️  Text-only prompt optimization failed on server side")
                                return {"optimized_prompt": text}  # Return original text

                            await asyncio.sleep(0.3)  # Shorter wait for text-only

                        except Exception as poll_error:
                            print(f"⚠️  Error polling text-only optimization: {poll_error}")
                            break

                    # If polling fails, return original text
                    print("⚠️  Text-only optimization polling failed, using original text")
                    return {"optimized_prompt": text}

        except Exception as e:
            print(f"❌ Text-only prompt optimization failed: {e}")
            # Return original text on failure
            return {"optimized_prompt": text}

    async def add_audio_to_video(self, video_url: str, prompt: str = "") -> Optional[str]:
        """
        Add audio/foley to a video using WavespeedAI audio API
        """
        try:
            # Audio generation API
            audio_url = f"{self.base_url}/api/v3/wavespeed-ai/hunyuan-video-foley"
            audio_payload = {
                "seed": -1,  # Random seed
                "video": video_url,
                "prompt": prompt  # Use the video prompt for better audio generation
            }

            print(f"🎵 Sending audio request for video: {video_url}")
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.post(audio_url, json=audio_payload) as response:
                    response.raise_for_status()
                    audio_result = await response.json()

                    if audio_result.get("data") and audio_result["data"].get("id"):
                        audio_request_id = audio_result["data"]["id"]
                        print(f"🎵 Audio generation started, request ID: {audio_request_id}")
                    else:
                        print(f"❌ Invalid audio API response: {audio_result}")
                        return None

            # Poll for audio completion
            audio_status_url = f"{self.base_url}/api/v3/predictions/{audio_request_id}/result"
            max_audio_attempts = 120  # ~2 minutes for audio

            for attempt in range(max_audio_attempts):
                try:
                    async with aiohttp.ClientSession(headers=self.headers) as session:
                        async with session.get(audio_status_url) as response:
                            if response.status == 200:
                                status_result = await response.json()

                                if status_result.get("data"):
                                    audio_data = status_result["data"]
                                    status = audio_data.get("status")

                                    if status == "completed":
                                        if audio_data.get("outputs") and len(audio_data["outputs"]) > 0:
                                            audio_video_url = audio_data["outputs"][0]
                                            print(f"🎵 Audio generation completed: {audio_video_url}")
                                            return audio_video_url

                                    elif status == "failed":
                                        error_msg = audio_data.get("error", "Audio generation failed")
                                        print(f"❌ Audio generation failed: {error_msg}")
                                        return None

                    print(f"⏳ Audio processing... ({attempt + 1}/{max_audio_attempts})")
                    await asyncio.sleep(1)

                except Exception as e:
                    print(f"⚠️  Audio polling error: {e}")
                    await asyncio.sleep(1)

            print("⏰ Audio generation timeout")
            return None

        except Exception as e:
            print(f"❌ Audio generation error: {e}")
            return None

    async def upscale_video_to_1080p(self, video_url: str) -> Optional[str]:
        """
        Upscale video to 1080P using WavespeedAI video upscaler pro
        """
        try:
            # Video upscale API
            upscale_url = f"{self.base_url}/api/v3/wavespeed-ai/video-upscaler-pro"
            upscale_payload = {
                "target_resolution": "1080p",
                "video": video_url
            }

            print(f"⬆️ Sending upscale request for video: {video_url}")
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.post(upscale_url, json=upscale_payload) as response:
                    response.raise_for_status()
                    upscale_result = await response.json()

                    if upscale_result.get("data") and upscale_result["data"].get("id"):
                        upscale_request_id = upscale_result["data"]["id"]
                        print(f"⬆️ Upscale generation started, request ID: {upscale_request_id}")
                    else:
                        print(f"❌ Invalid upscale API response: {upscale_result}")
                        return None

            # Poll for upscale completion
            upscale_status_url = f"{self.base_url}/api/v3/predictions/{upscale_request_id}/result"
            max_upscale_attempts = 120  # ~2 minutes for upscale

            for attempt in range(max_upscale_attempts):
                try:
                    async with aiohttp.ClientSession(headers=self.headers) as session:
                        async with session.get(upscale_status_url) as response:
                            if response.status == 200:
                                status_result = await response.json()

                                if status_result.get("data"):
                                    upscale_data = status_result["data"]
                                    status = upscale_data.get("status")

                                    if status == "completed":
                                        if upscale_data.get("outputs") and len(upscale_data["outputs"]) > 0:
                                            upscaled_video_url = upscale_data["outputs"][0]
                                            print(f"⬆️ Upscale completed: {upscaled_video_url}")
                                            return upscaled_video_url

                                    elif status == "failed":
                                        error_msg = upscale_data.get("error", "Upscale failed")
                                        print(f"❌ Upscale failed: {error_msg}")
                                        return None

                    print(f"⏫ Upscaling... ({attempt + 1}/{max_upscale_attempts})")
                    await asyncio.sleep(1)

                except Exception as e:
                    print(f"⚠️  Upscale polling error: {e}")
                    await asyncio.sleep(1)

            print("⏰ Upscale timeout")
            return None

        except Exception as e:
            print(f"❌ Upscale error: {e}")
            return None

    def get_available_models(self) -> Dict[str, Dict[str, Any]]:
        """
        Retorna información sobre los modelos disponibles
        """
        return {
            'ultra_fast': {
                'name': 'Ultra Fast 480p',
                'description': 'Video rápido en 480p, duración máxima 8s',
                'duration_max': 8,
                'resolution': '480p',
                'speed': 'ultra_fast'
            },
            'fast': {
                'name': 'Fast 480p',
                'description': 'Video rápido en 480p con mejor calidad',
                'duration_max': 8,
                'resolution': '480p',
                'speed': 'fast'
            },
            'quality': {
                'name': 'Quality 720p',
                'description': 'Video de alta calidad en 720p',
                'duration_max': 8,
                'resolution': '720p',
                'speed': 'quality'
            },
            'text_to_video': {
                'name': 'Text to Video 480p',
                'description': 'Genera video solo desde texto (sin imagen)',
                'duration_max': 8,
                'resolution': '480p',
                'speed': 'ultra_fast'
            }
        }
