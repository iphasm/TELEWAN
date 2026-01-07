import logging
import requests
import time
import io
import os
import uuid
import re
import subprocess
import asyncio
from datetime import datetime
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional
# Flask removido - ahora usamos FastAPI (ver fastapi_app.py)
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Message

# Import opcional para curl_cffi (se verifica después de definir logger)
CURL_CFFI_AVAILABLE = False
curl_requests = None

def _init_curl_cffi():
    """Inicializar curl_cffi si está disponible"""
    global CURL_CFFI_AVAILABLE, curl_requests
    try:
        from curl_cffi import requests as curl_req
        curl_requests = curl_req
        CURL_CFFI_AVAILABLE = True
        logger.info("✅ curl_cffi disponible para descargas avanzadas")
    except ImportError as e:
        CURL_CFFI_AVAILABLE = False
        logger.warning(f"⚠️ curl_cffi no disponible - usando solo yt-dlp: {e}")

# Filtros personalizados para imágenes
class ImageDocumentFilter:
    """Filtro para documentos que son imágenes"""
    def __call__(self, update):
        return self.check_update(update)

    def check_update(self, update):
        message = update.message or update.channel_post
        if message and message.document:
            mime_type = message.document.mime_type
            filename = message.document.file_name or ""

            # Log para debugging
            logger.debug(f"Documento recibido - MIME: {mime_type}, Filename: {filename}")

            if mime_type and mime_type.startswith('image/'):
                # Formatos de imagen comunes
                supported_formats = [
                    'image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif',
                    'image/bmp', 'image/tiff', 'image/tif', 'image/heic', 'image/heif',
                    'image/svg+xml', 'image/x-icon'
                ]

                # También verificar por extensión del archivo si el MIME no está claro
                image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.tiff', '.tif', '.heic', '.heif', '.svg', '.ico']
                has_image_extension = any(filename.lower().endswith(ext) for ext in image_extensions)

                mime_supported = mime_type.lower() in supported_formats
                extension_supported = has_image_extension

                result = mime_supported or extension_supported

                if result:
                    logger.info(f"✅ Documento de imagen aceptado - MIME: {mime_type}, Filename: {filename}")
                else:
                    logger.warning(f"❌ Documento de imagen rechazado - MIME: {mime_type}, Filename: {filename}")

                return result
        return False

class StaticStickerFilter:
    """Filtro para stickers estáticos (no animados)"""
    def __call__(self, update):
        return self.check_update(update)

    def check_update(self, update):
        message = update.message or update.channel_post
        if message and message.sticker:
            return not message.sticker.is_animated
        return False

# Instancias de los filtros
image_document_filter = ImageDocumentFilter()
static_sticker_filter = StaticStickerFilter()

class AsyncVideoProcessor:
    """
    Procesador asíncrono para manejar generación de videos de manera eficiente
    """
    def __init__(self, max_workers: int = 3):
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="video_processor")
        self.active_tasks: Dict[str, asyncio.Future] = {}
        self.logger = logging.getLogger(__name__)

    async def submit_video_generation(self, request_id: str, wavespeed_api: 'WavespeedAPI',
                                    prompt: str, image_url: str, model: str) -> str:
        """
        Envía una tarea de generación de video para procesamiento asíncrono

        Returns:
            request_id: ID de la solicitud para tracking
        """
        # Crear tarea asíncrona
        task = asyncio.get_event_loop().run_in_executor(
            self.executor,
            self._process_video_generation_sync,
            request_id, wavespeed_api, prompt, image_url, model
        )

        self.active_tasks[request_id] = task
        self.logger.info(f"🎬 Video task {request_id} submitted to async processor")
        return request_id

    def _process_video_generation_sync(self, request_id: str, wavespeed_api: 'WavespeedAPI',
                                     prompt: str, image_url: str, model: str) -> Dict[str, Any]:
        """
        Procesamiento síncrono de generación de video (ejecutado en thread pool)
        """
        try:
            self.logger.info(f"🔄 Procesando video {request_id} en thread separado")

            # Generar el video
            result = wavespeed_api.generate_video(prompt, image_url, model)

            if result.get('data') and result['data'].get('id'):
                task_id = result['data']['id']
                self.logger.info(f"✅ Video {request_id} generado exitosamente, task_id: {task_id}")
                return {
                    'status': 'success',
                    'request_id': request_id,
                    'task_id': task_id,
                    'result': result
                }
            else:
                raise Exception(f"Respuesta inválida de API: {result}")

        except Exception as e:
            self.logger.error(f"❌ Error procesando video {request_id}: {e}")
            return {
                'status': 'error',
                'request_id': request_id,
                'error': str(e)
            }

    async def wait_for_completion(self, request_id: str, timeout: int = 300) -> Optional[Dict[str, Any]]:
        """
        Espera a que se complete una tarea de generación de video

        Args:
            request_id: ID de la solicitud
            timeout: Timeout en segundos

        Returns:
            Resultado de la tarea o None si timeout
        """
        if request_id not in self.active_tasks:
            self.logger.error(f"Tarea {request_id} no encontrada")
            return None

        try:
            task = self.active_tasks[request_id]
            result = await asyncio.wait_for(task, timeout=timeout)
            del self.active_tasks[request_id]
            return result
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout esperando tarea {request_id}")
            return None
        except Exception as e:
            self.logger.error(f"Error esperando tarea {request_id}: {e}")
            return None

    def cancel_task(self, request_id: str) -> bool:
        """Cancela una tarea activa"""
        if request_id in self.active_tasks:
            task = self.active_tasks[request_id]
            task.cancel()
            del self.active_tasks[request_id]
            self.logger.info(f"🛑 Tarea {request_id} cancelada")
            return True
        return False

    def get_active_tasks_count(self) -> int:
        """Retorna el número de tareas activas"""
        return len(self.active_tasks)

    def cleanup_completed_tasks(self):
        """Limpia tareas completadas del diccionario"""
        completed = [rid for rid, task in self.active_tasks.items() if task.done()]
        for rid in completed:
            del self.active_tasks[rid]
        if completed:
            self.logger.debug(f"🧹 Limpias {len(completed)} tareas completadas")

from PIL import Image
from config import Config

# Instancia global del procesador asíncrono (inicializada después de importar Config)
async_video_processor = AsyncVideoProcessor(max_workers=Config.MAX_ASYNC_WORKERS)

# Configuración del logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Inicializar curl_cffi después de definir logger
_init_curl_cffi()

# Prompt por defecto cuando no se proporciona caption (configurable via env)
DEFAULT_PROMPT = os.getenv('DEFAULT_PROMPT', '')


