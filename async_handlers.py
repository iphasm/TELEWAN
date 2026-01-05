"""
Async Handlers for Event-Driven Architecture
Funciones que manejan la lógica de negocio de manera asíncrona
"""
import asyncio
import uuid
from typing import Dict, Any, Optional
from telegram import Update
from telegram.ext import ContextTypes
import logging

from async_wavespeed import AsyncWavespeedAPI
from config import Config

logger = logging.getLogger(__name__)

def generate_serial_filename(prefix: str, extension: str) -> str:
    """
    Genera un nombre de archivo único con timestamp y UUID
    """
    timestamp = uuid.uuid4().hex[:8]
    return f"{prefix}_{timestamp}.{extension}"

async def save_image_to_volume(image_data: bytes, filename: str) -> str:
    """
    Guarda imagen en el volumen de manera asíncrona
    """
    import aiofiles
    import os

    volume_path = Config.VOLUME_PATH
    os.makedirs(volume_path, exist_ok=True)

    filepath = os.path.join(volume_path, filename)

    async with aiofiles.open(filepath, 'wb') as f:
        await f.write(image_data)

    logger.info(f"💾 Imagen guardada asíncronamente: {filepath}")
    return filepath

async def save_video_to_volume(video_data: bytes, filename: str) -> str:
    """
    Guarda video en el volumen de manera asíncrona
    """
    import aiofiles
    import os

    volume_path = Config.VOLUME_PATH
    os.makedirs(volume_path, exist_ok=True)

    filepath = os.path.join(volume_path, filename)

    async with aiofiles.open(filepath, 'wb') as f:
        await f.write(video_data)

    logger.info(f"💾 Video guardado asíncronamente: {filepath}")
    return filepath

async def optimize_user_prompt_async(image_url: str, text: str, mode: str = "video", style: str = "default") -> str:
    """
    Optimiza un prompt usando la nueva API v3 de WaveSpeedAI (async)
    """
    try:
        wavespeed = AsyncWavespeedAPI()

        # Iniciar optimización con la nueva API
        result = await wavespeed.optimize_prompt_v3(
            image_url=image_url,
            text=text,
            mode=mode,
            style=style
        )

        if result.get('data') and result['data'].get('id'):
            request_id = result['data']['id']
            logger.info(f"🤖 Prompt optimization started. Request ID: {request_id}")

            # Esperar resultado (máximo 30 segundos)
            max_attempts = 300  # 30 segundos con polling de 0.1s
            attempt = 0

            while attempt < max_attempts:
                try:
                    status_result = await wavespeed.get_prompt_optimizer_result(request_id)

                    if status_result.get('data'):
                        task_data = status_result['data']
                        status = task_data.get('status')

                        if status == 'completed':
                            if task_data.get('outputs') and len(task_data['outputs']) > 0:
                                optimized_text = task_data['outputs'][0]
                                logger.info(f"🤖 Optimized result: {optimized_text[:100]}...")
                                logger.info(f"Original text: '{text}'")
                                logger.info(f"Optimization completed in {attempt * 0.1:.1f} seconds")
                                return optimized_text
                            else:
                                logger.warning("🤖 Prompt optimization completed but no outputs")
                                break

                        elif status == 'failed':
                            error_msg = task_data.get('error', 'Unknown error')
                            logger.error(f"🤖 Prompt optimization failed: {error_msg}")
                            break

                    attempt += 1
                    await asyncio.sleep(0.1)

                except Exception as poll_error:
                    logger.error(f"Error polling optimizer status: {poll_error}")
                    attempt += 1
                    await asyncio.sleep(0.1)

            logger.warning("🤖 Prompt optimization timed out or failed, using original text")
            return text

        else:
            logger.error(f"Failed to start prompt optimization. API Response: {result}")
            return text

    except Exception as e:
        logger.error(f"Critical error in prompt optimization: {e}")
        return text

async def process_video_generation_async(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    processing_msg,
    request_id: str,
    prompt: str,
    prompt_optimized: bool = False
) -> None:
    """
    Función común para procesar la generación de video (async version)
    """
    attempt = 0
    video_sent = False
    wavespeed = AsyncWavespeedAPI()

    while attempt < Config.MAX_POLLING_ATTEMPTS and not video_sent:
        try:
            status_result = await wavespeed.get_video_status(request_id)

            if status_result.get('data'):
                task_data = status_result['data']
                status = task_data.get('status')

                if status == 'completed':
                    logger.info(f"🎬 Task marked as completed. Checking for outputs...")

                    # Verificar múltiples veces si los outputs están disponibles
                    for output_check in range(5):  # Intentar hasta 5 veces obtener outputs
                        if task_data.get('outputs') and len(task_data['outputs']) > 0:
                            video_url = task_data['outputs'][0]
                            logger.info(f"🎬 Video URL obtained: {video_url}")

                            try:
                                # Descargar el video con validación
                                video_bytes = await wavespeed.download_video(video_url)

                                if len(video_bytes) > 1000:  # Verificar que tenga contenido significativo
                                    # Generar nombre único para el video y guardarlo en el volumen
                                    video_filename = generate_serial_filename("output", "mp4")
                                    video_filepath = await save_video_to_volume(video_bytes, video_filename)
                                    logger.info(f"Video saved to: {video_filepath}")

                                    # Preparar el caption del video con el prompt utilizado
                                    video_caption = f"🎬 **Prompt utilizado:**\n{prompt}"
                                    if prompt_optimized:
                                        video_caption += "\n\n🎨 *Prompt optimizado automáticamente*"

                                    # Enviar el video desde el archivo guardado
                                    with open(video_filepath, 'rb') as video_file:
                                        sent_message = await context.bot.send_video(
                                            chat_id=update.effective_chat.id,
                                            video=video_file,
                                            caption=video_caption,
                                            supports_streaming=True,
                                            parse_mode='Markdown'
                                        )

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

                            except Exception as download_error:
                                logger.error(f"❌ Error downloading/sending video (attempt {output_check + 1}): {download_error}")
                                if output_check < 4:  # No es el último intento
                                    wait_time = 2 * (output_check + 1)  # Espera progresiva: 2s, 4s, 6s, 8s
                                    logger.info(f"⏳ Reintentando en {wait_time} segundos...")
                                    await asyncio.sleep(wait_time)  # ASYNC SLEEP
                                else:  # Último intento fallido
                                    error_details = wavespeed._format_download_error(download_error, video_url)
                                    await processing_msg.edit_text(error_details)
                                    return

                        else:
                            logger.warning(f"No outputs available yet (attempt {output_check + 1}/5)")
                            await asyncio.sleep(1)  # ASYNC SLEEP

                elif status == 'failed':
                    error_msg = task_data.get('error', 'Unknown error')
                    logger.error(f"🎬 Task failed: {error_msg}")
                    await processing_msg.edit_text(
                        f"❌ La generación del video falló.\n\nError: {error_msg}"
                    )
                    return

                else:
                    logger.info(f"🎬 Task still processing. Status: {status}")

            else:
                logger.warning(f"No data in status response: {status_result}")

        except Exception as polling_error:
            logger.error(f"Error during polling (attempt {attempt + 1}): {polling_error}")

        # Esperar antes del siguiente check
        await asyncio.sleep(Config.POLLING_INTERVAL)  # ASYNC SLEEP
        attempt += 1

    # Si llegamos aquí, agotamos los intentos
    if not video_sent:
        await processing_msg.edit_text(
            f"⏰ Timeout agotado. La generación del video está tardando demasiado.\n\n"
            f"Request ID: `{request_id}`\n\n"
            f"💡 Inténtalo de nuevo más tarde."
        )
