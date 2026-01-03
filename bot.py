import logging
import requests
import time
import io
import os
import uuid
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image
from config import Config

# Configuración del logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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

class WavespeedAPI:
    def __init__(self):
        self.api_key = Config.WAVESPEED_API_KEY
        self.base_url = Config.WAVESPEED_BASE_URL
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    def generate_video(self, prompt: str, image_url: str = None) -> dict:
        """
        Genera un video usando el modelo wan 2.2 i2v 480p ultra fast
        """
        endpoint = f"{self.base_url}/api/v3/wavespeed-ai/wan-2.2/i2v-480p-ultra-fast"

        payload = {
            "duration": Config.MAX_VIDEO_DURATION,
            "image": image_url,  # URL de la imagen enviada por Telegram
            "last_image": "",
            "prompt": prompt,
            "negative_prompt": Config.NEGATIVE_PROMPT,
            "seed": -1
        }

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

    def download_video(self, video_url: str) -> bytes:
        """
        Descarga el video generado
        """
        try:
            response = requests.get(video_url)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            logger.error(f"Error descargando video: {e}")
            raise

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador del comando /start"""
    user_id = update.effective_user.id

    # Verificar autenticación si está configurada
    if Config.ALLOWED_USER_ID and str(user_id) != Config.ALLOWED_USER_ID:
        await update.message.reply_text(
            "❌ Lo siento, este bot es privado y solo puede ser usado por usuarios autorizados."
        )
        logger.warning(f"Acceso denegado para usuario {user_id} en /start")
        return

    welcome_message = """
¡Hola! Soy un bot que transforma fotos en videos usando IA.

📸 **Cómo usar:**
1. Envía una foto con un caption descriptivo
2. El bot usará el texto del caption como prompt para generar un video
3. Espera a que se procese (puede tomar unos minutos)

**Ejemplo:**
Envía una foto de un paisaje con el caption: "Un amanecer sobre las montañas con nubes moviéndose suavemente"