def generate_serial_filename(prefix: str, extension: str) -> str:
    """
    Genera un nombre de archivo único con timestamp y UUID
    Formato: {prefix}_{timestamp}_{uuid}.{extension}
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]  # Primeros 8 caracteres del UUID
    return f"{prefix}_{timestamp}_{unique_id}.{extension}"

def ensure_storage_directory():
    """
    Asegura que el directorio de almacenamiento existe
    """
    os.makedirs(Config.VOLUME_PATH, exist_ok=True)
    return Config.VOLUME_PATH

def save_image_to_volume(image_bytes: bytes, filename: str) -> str:
    """
    Guarda una imagen en el volumen y retorna la ruta completa
    """
    storage_dir = ensure_storage_directory()
    filepath = os.path.join(storage_dir, filename)

    with open(filepath, 'wb') as f:
        f.write(image_bytes)

    logger.info(f"Imagen guardada en: {filepath}")
    return filepath

def save_video_to_volume(video_bytes: bytes, filename: str) -> str:
    """
    Guarda un video en el volumen y retorna la ruta completa
    """
    storage_dir = ensure_storage_directory()
    filepath = os.path.join(storage_dir, filename)

    with open(filepath, 'wb') as f:
        f.write(video_bytes)

    logger.info(f"Video guardado en: {filepath}")
    return filepath

def calculate_smart_polling_interval(attempt: int, total_attempts: int, base_interval: float = 0.5) -> float:
    """
    Calcula intervalos de polling inteligentes con exponential backoff adaptativo

    Args:
        attempt: Número de intento actual (0-based)
        total_attempts: Número total de intentos permitidos
        base_interval: Intervalo base en segundos

    Returns:
        Intervalo de polling en segundos
    """
    # Estrategia adaptativa:
    # - Primeros 10 intentos: polling rápido (0.5s) para detectar cambios tempranos
    # - Intentos 10-30: polling medio (1-2s) con ligero backoff
    # - Intentos 30+: polling lento (3-5s) con exponential backoff

    if attempt < 10:
        # Polling rápido inicial para detectar cambios inmediatos
        return base_interval
    elif attempt < 30:
        # Polling medio con backoff lineal
        return min(base_interval * 2, base_interval + (attempt - 10) * 0.1)
    else:
        # Polling lento con exponential backoff
        # Fórmula: base_interval * 2^(attempt/20) con límite superior
        backoff_factor = 2 ** ((attempt - 30) / 20)
        return min(base_interval * 4 * backoff_factor, 10.0)  # Máximo 10 segundos

def cleanup_old_downloads(context, chat_id):
    """
    Limpia entradas antiguas de descargas del contexto del usuario para evitar memory leaks
    """
    try:
        # Buscar y eliminar entradas de descargas antiguas (más de 1 hora)
        import time
        current_time = time.time()
        one_hour_ago = current_time - 3600  # 1 hora en segundos

        keys_to_remove = []
        for key, value in context.user_data.items():
            if key.startswith('downloaded_'):
                # Si la entrada no tiene timestamp, asumir que es antigua
                if isinstance(value, dict) and 'timestamp' in value:
                    if value['timestamp'] < one_hour_ago:
                        keys_to_remove.append(key)
                elif isinstance(value, bool) and value == True:
                    # Para entradas booleanas simples, considerarlas como antiguas después de cierto tiempo
                    # Como no tenemos timestamp, las limpiamos después de procesar
                    keys_to_remove.append(key)

        for key in keys_to_remove:
            del context.user_data[key]
            logger.debug(f"🧹 Limpiada entrada antigua de descarga: {key}")

        if keys_to_remove:
            logger.info(f"🧹 Limpieza completada: {len(keys_to_remove)} entradas antiguas eliminadas para chat {chat_id}")
        else:
            logger.debug(f"🧹 No hay entradas antiguas para limpiar en chat {chat_id}")

    except Exception as cleanup_error:
        logger.warning(f"⚠️ Error limpiando descargas antiguas: {cleanup_error}")
        # No fallar el procesamiento principal por un error de limpieza

class WavespeedAPI:
    def __init__(self):
        self.api_key = Config.WAVESPEED_API_KEY
        self.base_url = Config.WAVESPEED_BASE_URL
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    def generate_video(self, prompt: str, image_url: str = None, model: str = None, webhook_url: str = None) -> dict:
        """
        Genera un video usando diferentes modelos de Wavespeed AI

        Args:
            prompt: Descripción del video a generar
            image_url: URL de la imagen de referencia (opcional para text-to-video)
            model: Modelo a usar ('ultra_fast', 'fast', 'quality', 'text_to_video')
            webhook_url: URL de webhook para notificaciones (si soportado por la API)
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

        # Agregar webhook si está configurado y soportado por la API
        if webhook_url:
            payload["webhook_url"] = webhook_url
            logger.info(f"Webhook configurado para notificaciones: {webhook_url}")

        # Solo incluir imagen si no es text-to-video o si se proporciona
        if image_url and model != 'text_to_video':
            payload["image"] = image_url
            payload["last_image"] = ""
        elif model == 'text_to_video' and image_url:
            # Para text-to-video con imagen de referencia opcional
            payload["image"] = image_url
            payload["last_image"] = ""

        try:
            response = requests.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en la API de Wavespeed: {e}")
            raise

    def get_video_status(self, request_id: str) -> dict:
        """
        Obtiene el estado de una tarea de generación de video
        """
        endpoint = f"{self.base_url}/api/v3/predictions/{request_id}/result"

        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error obteniendo estado del video: {e}")
            raise

    def download_video(self, video_url: str, timeout: int = 30, model: str = 'ultra_fast') -> bytes:
        """
        Descarga el video generado con mejor manejo de errores
        Ajusta timeout según el modelo para videos de calidad
        """
        # Ajustar timeout según el modelo
        if model == 'quality':
            # Videos 720p necesitan más tiempo (hasta 3 minutos)
            timeout = max(timeout, 180)  # 3 minutos mínimo
            logger.info(f"🎯 Video de CALIDAD detectado - Timeout extendido a {timeout} segundos")
        elif model == 'fast':
            timeout = max(timeout, 90)  # 1.5 minutos para fast
        else:
            timeout = max(timeout, 60)  # 1 minuto para ultra_fast

        try:
            logger.info(f"📥 Iniciando descarga de video desde: {video_url[:50]}...")
            logger.info(f"   Modelo: {model} | Timeout configurado: {timeout} segundos")

            # Hacer la petición con timeout y headers
            headers = {
                'User-Agent': 'TELEWAN-Bot/1.0',
                'Accept': 'video/mp4,video/*,*/*'
            }

            response = requests.get(
                video_url,
                timeout=timeout,
                headers=headers,
                stream=True  # Para mejor manejo de archivos grandes
            )

            response.raise_for_status()

            # Verificar el tipo de contenido
            content_type = response.headers.get('content-type', '')
            logger.info(f"   Content-Type: {content_type}")
            logger.info(f"   Content-Length: {response.headers.get('content-length', 'unknown')}")

            # Verificar que sea un video
            if not content_type.startswith('video/'):
                logger.warning(f"⚠️  Content-Type inesperado: {content_type}")

            # Descargar el contenido
            content = response.content
            logger.info(f"✅ Video descargado exitosamente: {len(content)} bytes")

            # Validaciones exhaustivas del archivo descargado
            self._validate_video_integrity(content, model)

            return content

        except requests.exceptions.Timeout as e:
            logger.error(f"⏰ Timeout descargando video ({timeout}s): {e}")
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"🌐 Error de conexión descargando video: {e}")
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f"🔴 Error HTTP descargando video: {e}")
            logger.error(f"   Status Code: {response.status_code if 'response' in locals() else 'unknown'}")
            logger.error(f"   Response: {response.text[:200] if 'response' in locals() else 'no response'}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"📡 Error general descargando video: {e}")
            raise
        except Exception as e:
            logger.error(f"💥 Error inesperado descargando video: {e}")
            raise

    def _format_download_error(self, error: Exception, video_url: str) -> str:
        """
        Formatea un mensaje de error detallado para problemas de descarga
        """
        error_type = type(error).__name__

        base_message = "❌ Error al descargar el video después de múltiples intentos.\n\n"

        if isinstance(error, requests.exceptions.Timeout):
            base_message += "⏰ **Error de timeout**\n"
            base_message += "El servidor tardó demasiado en responder.\n\n"
        elif isinstance(error, requests.exceptions.ConnectionError):
            base_message += "🌐 **Error de conexión**\n"
            base_message += "No se pudo conectar al servidor de videos.\n\n"
        elif isinstance(error, requests.exceptions.HTTPError):
            base_message += "🔴 **Error del servidor**\n"
            base_message += f"El servidor respondió con error HTTP.\n\n"
        else:
            base_message += "📡 **Error desconocido**\n"
            base_message += f"Tipo: `{error_type}`\n\n"

        base_message += f"🔗 **URL del video:**\n{video_url}\n\n"
        base_message += "💡 Contacta al administrador si el problema persiste."

        return base_message

    def _validate_video_integrity(self, video_bytes: bytes, model: str) -> None:
        """
        Valida que el video descargado esté completo y sea válido
        Realiza validaciones más estrictas para videos de calidad
        """
        file_size = len(video_bytes)

        # Validación básica de tamaño mínimo
        if file_size < 1000:
            raise ValueError(f"Archivo descargado demasiado pequeño: {file_size} bytes")

        # Validaciones específicas por modelo
        if model == 'quality':
            # Videos 720p deben ser más grandes (mínimo ~500KB para videos cortos)
            min_size_quality = 500 * 1024  # 500KB
            if file_size < min_size_quality:
                raise ValueError(f"Video de calidad demasiado pequeño: {file_size:,} bytes (mínimo: {min_size_quality:,} bytes)")
            logger.info(f"✅ Video de CALIDAD validado: {file_size:,} bytes")

        elif model == 'fast':
            # Videos fast deben ser razonables (~200KB mínimo)
            min_size_fast = 200 * 1024  # 200KB
            if file_size < min_size_fast:
                raise ValueError(f"Video fast demasiado pequeño: {file_size:,} bytes (mínimo: {min_size_fast:,} bytes)")

        else:
            # Videos ultra_fast pueden ser más pequeños (~50KB mínimo)
            min_size_ultra = 50 * 1024  # 50KB
            if file_size < min_size_ultra:
                raise ValueError(f"Video ultra_fast demasiado pequeño: {file_size:,} bytes (mínimo: {min_size_ultra:,} bytes)")

        # Validación de firma MP4 básica (primeros bytes)
        if len(video_bytes) >= 12:
            # MP4 files typically start with 'ftyp' box after 'moov' or similar
            # Check for common video file signatures
            header = video_bytes[:12]
            if not any(sig in header for sig in [b'ftyp', b'moov', b'mdat', b'free']):
                logger.warning(f"⚠️  Firma de video no reconocida en header: {header[:8].hex()}")

        logger.info(f"✅ Video validado: {file_size:,} bytes, modelo: {model}")

    def generate_text_to_video(self, prompt: str, model: str = 'text_to_video') -> dict:
        """
        Genera un video solo desde texto (sin imagen de referencia)
        """
        return self.generate_video(prompt, image_url=None, model=model)

    def generate_enhanced_video(self, prompt: str, image_url: str, quality: str = 'quality') -> dict:
        """
        Genera un video de alta calidad (720p) desde imagen
        """
        return self.generate_video(prompt, image_url, model=quality)

    def generate_quick_preview(self, prompt: str, image_url: str = None, model: str = 'ultra_fast') -> dict:
        """
        Genera una preview rápida (480p ultra fast)
        """
        return self.generate_video(prompt, image_url, model=model)

    def optimize_prompt_v3(self, image_url: str, text: str, mode: str = "video", style: str = "default") -> dict:
        """
        Optimiza un prompt usando la nueva API v3 de WaveSpeedAI

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

        logger.info(f"Calling new prompt optimizer v3: image={image_url[:50]}..., text='{text}', mode={mode}, style={style}")

        try:
            response = requests.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en nuevo prompt optimizer v3: {e}")
            raise

    def get_prompt_optimizer_result(self, request_id: str) -> dict:
        """
        Obtiene el resultado de una tarea de optimización de prompt
        """
        endpoint = f"{self.base_url}/api/v3/predictions/{request_id}/result"

        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error obteniendo resultado del prompt optimizer: {e}")
            raise

    def get_balance(self) -> dict:
        """
        Consulta el balance/creditos disponibles en la cuenta de Wavespeed
        Según documentación oficial: GET /api/v3/balance
        Respuesta: {code: 200, message: "success", data: {balance: X.XX}}
        """
        try:
            # Endpoint oficial según documentación 2026
            endpoint = '/api/v3/balance'
            url = f"{self.base_url}{endpoint}"

            logger.info(f"Consultando balance en: {url}")

            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            logger.info(f"Respuesta de balance obtenida: {data}")

            # Validar estructura de respuesta según documentación
            if data.get('code') == 200 and data.get('message') == 'success':
                balance_data = data.get('data', {})
                balance = balance_data.get('balance')

                if balance is not None:
                    logger.info(f"Balance obtenido exitosamente: ${balance}")
                    return {
                        'success': True,
                        'balance': balance,
                        'currency': 'USD',
                        'raw_response': data
                    }
                else:
                    logger.warning("Balance no encontrado en respuesta")
                    return {
                        'error': 'Balance not found',
                        'message': 'El balance no está disponible en la respuesta',
                        'raw_response': data
                    }
            else:
                # Respuesta con código de error
                error_code = data.get('code', 'unknown')
                error_message = data.get('message', 'unknown error')
                logger.warning(f"Error en respuesta de balance: {error_code} - {error_message}")
                return {
                    'error': f'API Error {error_code}',
                    'message': error_message,
                    'raw_response': data
                }

        except requests.exceptions.HTTPError as e:
            error_code = e.response.status_code
            try:
                error_data = e.response.json()
                error_message = error_data.get('message', 'HTTP Error')
            except:
                error_message = str(e)

            logger.error(f"Error HTTP consultando balance ({error_code}): {error_message}")
            return {
                'error': f'HTTP {error_code}',
                'message': error_message,
                'http_status': error_code
            }

        except requests.exceptions.Timeout:
            logger.error("Timeout consultando balance")
            return {
                'error': 'Timeout',
                'message': 'La consulta de balance tardó demasiado tiempo'
            }

        except requests.exceptions.ConnectionError:
            logger.error("Error de conexión consultando balance")
            return {
                'error': 'Connection Error',
                'message': 'No se pudo conectar al servidor de Wavespeed'
            }

        except Exception as e:
            logger.error(f"Error crítico consultando balance: {e}")
            return {
                'error': str(type(e).__name__),
                'message': f'Error interno: {str(e)}'
            }

    def get_available_models(self) -> dict:
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


class VideoDownloader:
    """Clase para descargar videos de redes sociales"""

    SUPPORTED_PLATFORMS = {
        'facebook.com': 'Facebook',
        'fb.com': 'Facebook',
        'instagram.com': 'Instagram',
        'instagr.am': 'Instagram',
        'twitter.com': 'X (Twitter)',
        'x.com': 'X (Twitter)',
        'reddit.com': 'Reddit',
        'tiktok.com': 'TikTok',
        'vm.tiktok.com': 'TikTok'
    }

    def __init__(self):
        self.temp_dir = Config.VOLUME_PATH

    def detect_platform(self, url: str) -> str:
        """Detecta la plataforma de redes sociales desde la URL"""
        try:
            domain = urlparse(url).netloc.lower()
            for platform_domain, platform_name in self.SUPPORTED_PLATFORMS.items():
                if platform_domain in domain:
                    return platform_name
            return None
        except Exception as e:
            logger.error(f"Error detectando plataforma para URL {url}: {e}")
            return None

    def is_valid_social_url(self, url: str) -> bool:
        """Verifica si la URL es de una red social soportada"""
        platform = self.detect_platform(url)
        return platform is not None

    def download_video_curl_cffi(self, url: str, platform: str) -> dict:
        """
        Descarga un video usando curl_cffi con impersonación de navegador
        Método principal para todas las plataformas soportadas
        """
        if not CURL_CFFI_AVAILABLE:
            return {
                'success': False,
                'error': 'curl_cffi no disponible'
            }

        try:
            logger.info(f"🔧 Intentando descarga con curl_cffi para {platform}")

            # Configuración específica por plataforma
            impersonate_target = "chrome124"  # Chrome moderno por defecto

            if platform == 'TikTok':
                # TikTok funciona mejor con Safari iOS
                impersonate_target = "safari18_ios"
            elif platform in ['Facebook', 'Instagram']:
                # Facebook/Instagram funcionan bien con Chrome
                impersonate_target = "chrome124"

            # Headers adicionales para mejor impersonación
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

            # Primera petición para obtener información del video
            logger.info(f"🌐 Consultando URL con impersonación: {impersonate_target}")
            response = curl_requests.get(
                url,
                impersonate=impersonate_target,
                headers=headers,
                timeout=30,
                allow_redirects=True
            )

            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'Error HTTP {response.status_code}: {response.text[:100]}...'
                }

            # Buscar URLs de video en la respuesta (JSON o HTML)
            content = response.text

            # Lógica específica por plataforma para extracción de datos
            if platform == 'TikTok':
                # Buscar patrones comunes de URLs de video en TikTok
                video_patterns = [
                    r'"playAddr":"([^"]+)"',
                    r'"downloadAddr":"([^"]+)"',
                    r'playAddr["\s]*:[\s]*"([^"]+)"',
                    r'https://v\d+\.ttcdn\.cn[^"\s]+',
                    r'https://v\d+\.bytecdn\.cn[^"\s]+'
                ]

                video_url = None
                for pattern in video_patterns:
                    match = re.search(pattern, content)
                    if match:
                        video_url = match.group(1).replace('\\u0026', '&').replace('\\', '')
                        if video_url.startswith('http'):
                            logger.info(f"🎥 URL de video encontrada: {video_url[:100]}...")
                            break

                if not video_url:
                    return {
                        'success': False,
                        'error': 'No se pudo encontrar la URL del video en la respuesta de TikTok'
                    }

                # Descargar el video real
                logger.info("📥 Descargando video desde URL encontrada")
                video_response = curl_requests.get(
                    video_url,
                    impersonate=impersonate_target,
                    headers=headers,
                    timeout=60
                )

                if video_response.status_code != 200:
                    return {
                        'success': False,
                        'error': f'Error descargando video: HTTP {video_response.status_code}'
                    }

                # Extraer metadatos del JSON de TikTok
                title = "TikTok Video"
                duration = 0

                # Buscar título en el JSON
                title_patterns = [
                    r'"desc":"([^"]+)"',
                    r'"text":"([^"]+)"',
                    r'title["\s]*:[\s]*"([^"]+)"'
                ]

                for pattern in title_patterns:
                    match = re.search(pattern, content)
                    if match:
                        title = match.group(1).replace('\\n', ' ').strip()
                        break

                # Guardar el video
                video_bytes = video_response.content
                file_size = len(video_bytes)

                # Validar tamaño mínimo
                if file_size < 10000:  # 10KB mínimo
                    return {
                        'success': False,
                        'error': f'Video descargado demasiado pequeño: {file_size} bytes'
                    }

                video_filename = generate_serial_filename("tiktok_curl", "mp4")
                video_filepath = save_video_to_volume(video_bytes, video_filename)

                return {
                    'success': True,
                    'filepath': video_filepath,
                    'title': title,
                    'duration': duration,
                    'platform': platform,
                    'file_size': file_size,
                    'method': 'curl_cffi'
                }

            else:
                # Para otras plataformas (Facebook, Instagram, etc.), intentar descarga directa
                logger.info(f"🎯 Intentando descarga directa para {platform}")

                # Para estas plataformas, la URL directa debería funcionar
                video_response = curl_requests.get(
                    url,
                    impersonate=impersonate_target,
                    headers=headers,
                    timeout=60,
                    allow_redirects=True
                )

                if video_response.status_code != 200:
                    return {
                        'success': False,
                        'error': f'Error accediendo a {platform}: HTTP {video_response.status_code}'
                    }

                # Verificar si la respuesta contiene un video
                content_type = video_response.headers.get('content-type', '').lower()

                # Si es un video directo, guardarlo
                if 'video/' in content_type or 'mp4' in content_type:
                    video_bytes = video_response.content
                    file_size = len(video_bytes)

                    if file_size < 10000:  # 10KB mínimo
                        return {
                            'success': False,
                            'error': f'Contenido descargado demasiado pequeño: {file_size} bytes'
                        }

                    # Extraer título del URL o usar genérico
                    title = f"{platform} Video"
                    duration = 0  # No podemos determinar duración sin metadata

                    video_filename = generate_serial_filename(f"{platform.lower().replace(' ', '_')}_curl", "mp4")
                    video_filepath = save_video_to_volume(video_bytes, video_filename)

                    return {
                        'success': True,
                        'filepath': video_filepath,
                        'title': title,
                        'duration': duration,
                        'platform': platform,
                        'file_size': file_size,
                        'method': 'curl_cffi'
                    }

                else:
                    # No es un video directo, probablemente una página HTML
                    # Esto requiere parsing más complejo que yt-dlp maneja mejor
                    return {
                        'success': False,
                        'error': f'{platform} requiere parsing HTML complejo, usar yt-dlp'
                    }

        except Exception as e:
            logger.error(f"Error en curl_cffi para {platform}: {e}")
            return {
                'success': False,
                'error': f'Error con curl_cffi: {str(e)}'
            }

    def download_video(self, url: str) -> dict:
        """
        Descarga un video de redes sociales usando curl_cffi (primer método) con fallback a yt-dlp

        Returns:
            dict: {
                'success': bool,
                'filepath': str (si éxito),
                'title': str,
                'duration': int,
                'platform': str,
                'method': str,  # 'curl_cffi' o 'yt-dlp'
                'error': str (si fallo)
            }
        """
        try:
            platform = self.detect_platform(url)
            if not platform:
                return {
                    'success': False,
                    'error': 'Plataforma no soportada. Solo Facebook, Instagram, X/Twitter, Reddit y TikTok.'
                }

            logger.info(f"📥 Descargando video de {platform}: {url}")

            # Usar curl_cffi como primer método si está disponible
            if CURL_CFFI_AVAILABLE:
                logger.info("🎯 Intentando curl_cffi como primer método")
                curl_result = self.download_video_curl_cffi(url, platform)
                if curl_result['success']:
                    logger.info("✅ curl_cffi funcionó exitosamente")
                    return curl_result
                else:
                    logger.warning(f"⚠️ curl_cffi falló: {curl_result.get('error', 'Unknown error')}")
                    logger.info("🔄 Intentando con yt-dlp (con impersonation avanzada) como fallback")

            # Si curl_cffi no está disponible o falló, usar yt-dlp con impersonation

            # Fallback a yt-dlp
            video_id = str(uuid.uuid4())[:8]
            output_template = os.path.join(self.temp_dir, f'social_video_{video_id}.%(ext)s')

            # Comando yt-dlp optimizado para videos sociales
            cmd = [
                'yt-dlp',
                '--no-check-certificates',
                '--no-playlist',
                '--max-filesize', '100M',  # Límite de 100MB
                '--format', 'best[height<=720]',  # Calidad máxima 720p
                '--output', output_template,
                '--print', '%(title)s',
                '--print', '%(duration)s',
                '--print', '%(ext)s',
            ]

            # Configuración para yt-dlp con impersonation avanzada
            # Necesaria para plataformas modernas que bloquean requests simples
            cmd.extend([
                '--user-agent', 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
                '--add-header', 'Accept-Language: en-US,en;q=0.9',
                '--add-header', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                '--add-header', 'Sec-Ch-Ua-Mobile: ?1',
                '--add-header', 'Sec-Ch-Ua-Platform: "iOS"',
            ])

            # Configuración de impersonation específica por plataforma
            if platform == 'TikTok':
                # Usar impersonation de Safari iOS para TikTok
                cmd.extend([
                    '--impersonate', 'safari-ios:17.5.1',
                    '--add-header', 'Referer: https://www.tiktok.com/',
                    '--add-header', 'Sec-Fetch-Dest: document',
                    '--add-header', 'Sec-Fetch-Mode: navigate',
                    '--add-header', 'Sec-Fetch-Site: none',
                ])
            elif platform == 'Instagram':
                # Usar impersonation de Safari iOS para Instagram
                cmd.extend([
                    '--impersonate', 'safari-ios:17.5.1',
                    '--add-header', 'Referer: https://www.instagram.com/',
                    '--add-header', 'X-Requested-With: XMLHttpRequest',
                ])
            elif platform == 'Facebook':
                # Usar impersonation de Chrome para Facebook
                cmd.extend([
                    '--impersonate', 'chrome-120',
                    '--add-header', 'Referer: https://www.facebook.com/',
                ])
            elif platform == 'X/Twitter':
                # Usar impersonation de Safari para Twitter/X
                cmd.extend([
                    '--impersonate', 'safari-17',
                    '--add-header', 'Referer: https://twitter.com/',
                    '--add-header', 'Authorization: Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
                ])
            elif platform == 'Reddit':
                # Usar impersonation básica para Reddit
                cmd.extend([
                    '--impersonate', 'chrome-120',
                    '--add-header', 'Referer: https://www.reddit.com/',
                ])

            # Agregar la URL al final
            cmd.append(url)

            logger.info(f"Ejecutando comando: {' '.join(cmd)}")

            # Ejecutar yt-dlp
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2 minutos timeout
            )

            if result.returncode != 0:
                logger.error(f"Error en yt-dlp: {result.stderr}")

                # Intentar con configuración básica si la impersonation falló
                if 'impersonate' in ' '.join(cmd) and 'no impersonate target is available' in result.stderr:
                    logger.info("🔄 Intentando con configuración básica (sin impersonation) como último recurso")
                    basic_cmd = [
                        'yt-dlp',
                        '--no-check-certificates',
                        '--no-playlist',
                        '--max-filesize', '50M',  # Reducir límite para videos más pequeños
                        '--format', 'best[height<=480]',  # Calidad más baja
                        '--output', output_template,
                        '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        '--add-header', 'Accept-Language: en-US,en;q=0.9',
                        url
                    ]

                    basic_result = subprocess.run(
                        basic_cmd,
                        capture_output=True,
                        text=True,
                        timeout=60  # Timeout más corto
                    )

                    if basic_result.returncode == 0:
                        logger.info("✅ Configuración básica funcionó como último recurso")
                        # Procesar resultado exitoso
                        lines = basic_result.stdout.strip().split('\n')
                        if len(lines) >= 3:
                            title = lines[0] if lines[0] else f"Video de {platform}"
                            duration = int(float(lines[1])) if lines[1].isdigit() else 0
                            ext = lines[2] if lines[2] else 'mp4'

                            # Encontrar el archivo descargado
                            for file in os.listdir(self.temp_dir):
                                if file.startswith(f'social_video_{video_id}') and file.endswith(f'.{ext}'):
                                    filepath = os.path.join(self.temp_dir, file)
                                    file_size = os.path.getsize(filepath)

                                    return {
                                        'success': True,
                                        'filepath': filepath,
                                        'title': title,
                                        'duration': duration,
                                        'platform': platform,
                                        'method': 'yt-dlp-basic',
                                        'file_size': file_size
                                    }

                # Si todo falló
                error_msg = result.stderr[:200] + "..." if len(result.stderr) > 200 else result.stderr
                return {
                    'success': False,
                    'error': f'Error descargando video: {error_msg}\n\n💡 También puedes usar /download [URL] para intentar manualmente.'
                }

            # Parsear la salida
            output_lines = result.stdout.strip().split('\n')
            if len(output_lines) < 3:
                return {
                    'success': False,
                    'error': 'No se pudo obtener información del video'
                }

            title = output_lines[0].strip()
            duration_str = output_lines[1].strip()
            extension = output_lines[2].strip()

            try:
                duration = int(float(duration_str))
            except:
                duration = 0

            # Encontrar el archivo descargado
            video_filename = f'social_video_{video_id}.{extension}'
            video_filepath = os.path.join(self.temp_dir, video_filename)

            if not os.path.exists(video_filepath):
                return {
                    'success': False,
                    'error': 'Video descargado pero archivo no encontrado'
                }

            # Verificar tamaño del archivo
            file_size = os.path.getsize(video_filepath)
            logger.info(f"✅ Video descargado: {video_filepath} ({file_size:,} bytes)")

            return {
                'success': True,
                'filepath': video_filepath,
                'title': title,
                'duration': duration,
                'platform': platform,
                'file_size': file_size
            }

        except subprocess.TimeoutExpired:
            logger.error("Timeout descargando video")
            return {
                'success': False,
                'error': 'Timeout: La descarga tomó demasiado tiempo (máx 2 minutos)'
            }

        except subprocess.TimeoutExpired:
            logger.error("Timeout descargando video de red social")
            return {
                'success': False,
                'error': 'Timeout: La descarga tomó demasiado tiempo (máx 2 minutos). El video puede ser muy largo o el servidor está lento.'
            }

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)

            # Mensajes de error más específicos
            if 'Video unavailable' in error_msg or 'not available' in error_msg:
                error = 'Video no disponible: El video puede haber sido eliminado o ser privado.'
            elif 'Unsupported URL' in error_msg:
                error = 'URL no soportada: Verifica que la URL sea correcta.'
            elif 'Private video' in error_msg:
                error = 'Video privado: No se puede acceder a videos privados.'
            elif 'Age-restricted' in error_msg:
                error = 'Video con restricción de edad: No se puede descargar contenido con restricción de edad.'
            elif 'Geo-blocked' in error_msg:
                error = 'Video geo-bloqueado: El contenido no está disponible en tu región.'
            elif 'impersonat' in error_msg.lower():
                error = 'Error de acceso: Problema técnico con la plataforma. Inténtalo más tarde.'
            else:
                error = f'Error de descarga: {error_msg[:150]}...'

            logger.error(f"Error en yt-dlp: {error_msg}")
            return {
                'success': False,
                'error': error,
                'platform': platform
            }

        except Exception as e:
            logger.error(f"Error crítico descargando video: {e}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}'
            }

    def cleanup_file(self, filepath: str) -> bool:
        """Elimina un archivo del sistema de archivos"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"🗑️ Archivo eliminado: {filepath}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error eliminando archivo {filepath}: {e}")
            return False


# Instancia global del downloader
video_downloader = VideoDownloader()

def optimize_user_prompt_v3(image_url: str, text: str, mode: str = "video", style: str = "default") -> str:
    """
    Optimiza un prompt usando la nueva API v3 de WaveSpeedAI
    """
    try:
        wavespeed = WavespeedAPI()

        # Iniciar optimización con la nueva API
        result = wavespeed.optimize_prompt_v3(
            image_url=image_url,
            text=text,
            mode=mode,
            style=style
        )

        if result.get('data') and result['data'].get('id'):
            request_id = result['data']['id']
            logger.info(f"New prompt optimization started. Request ID: {request_id}")

            # Esperar resultado (máximo 30 segundos)
            max_attempts = 300  # 30 segundos con polling de 0.1s
            attempt = 0

            while attempt < max_attempts:
                try:
                    status_result = wavespeed.get_prompt_optimizer_result(request_id)

                    if status_result.get('data'):
                        task_data = status_result['data']
                        status = task_data.get('status')

                        if status == 'completed':
                            if task_data.get('outputs') and len(task_data['outputs']) > 0:
                                optimized_text = task_data['outputs'][0]
                                logger.info(f"New optimizer result: {optimized_text[:100]}...")
                                logger.info(f"Original text: '{text}'")
                                logger.info(f"Optimization completed in {attempt * 0.1:.1f} seconds")
                                return optimized_text
                            else:
                                logger.warning("New prompt optimization completed but no outputs")
                                break

                        elif status == 'failed':
                            error_msg = task_data.get('error', 'Unknown error')
                            logger.error(f"New prompt optimization failed: {error_msg}")
                            break

                    attempt += 1
                    time.sleep(0.1)

                except Exception as poll_error:
                    logger.error(f"Error polling new optimizer status: {poll_error}")
                    attempt += 1
                    time.sleep(0.1)

            logger.warning("New prompt optimization timed out or failed, using original text")
            return text

        else:
            logger.error(f"Failed to start new prompt optimization. API Response: {result}")
            return text

    except Exception as e:
        logger.error(f"Critical error in new prompt optimization: {e}")
        return text

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador del comando /start"""
    user_id = update.effective_user.id

    # Verificar autenticación si está configurada
    if Config.ALLOWED_USER_ID and str(user_id) != Config.ALLOWED_USER_ID:
        await update.message.reply_text(Config.ACCESS_DENIED_MESSAGE)
        logger.warning(f"Acceso denegado para usuario {user_id} en /start")
        return

    await update.message.reply_text(Config.WELCOME_MESSAGE, parse_mode='Markdown')

def is_image_message(message) -> tuple[bool, str, str]:
    """
    Verifica si un mensaje contiene una imagen usando múltiples métodos de detección
    Esta función es usada por handle_image_message para validar antes del procesamiento

    Returns:
        tuple: (is_image, image_type, error_message)
    """
    # Método 1: Foto directa (photo array)
    if message.photo and len(message.photo) > 0:
        return True, "photo", ""

    # Método 2: Documento que es imagen (por MIME type)
    if message.document:
        mime_type = message.document.mime_type
        if mime_type and mime_type.startswith('image/'):
            # Tipos de imagen soportados
            supported_formats = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif']
            if mime_type.lower() in supported_formats:
                return True, "document", ""
            else:
                return False, "", f"❌ Formato de imagen no soportado: {mime_type}.\n\n💡 **Formatos aceptados:** JPG, PNG, WebP, GIF"

    # Método 3: Sticker estático (no animado)
    if message.sticker and not message.sticker.is_animated:
        return True, "sticker", ""

    # Método 4: Verificar si es un forward de un mensaje con foto
    if message.forward_origin and hasattr(message.forward_origin, 'photo') and message.forward_origin.photo:
        # Es un forward de una foto, pero no tenemos acceso directo a la foto
        return False, "", "❌ Para forwards de fotos, reenvía la imagen con el caption incluido."

            # Si no se detectó ninguna imagen
    return False, "", (
        "❌ No se detectó ninguna imagen en tu mensaje.\n\n"
        "📸 **Formatos aceptados:**\n"
        "• **Fotos:** JPG, PNG, WebP, GIF (desde galería/cámara)\n"
        "• **Documentos:** JPG, PNG, WebP, GIF, BMP, TIFF, HEIC, HEIF, SVG\n"
        "• **Stickers:** Estáticos (no animados)\n\n"
        "💡 **Tips para archivos:**\n"
        "• Si envías como documento, asegúrate que tenga extensión de imagen\n"
        "• Prueba reenviando la imagen como foto en lugar de documento\n"
        "• Usa `/debugfiles` para más información\n\n"
        "🎯 Incluye un **caption descriptivo** con tu imagen."
    )

async def handle_image_message(update: Update, context: ContextTypes.DEFAULT_TYPE, image_type: str = "photo") -> None:
    """
    Manejador genérico para mensajes con imágenes (fotos, documentos, stickers)
    """
    try:
        message = update.message
        if not message:
            logger.error("Mensaje vacío recibido")
            return

        user_id = message.from_user.id if message.from_user else "unknown"

        # Logging detallado del mensaje recibido
        logger.info(f"🎯 Procesando mensaje de tipo: {image_type}")
        logger.info(f"   Usuario: {user_id}")
        logger.info(f"   Tiene photo: {message.photo is not None}")
        logger.info(f"   Tiene document: {message.document is not None}")
        logger.info(f"   Tiene sticker: {message.sticker is not None}")

        if message.document:
            logger.info(f"   Document - MIME: {message.document.mime_type}, Filename: {message.document.file_name}")
        if message.photo:
            logger.info(f"   Photo - Cantidad de tamaños: {len(message.photo) if message.photo else 0}")
        if message.sticker:
            logger.info(f"   Sticker - Animado: {message.sticker.is_animated if message.sticker else 'N/A'}")

        if message.caption:
            logger.info(f"   Caption presente: '{message.caption[:50]}...'")
        else:
            logger.info(f"   Sin caption")
        chat_id = message.chat.id if message.chat else "unknown"
        message_id = message.message_id if hasattr(message, 'message_id') else "unknown"

        # Verificar si ya hay un procesamiento activo para este chat
        processing_key = f"processing_{chat_id}"
        if context.user_data.get(processing_key, False):
            logger.warning(f"🚫 Procesamiento ya activo para chat {chat_id} (mensaje {message_id}), ignorando posible duplicado")
            return

        # Marcar que hay un procesamiento activo
        context.user_data[processing_key] = True

        # Verificar autenticación si está configurada
        if Config.ALLOWED_USER_ID and str(user_id) != Config.ALLOWED_USER_ID:
            await message.reply_text(Config.ACCESS_DENIED_MESSAGE)
            logger.warning(f"Acceso denegado para usuario {user_id}")
            # Limpiar el flag de procesamiento
            context.user_data[processing_key] = False
            logger.info(f"🧹 Flag limpiado por autenticación denegada: chat {chat_id}")
            return

        # Validar que DEFAULT_PROMPT esté configurado para casos sin caption
        if not message.caption and (not DEFAULT_PROMPT or DEFAULT_PROMPT.strip() == ""):
            logger.warning("❌ Imagen enviada sin caption pero DEFAULT_PROMPT no está configurado")
            await message.reply_text(
                "❌ **Error de configuración**\n\n"
                "Para procesar imágenes sin descripción (caption), es necesario configurar un prompt por defecto.\n\n"
                "Por favor, contacta al administrador para configurar `DEFAULT_PROMPT` en las variables de entorno."
            )
            # Limpiar el flag de procesamiento
            context.user_data[processing_key] = False
            logger.info(f"🧹 Flag limpiado por falta de DEFAULT_PROMPT: chat {chat_id}")
            return

        # Determinar el modelo a usar basado en el contexto del usuario
        user_model = context.user_data.get('selected_model', Config.DEFAULT_MODEL)

        # Logging para debug
        media_type = "unknown"
        if message.photo:
            media_type = "photo"
        elif message.document:
            media_type = f"document ({message.document.mime_type})"
        elif message.sticker:
            media_type = f"sticker (animated: {message.sticker.is_animated})"

        logger.info(f"Imagen recibida - User: {user_id}, Tipo: {media_type}, Modelo: {user_model}, Forward: {bool(message.forward_origin)}, Caption: {bool(message.caption)}")
        logger.info(f"🔄 Iniciando procesamiento para chat {chat_id}, mensaje {message_id}, tipo: {media_type}")

        # Procesar el prompt con optimización automática
        if not message.caption:
            # Verificar si hay DEFAULT_PROMPT configurado
            if not DEFAULT_PROMPT or DEFAULT_PROMPT.strip() == "":
                logger.warning("❌ Imagen enviada sin caption y DEFAULT_PROMPT no configurado")
                await update.message.reply_text(Config.NO_CAPTION_MESSAGE, parse_mode='Markdown')
                # Limpiar el flag de procesamiento antes de retornar
                context.user_data[processing_key] = False
                logger.info(f"🧹 Flag limpiado por falta de DEFAULT_PROMPT: chat {chat_id}")
                return

            original_caption = ""  # Caption vacío para casos sin caption
            prompt = DEFAULT_PROMPT
            logger.info(f"🔄 Procesando imagen SIN caption - usando DEFAULT_PROMPT (longitud: {len(DEFAULT_PROMPT)} caracteres)")
            logger.info(f"   Prompt preview: {DEFAULT_PROMPT[:100]}...")
        else:
            original_caption = message.caption

            # Verificar si el usuario quiere optimización automática
            auto_optimize_enabled = context.user_data.get('auto_optimize', False)  # Por defecto desactivado
            prompt_optimized = False

            if auto_optimize_enabled and original_caption and len(original_caption.strip()) > 0:
                try:
                    # Obtener URL de la imagen para el optimizer
                    if image_type == "photo":
                        if not message.photo or len(message.photo) == 0:
                            raise ValueError("No se encontraron fotos en el mensaje")
                        photo = message.photo[-1]
                        photo_file = await context.bot.get_file(photo.file_id)
                    elif image_type == "document":
                        if not message.document:
                            raise ValueError("No se encontró documento en el mensaje")

                        logger.info(f"📄 Procesando documento de imagen: {message.document.file_name}")
                        logger.info(f"   MIME type: {message.document.mime_type}")
                        logger.info(f"   File size: {message.document.file_size} bytes")
                        logger.info(f"   File ID: {message.document.file_id[:20]}...")

                        try:
                            photo_file = await context.bot.get_file(message.document.file_id)
                            logger.info(f"   File path obtenido: {photo_file.file_path[:50]}...")
                        except Exception as file_error:
                            logger.error(f"❌ Error obteniendo file del documento: {file_error}")
                            raise ValueError(f"Error obteniendo archivo del documento: {str(file_error)}")
                    elif image_type == "sticker":
                        if not message.sticker:
                            raise ValueError("No se encontró sticker en el mensaje")
                        photo_file = await context.bot.get_file(message.sticker.file_id)
                    else:
                        prompt = original_caption
                        await processing_msg.edit_text("❌ Tipo de imagen no soportado.")
                        context.user_data[processing_key] = False
                        logger.info(f"🧹 Flag limpiado por tipo imagen no soportado: chat {chat_id}")
                        return

                    # Construir URL correcta para la imagen
                    if photo_file.file_path.startswith('http'):
                        photo_file_url = photo_file.file_path
                    else:
                        photo_file_url = f"https://api.telegram.org/file/bot{Config.TELEGRAM_BOT_TOKEN}/{photo_file.file_path}"

                    # Optimizar el prompt usando la nueva API v3
                    optimized_prompt = optimize_user_prompt_v3(
                        image_url=photo_file_url,
                        text=original_caption,
                        mode="video",
                        style="default"
                    )

                    if optimized_prompt and optimized_prompt != original_caption:
                        prompt = optimized_prompt
                        prompt_optimized = True
                        logger.info(f"Prompt optimizado con nueva API v3: '{original_caption}' → '{optimized_prompt[:100]}...'")
                    else:
                        prompt = original_caption
                        logger.info(f"Optimización no aplicable, usando caption original: '{original_caption}'")

                except Exception as optimizer_error:
                    prompt = original_caption
                    logger.error(f"Error en optimización con nueva API v3: {optimizer_error}")
                    logger.info(f"Continuando con caption original: '{original_caption}'")
            else:
                prompt = original_caption
                logger.info(f"Usando caption personalizado (sin optimización): '{prompt[:50]}...'")

        # Múltiples métodos de verificación de imagen
        is_image, image_type, error_msg = is_image_message(message)

        if not is_image:
            await message.reply_text(error_msg)
            context.user_data[processing_key] = False
            logger.info(f"🧹 Flag limpiado por validación imagen fallida: chat {chat_id}")
            return

        logger.info(f"✅ Imagen detectada correctamente - Tipo: {image_type}, User: {user_id}")
        logger.info(f"   Prompt a usar: '{prompt[:100]}...' (longitud: {len(prompt)})")

        # Información adicional para forwards
        if message.forward_origin:
            logger.info(f"Procesando imagen forwardeada con caption: '{message.caption[:50]}...'")

        # Obtener la imagen según el tipo detectado
        if image_type == "photo":
            # Foto directa - obtener la mejor calidad
            if not message.photo or len(message.photo) == 0:
                await message.reply_text("❌ Error: No se pudo acceder a la foto.")
                context.user_data[processing_key] = False
                logger.error(f"🧹 Flag limpiado - message.photo vacío o None")
                return

            logger.info(f"📷 Procesando foto con {len(message.photo)} tamaños disponibles")
            photo = message.photo[-1]  # La última es la de mejor calidad
            logger.info(f"📷 Usando tamaño de foto: {photo.width}x{photo.height}, file_id: {photo.file_id[:20]}...")

            try:
                photo_file = await context.bot.get_file(photo.file_id)
                logger.info(f"📁 File obtenido correctamente: {photo_file.file_path[:50]}...")
            except Exception as file_error:
                await message.reply_text("❌ Error al obtener el archivo de la foto.")
                context.user_data[processing_key] = False
                logger.error(f"Error obteniendo file: {file_error}")
                return
        elif image_type == "document":
            # Documento de imagen
            photo_file = await context.bot.get_file(message.document.file_id)
        elif image_type == "sticker":
            # Sticker estático
            photo_file = await context.bot.get_file(message.sticker.file_id)
        else:
            await message.reply_text("❌ Tipo de imagen no soportado.")
            context.user_data[processing_key] = False
            logger.info(f"🧹 Flag limpiado por tipo imagen no soportado (2): chat {chat_id}")
            return

        # Construir URL correcta para la imagen (para WaveSpeed API)
        if photo_file.file_path.startswith('http'):
            # file_path ya es una URL completa
            photo_file_url = photo_file.file_path
        else:
            # file_path es relativo, construir URL completa
            photo_file_url = f"https://api.telegram.org/file/bot{Config.TELEGRAM_BOT_TOKEN}/{photo_file.file_path}"

        # Descargar la foto para guardarla localmente
        try:
            logger.info(f"📥 Descargando imagen ({photo_file.file_size} bytes)...")
            photo_bytes = await photo_file.download_as_bytearray()
            logger.info(f"✅ Imagen descargada correctamente: {len(photo_bytes)} bytes")
        except Exception as download_error:
            await message.reply_text("❌ Error al descargar la imagen.")
            context.user_data[processing_key] = False
            logger.error(f"Error descargando imagen: {download_error}")
            return

        # Generar nombre único para la imagen y guardarla en el volumen
        try:
            image_filename = generate_serial_filename("input", "jpg")
            image_filepath = save_image_to_volume(photo_bytes, image_filename)
            logger.info(f"💾 Imagen guardada localmente: {image_filepath}")
        except Exception as save_error:
            await message.reply_text("❌ Error al guardar la imagen.")
            context.user_data[processing_key] = False
            logger.error(f"Error guardando imagen: {save_error}")
            return

        # Procesar la imagen (opcional, por si necesitamos redimensionar)
        image = Image.open(io.BytesIO(photo_bytes))

        logger.info(f"🚀 Iniciando envío a Wavespeed - Modelo: {user_model}, Prompt length: {len(prompt)}")

        # Enviar mensaje de procesamiento
        processing_msg = await update.message.reply_text(Config.PROCESSING_MESSAGE)

        logger.info(f"📤 Mensaje de procesamiento enviado correctamente")

        # Inicializar API de Wavespeed
        wavespeed = WavespeedAPI()

        # Usar procesamiento asíncrono inteligente
        use_async_processing = Config.USE_ASYNC_PROCESSING

        if use_async_processing:
            logger.info(f"🚀 Usando procesamiento asíncrono inteligente")

            # Generar ID único para esta solicitud
            async_request_id = f"async_{chat_id}_{int(time.time())}_{uuid.uuid4().hex[:8]}"

            # Enviar tarea para procesamiento asíncrono
            await async_video_processor.submit_video_generation(
                async_request_id, wavespeed, prompt, photo_file_url, user_model
            )

            # Esperar resultado con timeout inteligente
            result = await async_video_processor.wait_for_completion(async_request_id, timeout=Config.ASYNC_TASK_TIMEOUT)

            if not result or result.get('status') != 'success':
                error_msg = result.get('error', 'Error desconocido en procesamiento asíncrono') if result else 'Timeout en procesamiento asíncrono'
                await processing_msg.edit_text(f"❌ Error en generación asíncrona: {error_msg}")
                context.user_data[processing_key] = False
                return

            # Extraer el result de la respuesta asíncrona
            api_result = result['result']
        else:
            # Método tradicional de generación síncrona
            logger.info(f"🔄 Usando procesamiento síncrono tradicional")
            logger.info(f"Generando video con prompt: {prompt[:100]}...")

            # Llamar a la API con el modelo seleccionado
            api_result = wavespeed.generate_video(prompt, photo_file_url, model=user_model)

        if api_result.get('data') and api_result['data'].get('id'):
            request_id = api_result['data']['id']
            logger.info(f"Task submitted successfully. Request ID: {request_id}")

            # Esperar a que se complete con lógica mejorada y robusta
            attempt = 0
            video_sent = False
            consecutive_errors = 0
            max_consecutive_errors = 3

            while attempt < Config.MAX_POLLING_ATTEMPTS and not video_sent:
                try:
                    status_result = wavespeed.get_video_status(request_id)

                    if status_result.get('data'):
                        task_data = status_result['data']
                        status = task_data.get('status')

                        if status == 'completed':
                            logger.info(f"Task marked as completed. Checking for outputs...")

                            # Verificar múltiples veces si los outputs están disponibles
                            for output_check in range(5):  # Intentar hasta 5 veces obtener outputs
                                if task_data.get('outputs') and len(task_data['outputs']) > 0:
                                    video_url = task_data['outputs'][0]
                                    logger.info(f"Video URL obtained: {video_url}")

                                    # Verificar si ya descargamos este video URL para evitar duplicados
                                    downloaded_video_key = f"downloaded_{request_id}_{video_url}"
                                    if context.user_data.get(downloaded_video_key, False):
                                        logger.warning(f"⚠️ Video URL ya descargado anteriormente: {video_url}")
                                        logger.info(f"   Saltando descarga duplicada para request {request_id}")
                                        continue

                                    try:
                                        # Validar URL antes de descargar
                                        if not video_url or not video_url.startswith('http'):
                                            logger.error(f"❌ URL de video inválida: {video_url}")
                                            raise ValueError(f"URL de video inválida: {video_url}")

                                        logger.info(f"🎬 Iniciando descarga de video (intento {output_check + 1}/5)")

                                        # Descargar el video con validación (timeout adaptado al modelo)
                                        video_bytes = wavespeed.download_video(video_url, model=user_model)

                                        # Marcar que descargamos este video URL
                                        context.user_data[downloaded_video_key] = True

                                        if len(video_bytes) > 1000:  # Verificar que tenga contenido significativo
                                            logger.info(f"✅ Video descargado correctamente: {len(video_bytes)} bytes")

                                            # Generar nombre único para el video y guardarlo en el volumen
                                            video_filename = generate_serial_filename("output", "mp4")
                                            video_filepath = save_video_to_volume(video_bytes, video_filename)
                                            logger.info(f"💾 Video guardado en: {video_filepath}")

                                            # Verificar que el archivo se guardó correctamente
                                            if not os.path.exists(video_filepath) or os.path.getsize(video_filepath) == 0:
                                                logger.error(f"❌ Error: Archivo de video no se guardó correctamente: {video_filepath}")
                                                raise Exception(f"Archivo de video no se guardó correctamente: {video_filepath}")

                                            logger.info(f"✅ Archivo de video verificado: {os.path.getsize(video_filepath)} bytes")

                                            # Preparar el caption del video con el prompt utilizado
                                            video_caption = f"🎬 **Prompt utilizado:**\n{prompt}"
                                            if prompt_optimized:
                                                video_caption += "\n\n🎨 *Prompt optimizado automáticamente*"

                                            logger.info(f"📝 Caption del video preparado:")
                                            logger.info(f"   Longitud: {len(video_caption)} caracteres")
                                            logger.info(f"   Prompt optimizado: {prompt_optimized}")
                                            logger.info(f"   Original caption presente: {bool(original_caption)}")
                                            logger.info(f"   Preview: {video_caption[:200]}...")

                                            # Enviar el video desde el archivo guardado con reintentos
                                            send_attempts = 3  # Máximo 3 intentos para enviar a Telegram
                                            video_sent_successfully = False

                                            for send_attempt in range(send_attempts):
                                                try:
                                                    logger.info(f"📤 Enviando video a Telegram (intento {send_attempt + 1}/{send_attempts})")
                                                    logger.info(f"   Chat ID: {update.effective_chat.id}")
                                                    logger.info(f"   Video filepath: {video_filepath}")
                                                    logger.info(f"   Video file exists: {os.path.exists(video_filepath)}")
                                                    logger.info(f"   Video file size: {os.path.getsize(video_filepath) if os.path.exists(video_filepath) else 'N/A'}")
                                                    logger.info(f"   Caption length: {len(video_caption)} chars")

                                                    with open(video_filepath, 'rb') as video_file:
                                                        sent_message = await context.bot.send_video(
                                                            chat_id=update.effective_chat.id,
                                                            video=video_file,
                                                            caption=video_caption,
                                                            supports_streaming=True,
                                                        )

                                                    video_sent_successfully = True
                                                    logger.info(f"✅ Video enviado exitosamente a Telegram en intento {send_attempt + 1}")
                                                    logger.info(f"   Message ID enviado: {sent_message.message_id if sent_message else 'N/A'}")
                                                    break  # Salir del loop si se envió correctamente

                                                except Exception as send_error:
                                                    logger.error(f"❌ Error enviando video a Telegram (intento {send_attempt + 1}): {send_error}")
                                                    logger.error(f"   Tipo de error: {type(send_error).__name__}")

                                                    if send_attempt < send_attempts - 1:  # No es el último intento
                                                        wait_time = 2 * (send_attempt + 1)  # Espera progresiva: 2s, 4s
                                                        logger.info(f"⏳ Reintentando envío en {wait_time} segundos...")
                                                        await asyncio.sleep(wait_time)
                                                    else:
                                                        # Último intento falló, relanzar el error
                                                        logger.error("💥 Todos los intentos de envío fallaron")
                                                        raise send_error

                                            if not video_sent_successfully:
                                                raise Exception("No se pudo enviar el video a Telegram después de múltiples intentos")

                                            # Almacenar información del último video procesado para recuperación
                                            context.user_data['last_video'] = {
                                                'filepath': video_filepath,
                                                'caption': video_caption,
                                                'timestamp': datetime.now().isoformat(),
                                                'model': user_model,
                                                'request_id': request_id,
                                                'prompt_optimized': prompt_optimized,
                                                'original_caption': original_caption
                                            }
                                            logger.info(f"💾 Último video almacenado para usuario {user_id}")

                                            # Confirmar envío exitoso
                                            success_msg = "✅ ¡Video enviado exitosamente!"
                                            if prompt_optimized:
                                                success_msg += "\n\n🎨 Video con prompt optimizado"
                                            await processing_msg.edit_text(success_msg)
                                            logger.info(f"Video sent successfully to user {update.effective_chat.id}")
                                            video_sent = True
                                            context.user_data[processing_key] = False
                                            logger.info(f"🧹 Flag limpiado por envío exitoso de video: chat {chat_id}")
                                            return
                                        else:
                                            logger.warning(f"❌ Video descargado muy pequeño: {len(video_bytes)} bytes - descartando")
                                            raise Exception(f"Video descargado muy pequeño: {len(video_bytes)} bytes")

                                    except Exception as download_error:
                                        logger.error(f"❌ Error descargando video (intento {output_check + 1}/5): {download_error}")
                                        logger.error(f"   Tipo de error: {type(download_error).__name__}")
                                        logger.error(f"   URL: {video_url}")

                                        if output_check < 4:  # No es el último intento
                                            wait_time = 2 * (output_check + 1)  # Espera progresiva: 2s, 4s, 6s, 8s
                                            logger.info(f"⏳ Reintentando en {wait_time} segundos...")
                                            time.sleep(wait_time)
                                        else:  # Último intento fallido
                                            error_details = self._format_download_error(download_error, video_url)
                                            await processing_msg.edit_text(error_details)
                                            context.user_data[processing_key] = False
                                            logger.info(f"🧹 Flag limpiado por error en descarga: chat {chat_id}")
                                            return

                                else:
                                    logger.warning(f"No outputs available yet (attempt {output_check + 1}/5)")
                                    time.sleep(1)  # Esperar 1 segundo antes del siguiente check

                        elif status == 'failed':
                            error_msg = task_data.get('error', 'Error desconocido')
                            logger.error(f"Video generation failed: {error_msg}")
                            await processing_msg.edit_text(
                                f"❌ Lo siento, hubo un error al generar el video: {error_msg}"
                            )
                            context.user_data[processing_key] = False
                            logger.info(f"🧹 Flag limpiado por error en generación: chat {chat_id}")
                            return
                        elif status in ['processing', 'pending', 'running']:
                            logger.info(f"Task still processing. Status: {status} (attempt {attempt + 1}/{Config.MAX_POLLING_ATTEMPTS})")
                        else:
                            logger.warning(f"Unknown status: {status}")

                    else:
                        logger.warning(f"No data in status response: {status_result}")

                except Exception as polling_error:
                    logger.error(f"Error during polling (attempt {attempt + 1}): {polling_error}")
                    consecutive_errors += 1

                    # Si hay muchos errores consecutivos, aumentar el intervalo
                    if consecutive_errors >= max_consecutive_errors:
                        logger.warning(f"Múltiples errores consecutivos ({consecutive_errors}), aumentando intervalo de polling")
                        # Resetear contador después de logging
                        consecutive_errors = max_consecutive_errors - 1

                # Calcular intervalo de polling inteligente
                polling_interval = calculate_smart_polling_interval(attempt, Config.MAX_POLLING_ATTEMPTS, Config.POLLING_INTERVAL)
                logger.debug(f"⏱️  Esperando {polling_interval:.1f}s antes del siguiente check (intento {attempt + 1})")

                # Esperar antes del siguiente check
                time.sleep(polling_interval)
                attempt += 1

            # Si llegamos aquí, agotamos los intentos
            if not video_sent:
                logger.error(f"Polling timeout reached for request {request_id} after {Config.MAX_POLLING_ATTEMPTS} attempts")
                await processing_msg.edit_text(
                    f"⏰ El procesamiento agotó el tiempo límite.\n\n"
                    f"🔄 La solicitud se envió correctamente a WaveSpeed (ID: {request_id[:8]}...)\n"
                    f"📊 Estado final: Se realizaron {Config.MAX_POLLING_ATTEMPTS} verificaciones\n"
                    f"💡 El video puede estar disponible más tarde. Contacta al administrador si necesitas recuperar el video."
                )

        else:
            logger.error(f"❌ Error al iniciar la generación del video - respuesta inválida de API")
            await processing_msg.edit_text(
                "❌ Error al iniciar la generación del video.\n\n"
                "Verifica que la API de WaveSpeed esté funcionando correctamente."
            )

    except Exception as e:
        logger.error(f"❌ Error crítico procesando imagen: {e}")
        logger.error(f"   Tipo de error: {type(e).__name__}")
        logger.error(f"   Chat ID: {chat_id}, Message ID: {message_id}")
        logger.error(f"   Tipo de imagen: {media_type}")
        logger.error(f"   Modelo: {user_model}")
        logger.error(f"   Tiene caption: {bool(message.caption)}")
        logger.error(f"   DEFAULT_PROMPT configurado: {bool(DEFAULT_PROMPT and DEFAULT_PROMPT.strip())}")

        # Mostrar información adicional si es posible
        if hasattr(e, '__traceback__'):
            import traceback
            logger.error(f"   Traceback completo:\n{traceback.format_exc()}")

        try:
            await update.message.reply_text(
                "❌ Ocurrió un error inesperado. Por favor, inténtalo de nuevo.\n\n"
                f"**Detalles técnicos:**\n"
                f"• Error: `{type(e).__name__}`\n"
                f"• Mensaje: `{str(e)}`\n\n"
                f"💡 Contacta al administrador si el problema persiste."
            )
        except Exception as reply_error:
            logger.error(f"❌ Error adicional enviando mensaje de error: {reply_error}")
            # No podemos hacer mucho más aquí sin arriesgar un loop infinito
    finally:
        # Limpiar el flag de procesamiento
        context.user_data[processing_key] = False
        logger.info(f"✅ Procesamiento finalizado y flag limpiado para chat {chat_id}")

        # Limpiar descargas antiguas del contexto para evitar memory leaks
        cleanup_old_downloads(context, chat_id)

# Funciones wrapper para diferentes tipos de mensajes con imagen
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador específico para fotos"""
    await handle_image_message(update, context, "photo")

async def handle_document_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador específico para documentos de imagen"""
    await handle_image_message(update, context, "document")

async def handle_sticker_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador específico para stickers estáticos"""
    await handle_image_message(update, context, "sticker")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador del comando /help"""
    user_id = update.effective_user.id

    # Verificar autenticación si está configurada
    if Config.ALLOWED_USER_ID and str(user_id) != Config.ALLOWED_USER_ID:
        await update.message.reply_text(Config.ACCESS_DENIED_MESSAGE)
        logger.warning(f"Acceso denegado para usuario {user_id} en /help")
        return

    await update.message.reply_text(Config.HELP_MESSAGE, parse_mode='Markdown')

async def list_models_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra los modelos disponibles de Wavespeed AI"""
    user_id = update.effective_user.id

    # Verificar autenticación si está configurada
    if Config.ALLOWED_USER_ID and str(user_id) != Config.ALLOWED_USER_ID:
        await update.message.reply_text(Config.ACCESS_DENIED_MESSAGE)
        return

    wavespeed = WavespeedAPI()
    models = wavespeed.get_available_models()

    models_text = "🎬 **Modelos de Wavespeed AI Disponibles:**\n\n"

    for model_key, model_info in models.items():
        models_text += f"**{model_info['name']}** (`{model_key}`)\n"
        models_text += f"└ {model_info['description']}\n\n"

    models_text += "**📝 Cómo usar diferentes modelos:**\n"
    models_text += "`/textvideo [prompt]` - Video solo desde texto\n"
    models_text += "`/quality` - 720p alta calidad (con imagen)\n"
    models_text += "`/preview` - 480p ultra rápido (con imagen)\n\n"
    models_text += f"**Modelo por defecto:** `{Config.DEFAULT_MODEL}`"

    await update.message.reply_text(models_text, parse_mode='Markdown')

async def handle_text_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Genera video solo desde texto sin imagen"""
    user_id = update.effective_user.id

    # Verificar autenticación si está configurada
    if Config.ALLOWED_USER_ID and str(user_id) != Config.ALLOWED_USER_ID:
        await update.message.reply_text(Config.ACCESS_DENIED_MESSAGE)
        return

    # Obtener el prompt del mensaje
    if not context.args:
        await update.message.reply_text(
            "❌ Uso: `/textvideo [tu descripción del video]`\n\n"
            "💡 **Ejemplo:** `/textvideo Un amanecer espectacular sobre las montañas con nubes moviéndose`",
            parse_mode='Markdown'
        )
        return

    prompt = ' '.join(context.args)
    logger.info(f"Text-to-video solicitado por {user_id}: {prompt}")

    # Enviar mensaje de procesamiento
    processing_msg = await update.message.reply_text(
        "🎬 **Generando video desde texto...**\n\n"
        f"Prompt: _{prompt[:100]}{'...' if len(prompt) > 100 else ''}_\n\n"
        "Esto puede tomar unos minutos ⏳",
        parse_mode='Markdown'
    )

    try:
        wavespeed = WavespeedAPI()
        result = wavespeed.generate_text_to_video(prompt)

        if result.get('data') and result['data'].get('id'):
            request_id = result['data']['id']
            logger.info(f"Text-to-video task submitted. Request ID: {request_id}")

            # Esperar y procesar resultado igual que con imágenes
            await process_video_generation(update, context, processing_msg, wavespeed, request_id, prompt, model='text_to_video')

        else:
            await processing_msg.edit_text(
                "❌ Error al iniciar la generación del video desde texto."
            )

    except Exception as e:
        logger.error(f"Error en text-to-video: {e}")
        await processing_msg.edit_text(
            "❌ Ocurrió un error generando el video desde texto."
        )

async def handle_quality_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Activa el modo de video de alta calidad (720p)"""
    user_id = update.effective_user.id

    # Verificar autenticación si está configurada
    if Config.ALLOWED_USER_ID and str(user_id) != Config.ALLOWED_USER_ID:
        await update.message.reply_text(Config.ACCESS_DENIED_MESSAGE)
        return

    # Activar modo calidad para este usuario
    context.user_data['selected_model'] = 'quality'

    await update.message.reply_text(
        "🎯 **Modo Calidad Activado** ✨\n\n"
        "Ahora envía una imagen con un caption para generar un video en **720p alta calidad**.\n\n"
        "⚠️ **Nota:** Los videos de alta calidad pueden tomar más tiempo de procesamiento.\n\n"
        "✅ **Mejoras implementadas:**\n"
        "• Timeout extendido (3 minutos para descarga)\n"
        "• Reintentos automáticos en caso de error\n"
        "• Validación exhaustiva del archivo\n"
        "• Sistema de recuperación con `/lastvideo`\n\n"
        "💡 Para volver al modo normal, usa `/start` o `/preview`",
        parse_mode='Markdown'
    )

async def handle_preview_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Activa el modo de preview rápida (480p ultra fast)"""
    user_id = update.effective_user.id

    # Verificar autenticación si está configurada
    if Config.ALLOWED_USER_ID and str(user_id) != Config.ALLOWED_USER_ID:
        await update.message.reply_text(Config.ACCESS_DENIED_MESSAGE)
        return

    # Activar modo preview para este usuario
    context.user_data['selected_model'] = 'ultra_fast'

    await update.message.reply_text(
        "⚡ **Modo Preview Rápida Activado** 🚀\n\n"
        "Ahora envía una imagen con un caption para generar un video **480p ultra rápido**.\n\n"
        "💡 **Ideal para:** Probar ideas rápidamente antes de hacer versiones de mayor calidad.\n\n"
        "🎯 Para videos de alta calidad, usa `/quality`",
        parse_mode='Markdown'
    )

async def handle_optimize(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador para el comando /optimize - activar/desactivar optimización automática de prompts"""
    user_id = update.effective_user.id

    # Verificar autenticación si está configurada
    if Config.ALLOWED_USER_ID and str(user_id) != Config.ALLOWED_USER_ID:
        await update.message.reply_text(Config.ACCESS_DENIED_MESSAGE)
        return

    # Toggle optimización automática (por defecto desactivado)
    current_state = context.user_data.get('auto_optimize', False)
    context.user_data['auto_optimize'] = not current_state
    new_state = context.user_data['auto_optimize']

    if new_state:
        await update.message.reply_text(
            "🤖 **Optimización Automática ACTIVADA** ✨\n\n"
            "Ahora tus captions serán automáticamente mejorados usando IA cuando:\n"
            "• Contengan texto descriptivo\n"
            "• La optimización pueda mejorar la calidad del video\n\n"
            "🎨 **Mejora:** Tus videos tendrán mejor calidad automáticamente.\n\n"
            "💡 Usa `/optimize` nuevamente para desactivar.",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "🚫 **Optimización Automática DESACTIVADA**\n\n"
            "Ahora usarás tus captions exactamente como los escribas.\n\n"
            "💡 **Tip:** Usa `/optimize` nuevamente para activar la optimización automática.",
            parse_mode='Markdown'
        )

    logger.info(f"Usuario {user_id} cambió optimización automática a: {new_state}")

async def handle_debug_files(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador para el comando /debugfiles - diagnosticar tipos de archivos"""
    user_id = update.effective_user.id

    # Verificar autenticación si está configurada
    if Config.ALLOWED_USER_ID and str(user_id) != Config.ALLOWED_USER_ID:
        await update.message.reply_text(Config.ACCESS_DENIED_MESSAGE)
        return

    supported_info = """
🔍 **Diagnóstico de Archivos Soportados**

**Formatos de imagen aceptados:**
• **Como foto directa:** JPG, PNG, WebP, GIF
• **Como documento:** JPG, PNG, WebP, GIF, BMP, TIFF, HEIC, HEIF, SVG, ICO

**Cómo enviar imágenes:**
1. **Como foto:** Selecciona desde galería/cámara
2. **Como archivo:** Adjunta como documento

**Si tu imagen no funciona:**
• Verifica que sea un formato soportado
• Intenta reenviarla como foto en lugar de documento
• Usa /debugfiles para diagnóstico

📝 **Nota:** Los documentos con extensión de imagen (.jpg, .png, etc.) también son aceptados.
"""

    await update.message.reply_text(supported_info, parse_mode='Markdown')
    logger.info(f"Usuario {user_id} solicitó diagnóstico de archivos")

async def handle_lastvideo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador para el comando /lastvideo - recuperar el último video procesado"""
    user_id = update.effective_user.id

    # Verificar autenticación si está configurada
    if Config.ALLOWED_USER_ID and str(user_id) != Config.ALLOWED_USER_ID:
        await update.message.reply_text(Config.ACCESS_DENIED_MESSAGE)
        return

    # Verificar si hay un último video almacenado
    last_video = context.user_data.get('last_video')
    if not last_video:
        await update.message.reply_text(
            "📭 **No hay videos recientes**\n\n"
            "No tienes ningún video procesado recientemente para recuperar.\n\n"
            "💡 **Para recuperar un video:**\n"
            "1. Envía una imagen con caption\n"
            "2. Espera a que se procese\n"
            "3. Si no lo recibes, usa `/lastvideo`",
            parse_mode='Markdown'
        )
        logger.info(f"Usuario {user_id} intentó recuperar video pero no hay ninguno almacenado")
        return

    try:
        # Verificar que el archivo aún existe
        video_filepath = last_video.get('filepath')
        if not video_filepath or not os.path.exists(video_filepath):
            await update.message.reply_text(
                "❌ **Video no encontrado**\n\n"
                "El archivo del último video ya no está disponible.\n\n"
                "💡 **Solución:** Procesa una nueva imagen para generar un video fresco.",
                parse_mode='Markdown'
            )
            logger.warning(f"Usuario {user_id} intentó recuperar video pero archivo no existe: {video_filepath}")
            return

        # Preparar información del video
        timestamp = last_video.get('timestamp', 'desconocido')
        model = last_video.get('model', 'desconocido')
        prompt_optimized = last_video.get('prompt_optimized', False)
        original_caption = last_video.get('original_caption', 'sin caption')
        request_id = last_video.get('request_id', 'desconocido')

        # Preparar caption con información adicional
        recovery_caption = f"🔄 **Video Recuperado**\n\n"
        recovery_caption += f"📅 **Procesado:** {timestamp}\n"
        recovery_caption += f"🎬 **Modelo:** {model}\n"
        recovery_caption += f"🆔 **ID:** `{request_id[:8]}...`\n"

        if prompt_optimized:
            recovery_caption += f"🎨 **Optimizado:** Sí\n"
            recovery_caption += f"📝 **Original:** {original_caption}\n\n"
        else:
            recovery_caption += f"🎨 **Optimizado:** No\n\n"

        recovery_caption += f"💡 **Nota:** Este es el último video que procesaste."

        # Enviar el video recuperado
        with open(video_filepath, 'rb') as video_file:
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=video_file,
                caption=recovery_caption,
                supports_streaming=True,
                parse_mode='Markdown'
            )

        await update.message.reply_text(
            "✅ **Video recuperado exitosamente** ✨\n\n"
            "El último video procesado ha sido reenviado.",
            parse_mode='Markdown'
        )

        logger.info(f"Usuario {user_id} recuperó exitosamente el último video: {video_filepath}")

    except Exception as e:
        logger.error(f"Error recuperando último video para usuario {user_id}: {e}")
        await update.message.reply_text(
            "❌ **Error recuperando video**\n\n"
            f"Ocurrió un error al intentar recuperar el último video.\n\n"
            f"**Detalles:** {str(e)}\n\n"
            f"💡 Inténtalo de nuevo o procesa una nueva imagen.",
            parse_mode='Markdown'
        )

async def handle_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador para el comando /balance - consultar balance de Wavespeed"""
    user_id = update.effective_user.id

    # Verificar autenticación si está configurada
    if Config.ALLOWED_USER_ID and str(user_id) != Config.ALLOWED_USER_ID:
        await update.message.reply_text(Config.ACCESS_DENIED_MESSAGE)
        return

    try:
        # Enviar mensaje de procesamiento
        processing_msg = await update.message.reply_text(
            "💰 **Consultando balance...**\n\n"
            "🔄 Obteniendo información de tu cuenta Wavespeed.",
            parse_mode='Markdown'
        )

        # Consultar balance usando la API
        wavespeed = WavespeedAPI()
        balance_data = wavespeed.get_balance()

        # Procesar respuesta según nueva estructura
        if balance_data.get('success'):
            # Respuesta exitosa
            balance = balance_data.get('balance')
            currency = balance_data.get('currency', 'USD')

            balance_info = "💰 **Balance de Wavespeed**\n\n"

            if isinstance(balance, (int, float)):
                balance_info += f"**Saldo actual:** ${balance:.2f} {currency}\n"
            else:
                balance_info += f"**Saldo actual:** {balance}\n"

            # Agregar información adicional si está disponible
            raw_response = balance_data.get('raw_response', {})
            if 'data' in raw_response and isinstance(raw_response['data'], dict):
                data = raw_response['data']
                if 'credits' in data:
                    credits = data['credits']
                    balance_info += f"**Créditos disponibles:** {credits:,}\n"
                if 'usage' in data:
                    usage = data['usage']
                    balance_info += f"**Uso del mes:** {usage}\n"
                if 'plan' in data:
                    plan = data['plan']
                    balance_info += f"**Plan:** {plan}\n"

            balance_info += f"\n📊 **Estado:** Operativo ✅\n"
            balance_info += f"🔄 **Última consulta:** {datetime.now().strftime('%H:%M:%S')}"

            await processing_msg.edit_text(balance_info, parse_mode='Markdown')
            logger.info(f"Balance consultado exitosamente para usuario {user_id}: ${balance} {currency}")

        else:
            # Error en la consulta
            error_type = balance_data.get('error', 'Unknown error')
            error_msg = balance_data.get('message', 'Error desconocido')

            await processing_msg.edit_text(
                f"❌ **Error consultando balance**\n\n"
                f"**Tipo de error:** {error_type}\n"
                f"**Detalles:** {error_msg}\n\n"
                f"💡 Si el problema persiste, contacta al administrador.",
                parse_mode='Markdown'
            )
            logger.warning(f"Error consultando balance para usuario {user_id}: {error_type} - {error_msg}")

    except Exception as e:
        logger.error(f"Error crítico en comando /balance para usuario {user_id}: {e}")
        try:
            await processing_msg.edit_text(
                "❌ **Error interno**\n\n"
                f"Ocurrió un error procesando tu solicitud.\n\n"
                f"**Detalles técnicos:** {str(e)}\n\n"
                f"💡 Inténtalo de nuevo en unos minutos.",
                parse_mode='Markdown'
            )
        except:
            # Fallback si no se puede editar el mensaje
            await update.message.reply_text(
                "❌ **Error consultando balance**\n\n"
                "Hubo un problema técnico. Inténtalo de nuevo.",
                parse_mode='Markdown'
            )

async def handle_download(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador para el comando /download - descargar videos de redes sociales"""
    user_id = update.effective_user.id

    # Verificar autenticación si está configurada
    if Config.ALLOWED_USER_ID and str(user_id) != Config.ALLOWED_USER_ID:
        await update.message.reply_text(Config.ACCESS_DENIED_MESSAGE)
        return

    # Verificar que se proporcionó una URL
    if not context.args:
        await update.message.reply_text(
            "❌ **Uso incorrecto**\n\n"
            "💡 **Uso correcto:** `/download [URL]`\n\n"
            "**Ejemplos:**\n"
            "`/download https://www.instagram.com/p/ABC123/`\n"
            "`/download https://twitter.com/user/status/123`\n"
            "`/download https://www.facebook.com/watch?v=456`\n"
            "`/download https://reddit.com/r/videos/comments/789/video/`",
            parse_mode='Markdown'
        )
        return

    url = ' '.join(context.args).strip()

    # Validar que sea una URL
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text(
            "❌ **URL inválida**\n\n"
            "La URL debe comenzar con `http://` o `https://`",
            parse_mode='Markdown'
        )
        return

    # Verificar que sea una plataforma soportada
    if not video_downloader.is_valid_social_url(url):
        await update.message.reply_text(
            "❌ **Plataforma no soportada**\n\n"
            "**Plataformas soportadas:**\n"
            "• 📘 Facebook\n"
            "• 📷 Instagram\n"
            "• 🐦 X (Twitter)\n"
            "• 🔴 Reddit\n"
            "• 🎵 TikTok\n\n"
            "💡 Envía `/download [URL]` con un enlace válido",
            parse_mode='Markdown'
        )
        return

    # Enviar mensaje de procesamiento
    # Usar formato simple sin Markdown para evitar problemas con URLs
    processing_msg = await update.message.reply_text(
        "🎬 Descargando video...\n\n"
        f"🔗 URL: {url[:50]}{'...' if len(url) > 50 else ''}\n\n"
        "🔧 Método: curl_cffi (avanzado) + yt-dlp fallback\n"
        "⏳ Esto puede tomar unos minutos..."
    )

    try:
        # Descargar el video
        logger.info(f"Usuario {user_id} solicitó descarga de: {url}")
        result = video_downloader.download_video(url)

        if not result['success']:
            error_msg = result['error']

            # Mensaje más específico para TikTok con información sobre fallback
            if platform == 'TikTok' and 'impersonat' in error_msg.lower():
                error_msg = "Error de acceso a TikTok. Se intentó con métodos avanzados pero falló."

            await processing_msg.edit_text(
                f"❌ **Error descargando video**\n\n"
                f"**Detalles:** {error_msg}\n\n"
                f"💡 Verifica que la URL sea correcta y el video esté disponible.\n"
                f"🔧 Para TikTok, se usan técnicas avanzadas de acceso.",
                parse_mode='Markdown'
            )
            return

        # Información del video descargado
        video_filepath = result['filepath']
        title = result.get('title', 'Video sin título')
        duration = result.get('duration', 0)
        platform = result.get('platform', 'Desconocido')
        file_size = result.get('file_size', 0)

        logger.info(f"Video descargado exitosamente: {video_filepath}")

        # Preparar información para enviar
        # Usar formato simple sin Markdown para evitar problemas con URLs
        caption = f"🎬 {platform} Video\n\n"
        caption += f"📹 Título: {title[:100]}{'...' if len(title) > 100 else ''}\n"
        if duration > 0:
            caption += f"⏱️ Duración: {duration}s\n"
        caption += f"📏 Tamaño: {file_size:,} bytes\n"
        caption += f"🔧 Método usado: {method_used}\n\n"
        caption += f"🔗 Fuente: {url[:30]}{'...' if len(url) > 30 else ''}"

        # Enviar el video
        try:
            with open(video_filepath, 'rb') as video_file:
                await context.bot.send_video(
                    chat_id=update.effective_chat.id,
                    video=video_file,
                    caption=caption,
                    supports_streaming=True,
                )

            # Confirmar envío exitoso
            method_used = result.get('method', 'desconocido')
            await processing_msg.edit_text(
                "✅ Video enviado exitosamente ✨\n\n"
                f"🎬 {platform} Video\n"
                f"📹 {title[:50]}{'...' if len(title) > 50 else ''}\n"
                f"🔧 Método usado: {method_used}\n\n"
                "🗑️ Archivo temporal eliminado."
            )

            logger.info(f"Video enviado exitosamente a usuario {user_id} usando método {method_used}")

        except Exception as send_error:
            logger.error(f"Error enviando video a Telegram: {send_error}")
            await processing_msg.edit_text(
                "❌ **Error enviando video**\n\n"
                f"El video se descargó pero no pudo enviarse a Telegram.\n\n"
                f"**Error:** {str(send_error)[:100]}...",
                parse_mode='Markdown'
            )

        finally:
            # Limpiar archivo temporal SIEMPRE
            cleanup_success = video_downloader.cleanup_file(video_filepath)
            if cleanup_success:
                logger.info(f"Archivo temporal limpiado: {video_filepath}")
            else:
                logger.warning(f"No se pudo limpiar archivo temporal: {video_filepath}")

    except Exception as e:
        logger.error(f"Error crítico en comando /download para usuario {user_id}: {e}")
        try:
            await processing_msg.edit_text(
                "❌ **Error interno**\n\n"
                f"Ocurrió un error procesando tu solicitud.\n\n"
                f"**Detalles técnicos:** {str(e)}\n\n"
                f"💡 Inténtalo de nuevo en unos minutos.",
                parse_mode='Markdown'
            )
        except:
            # Fallback si no se puede editar el mensaje
            await update.message.reply_text(
                "❌ **Error procesando descarga**\n\n"
                "Hubo un problema técnico. Inténtalo de nuevo.",
                parse_mode='Markdown'
            )

async def handle_social_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador automático para URLs de redes sociales enviadas como mensajes de texto"""
    user_id = update.effective_user.id

    # Verificar autenticación si está configurada
    if Config.ALLOWED_USER_ID and str(user_id) != Config.ALLOWED_USER_ID:
        return  # Silenciosamente ignorar usuarios no autorizados

    message = update.message
    if not message or not message.text:
        return

    text = message.text.strip()

    # Buscar URLs en el mensaje usando regex
    url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?'
    urls = re.findall(url_pattern, text)

    if not urls:
        return  # No hay URLs en el mensaje

    # Procesar la primera URL encontrada
    url = urls[0]

    # Verificar si es una URL de red social soportada
    if not video_downloader.is_valid_social_url(url):
        return  # No es una URL soportada, ignorar silenciosamente

    logger.info(f"🎯 URL de red social detectada automáticamente: {url} de usuario {user_id}")

    # Enviar mensaje de procesamiento automático
    # Usar formato simple sin Markdown para evitar problemas con URLs
    processing_msg = await update.message.reply_text(
        "🎬 Descargando video automáticamente...\n\n"
        f"🔗 URL detectada: {url[:50]}{'...' if len(url) > 50 else ''}\n\n"
        "🔧 Método: curl_cffi (avanzado) + yt-dlp fallback\n"
        "⏳ Procesando..."
    )

    try:
        # Descargar el video
        result = video_downloader.download_video(url)

        if not result['success']:
            await processing_msg.edit_text(
                f"❌ **Error descargando video**\n\n"
                f"**Detalles:** {result['error']}\n\n"
                f"💡 También puedes usar `/download [URL]` para intentar manualmente.",
                parse_mode='Markdown'
            )
            return

        # Información del video descargado
        video_filepath = result['filepath']
        title = result.get('title', 'Video sin título')
        duration = result.get('duration', 0)
        platform = result.get('platform', 'Desconocido')
        file_size = result.get('file_size', 0)

        logger.info(f"Video descargado exitosamente: {video_filepath}")

        # Preparar información para enviar
        # Usar formato simple sin Markdown para evitar problemas con URLs
        caption = f"🎬 {platform} Video (Auto-descargado)\n\n"
        caption += f"📹 Título: {title[:100]}{'...' if len(title) > 100 else ''}\n"
        if duration > 0:
            caption += f"⏱️ Duración: {duration}s\n"
        caption += f"📏 Tamaño: {file_size:,} bytes\n"
        caption += f"🔧 Método usado: {method_used}\n\n"
        caption += f"🔗 Fuente: {url[:30]}{'...' if len(url) > 30 else ''}"

        # Enviar el video
        try:
            with open(video_filepath, 'rb') as video_file:
                await context.bot.send_video(
                    chat_id=update.effective_chat.id,
                    video=video_file,
                    caption=caption,
                    supports_streaming=True,
                )

            # Confirmar envío exitoso
            method_used = result.get('method', 'desconocido')
            await processing_msg.edit_text(
                "✅ Video descargado y enviado automáticamente ✨\n\n"
                f"🎬 {platform} Video (Auto-descargado)\n"
                f"📹 {title[:50]}{'...' if len(title) > 50 else ''}\n"
                f"🔧 Método usado: {method_used}\n\n"
                "🤖 Detección automática activada."
            )

            logger.info(f"Video enviado exitosamente por detección automática a usuario {user_id}")

        except Exception as send_error:
            logger.error(f"Error enviando video por detección automática: {send_error}")
            await processing_msg.edit_text(
                "❌ **Error enviando video**\n\n"
                f"El video se descargó pero no pudo enviarse.\n\n"
                f"**Error:** {str(send_error)[:100]}...",
                parse_mode='Markdown'
            )

        finally:
            # Limpiar archivo temporal SIEMPRE
            cleanup_success = video_downloader.cleanup_file(video_filepath)
            if cleanup_success:
                logger.info(f"Archivo temporal limpiado: {video_filepath}")
            else:
                logger.warning(f"No se pudo limpiar archivo temporal: {video_filepath}")

    except Exception as e:
        logger.error(f"Error crítico en detección automática para usuario {user_id}: {e}")
        try:
            await processing_msg.edit_text(
                "❌ **Error en descarga automática**\n\n"
                f"Ocurrió un error procesando la URL.\n\n"
                f"💡 Usa `/download [URL]` para intentar manualmente.",
                parse_mode='Markdown'
            )
        except:
            # Fallback si no se puede editar el mensaje
            await update.message.reply_text(
                "❌ **Error procesando URL automática**\n\n"
                "Hubo un problema técnico.",
                parse_mode='Markdown'
            )

async def process_video_generation(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                 processing_msg, wavespeed: WavespeedAPI, request_id: str, prompt: str, model: str = 'ultra_fast'):
    """
    Función común para procesar la generación de video (reutilizable para diferentes modos)
    """
    attempt = 0
    video_sent = False

    while attempt < Config.MAX_POLLING_ATTEMPTS and not video_sent:
        try:
            status_result = wavespeed.get_video_status(request_id)

            if status_result.get('data'):
                task_data = status_result['data']
                status = task_data.get('status')

                if status == 'completed':
                    logger.info(f"Task marked as completed. Checking for outputs...")

                    # Verificar múltiples veces si los outputs están disponibles
                    for output_check in range(5):  # Intentar hasta 5 veces obtener outputs
                        if task_data.get('outputs') and len(task_data['outputs']) > 0:
                            video_url = task_data['outputs'][0]
                            logger.info(f"Video URL obtained: {video_url}")

                            # Sistema de reintentos para descarga de video
                            for download_attempt in range(5):  # Intentar hasta 5 veces
                                try:
                                    # Validar URL antes de descargar
                                    if not video_url or not video_url.startswith('http'):
                                        logger.error(f"❌ URL de video inválida: {video_url}")
                                        raise ValueError(f"URL de video inválida: {video_url}")

                                    logger.info(f"🎬 Iniciando descarga de video (intento {download_attempt + 1}/5)")

                                    # Descargar el video con validación (timeout adaptado al modelo)
                                    video_bytes = wavespeed.download_video(video_url, model=model)

                                    if len(video_bytes) > 1000:  # Verificar que tenga contenido significativo
                                        # Generar nombre único para el video y guardarlo en el volumen
                                        video_filename = generate_serial_filename("output", "mp4")
                                        video_filepath = save_video_to_volume(video_bytes, video_filename)
                                        logger.info(f"Video saved to: {video_filepath}")

                                        # Preparar el caption del video con el prompt utilizado
                                        video_caption = f"🎬 **Prompt utilizado:**\n{prompt}"

                                        # Enviar el video desde el archivo guardado con reintentos
                                        send_attempts = 3  # Máximo 3 intentos para enviar a Telegram
                                        video_sent_successfully = False

                                        for send_attempt in range(send_attempts):
                                            try:
                                                logger.info(f"📤 Enviando video a Telegram (intento {send_attempt + 1}/{send_attempts})")

                                                with open(video_filepath, 'rb') as video_file:
                                                    sent_message = await context.bot.send_video(
                                                        chat_id=update.effective_chat.id,
                                                        video=video_file,
                                                        caption=video_caption,
                                                        supports_streaming=True,
                                                    )

                                                video_sent_successfully = True
                                                logger.info(f"✅ Video enviado exitosamente a Telegram en intento {send_attempt + 1}")
                                                break  # Salir del loop si se envió correctamente

                                            except Exception as send_error:
                                                logger.error(f"❌ Error enviando video a Telegram (intento {send_attempt + 1}): {send_error}")

                                                if send_attempt < send_attempts - 1:  # No es el último intento
                                                    wait_time = 2 * (send_attempt + 1)  # Espera progresiva: 2s, 4s
                                                    logger.info(f"⏳ Reintentando envío en {wait_time} segundos...")
                                                    await asyncio.sleep(wait_time)
                                                else:
                                                    # Último intento falló, relanzar el error
                                                    logger.error("💥 Todos los intentos de envío fallaron")
                                                    raise send_error

                                        if not video_sent_successfully:
                                            raise Exception("No se pudo enviar el video a Telegram después de múltiples intentos")

                                        # Confirmar envío exitoso
                                        success_msg = "✅ ¡Video enviado exitosamente!"
                                        if prompt_optimized:
                                            success_msg += "\n\n🎨 Video con prompt optimizado"
                                        await processing_msg.edit_text(success_msg)
                                        logger.info(f"Video sent successfully to user {update.effective_chat.id}")
                                        video_sent = True
                                        return

                                    else:
                                        logger.warning(f"Downloaded video too small: {len(video_bytes)} bytes")
                                        break  # Salir del loop de reintentos

                                except Exception as download_error:
                                    logger.error(f"❌ Error descargando video (intento {download_attempt + 1}/5): {download_error}")
                                    logger.error(f"   Tipo de error: {type(download_error).__name__}")
                                    logger.error(f"   URL: {video_url}")

                                    if download_attempt < 4:  # No es el último intento
                                        wait_time = 2 * (download_attempt + 1)  # Espera progresiva: 2s, 4s, 6s, 8s
                                        logger.info(f"⏳ Reintentando descarga en {wait_time} segundos...")
                                        time.sleep(wait_time)
                                    else:  # Último intento fallido
                                        error_details = wavespeed._format_download_error(download_error, video_url)
                                        await processing_msg.edit_text(error_details)
                                        return

                        else:
                            logger.info(f"Outputs not ready yet (attempt {output_check + 1}/5)")
                            time.sleep(1)  # Esperar 1 segundo entre checks de outputs

                elif status == 'failed':
                    error_msg = task_data.get('error', 'Unknown error')
                    logger.error(f"Task failed: {error_msg}")
                    await processing_msg.edit_text(
                        f"❌ La generación del video falló.\n\nError: {error_msg}"
                    )
                    return

                else:
                    logger.info(f"Task still processing. Status: {status}")

            else:
                logger.warning(f"No data in status response: {status_result}")

        except Exception as polling_error:
            logger.error(f"Error during polling (attempt {attempt + 1}): {polling_error}")

        # Esperar antes del siguiente check
        time.sleep(Config.POLLING_INTERVAL)
        attempt += 1

    # Si llegamos aquí, agotamos los intentos
    if not video_sent:
        logger.error(f"Polling timeout reached for request {request_id} after {Config.MAX_POLLING_ATTEMPTS} attempts")
        await processing_msg.edit_text(
            f"⏰ El procesamiento agotó el tiempo límite.\n\n"
            f"🔄 La solicitud se envió correctamente (ID: {request_id[:8]}...)\n"
            f"📊 Estado final: Se realizaron {Config.MAX_POLLING_ATTEMPTS} verificaciones\n"
            f"💡 El video puede estar disponible más tarde."
        )

def create_app():
    """Importar aplicación FastAPI (reemplaza Flask)"""
    from fastapi_app import create_app as create_fastapi_app
    return create_fastapi_app()

def main() -> None:
    """Función principal"""
    logger.info("Iniciando TELEWAN Bot...")

    try:
        Config.validate()
        logger.info("Configuración validada correctamente")
    except ValueError as e:
        logger.error(f"Error de configuración: {e}")
        return

    # Verificar modo de operación
    use_webhook = Config.USE_WEBHOOK
    logger.info(f"USE_WEBHOOK config: {Config.USE_WEBHOOK}")
    logger.info(f"USE_WEBHOOK evaluated: {use_webhook}")
    logger.info(f"Modo de operación: {'WEBHOOK' if use_webhook else 'POLLING'}")

    # Crear aplicación
    if use_webhook:
        logger.info("🎯 Configurando bot para usar WEBHOOKS con FastAPI (ASGI)")
        logger.info(f"WEBHOOK_URL: {Config.WEBHOOK_URL}")
        logger.info(f"WEBHOOK_PORT: {Config.WEBHOOK_PORT}")
        logger.info(f"WEBHOOK_PATH: {Config.WEBHOOK_PATH}")
        logger.info(f"PORT env: {os.getenv('PORT', 'not set')}")

        # Configurar webhook URL en Telegram
        if Config.WEBHOOK_URL:
            # Asegurar que la URL tenga https://
            webhook_base_url = Config.WEBHOOK_URL
            if not webhook_base_url.startswith('http'):
                webhook_base_url = f"https://{webhook_base_url}"

            webhook_url = f"{webhook_base_url}{Config.WEBHOOK_PATH}"
            logger.info(f"Webhook URL completa: {webhook_url}")

            # Intentar configurar webhook en Telegram
            try:
                telegram_api_url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/setWebhook"
                payload = {"url": webhook_url}
                secret_token = os.getenv('WEBHOOK_SECRET_TOKEN')
                if secret_token:
                    payload["secret_token"] = secret_token

                # Usar requests para configurar webhook (no necesitamos async aquí)
                import requests
                response = requests.post(telegram_api_url, json=payload, timeout=10)
                result = response.json()
                if result.get("ok"):
                    logger.info("✅ Webhook configurado exitosamente en Telegram")
                    logger.info(f"📝 Descripción: {result.get('description', 'OK')}")
                else:
                    logger.error(f"❌ Error configurando webhook: {result}")
                    logger.error(f"📝 Error details: {result.get('description', 'Unknown error')}")
            except Exception as e:
                logger.error(f"Error configurando webhook: {e}")

        # Iniciar servidor FastAPI con Uvicorn
        logger.info(f"🚀 Iniciando servidor FastAPI con Uvicorn en puerto {Config.WEBHOOK_PORT}")
        logger.info("Servidor ASGI listo para recibir peticiones")

        try:
            from fastapi_app import run_server
            run_server()
        except Exception as server_error:
            logger.error(f"Error iniciando servidor FastAPI: {server_error}")
            raise

    else:
        logger.info("Configurando bot para usar POLLING")
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()

        # Agregar manejadores
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("models", list_models_command))
        application.add_handler(CommandHandler("textvideo", handle_text_video))
        application.add_handler(CommandHandler("quality", handle_quality_video))
        application.add_handler(CommandHandler("preview", handle_preview_video))
        application.add_handler(CommandHandler("optimize", handle_optimize))
        # Múltiples handlers para diferentes tipos de imágenes
        application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        application.add_handler(MessageHandler(image_document_filter, handle_document_image))
        application.add_handler(MessageHandler(static_sticker_filter, handle_sticker_image))

        # Iniciar el bot con polling
        logger.info("Bot iniciado con polling. Presiona Ctrl+C para detener.")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

# Función de prueba para los filtros (útil para debugging)
def test_image_filters():
    """Función de prueba para verificar los filtros de imagen"""
    from telegram import Message, Document, Sticker, PhotoSize

    # Simular mensajes de prueba
    print("🧪 Probando filtros de imagen...")

    # Foto
    photo_msg = Message(message_id=1, date=None, chat=None)
    photo_msg.photo = [PhotoSize(file_id="test", file_unique_id="test", width=100, height=100)]
    print(f"Foto: {image_document_filter(photo_msg)} (debería ser False), {static_sticker_filter(photo_msg)} (debería ser False)")

    # Documento de imagen
    doc_msg = Message(message_id=1, date=None, chat=None)
    doc_msg.document = Document(file_id="test", file_unique_id="test", mime_type="image/jpeg")
    print(f"Documento JPG: {image_document_filter(doc_msg)} (debería ser True), {static_sticker_filter(doc_msg)} (debería ser False)")

    # Documento no imagen
    doc_msg2 = Message(message_id=1, date=None, chat=None)
    doc_msg2.document = Document(file_id="test", file_unique_id="test", mime_type="application/pdf")
    print(f"Documento PDF: {image_document_filter(doc_msg2)} (debería ser False), {static_sticker_filter(doc_msg2)} (debería ser False)")

    # Sticker estático
    sticker_msg = Message(message_id=1, date=None, chat=None)
    sticker_msg.sticker = Sticker(file_id="test", file_unique_id="test", width=100, height=100, is_animated=False)
    print(f"Sticker estático: {image_document_filter(sticker_msg)} (debería ser False), {static_sticker_filter(sticker_msg)} (debería ser True)")

    # Sticker animado
    sticker_msg2 = Message(message_id=1, date=None, chat=None)
    sticker_msg2.sticker = Sticker(file_id="test", file_unique_id="test", width=100, height=100, is_animated=True)
    print(f"Sticker animado: {image_document_filter(sticker_msg2)} (debería ser False), {static_sticker_filter(sticker_msg2)} (debería ser False)")

    print("✅ Pruebas completadas")

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'test_filters':
        test_image_filters()
    else:
        main()