¡Prueba enviando una foto ahora!
    """
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador de fotos enviadas (incluyendo forwards)"""
    try:
        message = update.message
        user_id = message.from_user.id

        # Verificar autenticación si está configurada
        if Config.ALLOWED_USER_ID and str(user_id) != Config.ALLOWED_USER_ID:
            await message.reply_text(
                "❌ Lo siento, este bot es privado y solo puede ser usado por usuarios autorizados."
            )
            logger.warning(f"Acceso denegado para usuario {user_id}")
            return

        # Logging para debug
        logger.info(f"Foto recibida - User: {user_id}, Forward: {bool(message.forward_origin)}, Caption: {bool(message.caption)}")

        # Verificar que hay un caption
        # El bot acepta tanto fotos enviadas directamente como forwards con caption
        if not message.caption:
            await message.reply_text(
                "❌ Por favor, incluye una descripción (caption) con tu foto para generar el video.\n\n"
                "💡 **Tip:** Si estás forwardeando una foto, asegúrate de que el mensaje original tenga un caption descriptivo."
            )
            return

        # Información adicional para forwards
        if message.forward_origin:
            logger.info(f"Procesando foto forwardeada con caption: '{message.caption[:50]}...'")

        # Obtener la foto de mejor calidad
        photo = update.message.photo[-1]  # La última es la de mejor calidad

        # Obtener información del archivo de la foto
        photo_file = await context.bot.get_file(photo.file_id)

        # Construir URL correcta para la imagen (para WaveSpeed API)
        if photo_file.file_path.startswith('http'):
            # file_path ya es una URL completa
            photo_file_url = photo_file.file_path
        else:
            # file_path es relativo, construir URL completa
            photo_file_url = f"https://api.telegram.org/file/bot{Config.TELEGRAM_BOT_TOKEN}/{photo_file.file_path}"

        # Descargar la foto para guardarla localmente
        photo_bytes = await photo_file.download_as_bytearray()

        # Generar nombre único para la imagen y guardarla en el volumen
        image_filename = generate_serial_filename("input", "jpg")
        image_filepath = save_image_to_volume(photo_bytes, image_filename)

        # Procesar la imagen (opcional, por si necesitamos redimensionar)
        image = Image.open(io.BytesIO(photo_bytes))

        # Enviar mensaje de procesamiento
        processing_msg = await update.message.reply_text(
            "🎬 Procesando tu imagen... Esto puede tomar unos minutos."
        )

        # Inicializar API de Wavespeed
        wavespeed = WavespeedAPI()

        # Generar video
        prompt = update.message.caption
        logger.info(f"Generando video con prompt: {prompt}")

        # Llamar a la API
        result = wavespeed.generate_video(prompt, photo_file_url)

        if result.get('data') and result['data'].get('id'):
            request_id = result['data']['id']
            logger.info(f"Task submitted successfully. Request ID: {request_id}")

            # Esperar a que se complete con lógica mejorada y robusta
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

                                    try:
                                        # Descargar el video con validación
                                        video_bytes = wavespeed.download_video(video_url)

                                        if len(video_bytes) > 1000:  # Verificar que tenga contenido significativo
                                            # Generar nombre único para el video y guardarlo en el volumen
                                            video_filename = generate_serial_filename("output", "mp4")
                                            video_filepath = save_video_to_volume(video_bytes, video_filename)
                                            logger.info(f"Video saved to: {video_filepath}")

                                            # Enviar el video desde el archivo guardado
                                            with open(video_filepath, 'rb') as video_file:
                                                sent_message = await context.bot.send_video(
                                                    chat_id=update.effective_chat.id,
                                                    video=video_file,
                                                    caption="¡Aquí está tu video generado! 🎥",
                                                    supports_streaming=True
                                                )

                                            # Confirmar envío exitoso
                                            await processing_msg.edit_text("✅ ¡Video enviado exitosamente!")
                                            logger.info(f"Video sent successfully to user {update.effective_chat.id}")
                                            video_sent = True
                                            return
                                        else:
                                            logger.warning(f"Downloaded video too small: {len(video_bytes)} bytes")

                                    except Exception as download_error:
                                        logger.error(f"Error downloading/sending video (attempt {output_check + 1}): {download_error}")
                                        if output_check < 4:  # No es el último intento
                                            time.sleep(2)  # Esperar antes de reintentar
                                        else:  # Último intento fallido
                                            await processing_msg.edit_text(
                                                f"❌ Error al descargar el video después de múltiples intentos.\n\n"
                                                f"🔗 URL del video: {video_url}\n"
                                                f"💡 Contacta al administrador si el problema persiste."
                                            )
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
                            return
                        elif status in ['processing', 'pending', 'running']:
                            logger.info(f"Task still processing. Status: {status} (attempt {attempt + 1}/{Config.MAX_POLLING_ATTEMPTS})")
                        else:
                            logger.warning(f"Unknown status: {status}")

                    else:
                        logger.warning(f"No data in status response: {status_result}")

                except Exception as polling_error:
                    logger.error(f"Error during polling (attempt {attempt + 1}): {polling_error}")
                    # No romper el loop, continuar intentando

                # Esperar antes del siguiente check
                time.sleep(Config.POLLING_INTERVAL)
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
            await processing_msg.edit_text(
                "❌ Error al iniciar la generación del video."
            )

    except Exception as e:
        logger.error(f"Error procesando foto: {e}")
        await update.message.reply_text(
            "❌ Ocurrió un error inesperado. Por favor, inténtalo de nuevo."
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador del comando /help"""
    user_id = update.effective_user.id

    # Verificar autenticación si está configurada
    if Config.ALLOWED_USER_ID and str(user_id) != Config.ALLOWED_USER_ID:
        await update.message.reply_text(
            "❌ Lo siento, este bot es privado y solo puede ser usado por usuarios autorizados."
        )
        logger.warning(f"Acceso denegado para usuario {user_id} en /help")
        return

    help_text = """
🤖 **Comandos disponibles:**

/start - Inicia el bot y muestra instrucciones
/help - Muestra esta ayuda

📸 **Cómo generar videos:**
- Envía una foto con un caption descriptivo
- El bot usará el caption como prompt para crear un video con IA
- Los videos se generan usando el modelo Wan 2.2 480p Fast

💡 **Tips para mejores resultados:**
- Sé específico en tu descripción
- Incluye detalles sobre movimiento y estilo
- Prueba con diferentes tipos de escenas

¡Disfruta creando videos con IA! 🎬
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

def main() -> None:
    """Función principal"""
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Error de configuración: {e}")
        return

    # Crear aplicación
    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()

    # Agregar manejadores
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Iniciar el bot
    logger.info("Bot iniciado. Presiona Ctrl+C para detener.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
