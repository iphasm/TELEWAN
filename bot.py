import logging
import requests
import time
import io
import os
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Message

# Filtros personalizados para imágenes
def image_document_filter(message: Message) -> bool:
    """Filtro para documentos que son imágenes"""
    if message.document:
        mime_type = message.document.mime_type
        if mime_type and mime_type.startswith('image/'):
            supported_formats = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif']
            return mime_type.lower() in supported_formats
    return False

def static_sticker_filter(message: Message) -> bool:
    """Filtro para stickers estáticos (no animados)"""
    if message.sticker:
        return not message.sticker.is_animated
    return False
from PIL import Image
from config import Config

# Configuración del logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Prompt por defecto cuando no se proporciona caption
DEFAULT_PROMPT = (
    "Absolutely fixed face and head position, zero head movement. No camera movement — a static, hyper-detailed cinematic shot. "
    "She swiftly reaches and removes her entire dress with decisive and strong motion, revealing bare natural breasts with visible nipples, "
    "fully naked body without underwear beneath exposing genitals. Skin texture rendered with extreme realism — soft, lifelike, "
    "with natural pores and subtle sheen under soft, diffused lighting. Moody, atmospheric tone with low-key shadows and ambient glow, "
    "evoking intimacy and tension. Shot in 4K resolution with shallow depth of field, blurring the background to isolate the subject. "
    "Cinematic composition, film grain subtly present, emphasizing emotional gravity and visual precision."
)

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
        "• Fotos (directamente desde la cámara/galería)\n"
        "• Documentos de imagen (JPG, PNG, WebP, GIF)\n"
        "• Stickers estáticos\n\n"
        "💡 Asegúrate de incluir un **caption descriptivo** con tu imagen."
    )

async def handle_image_message(update: Update, context: ContextTypes.DEFAULT_TYPE, image_type: str = "photo") -> None:
    """
    Manejador genérico para mensajes con imágenes (fotos, documentos, stickers)
    """
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
        media_type = "unknown"
        if message.photo:
            media_type = "photo"
        elif message.document:
            media_type = f"document ({message.document.mime_type})"
        elif message.sticker:
            media_type = f"sticker (animated: {message.sticker.is_animated})"

        logger.info(f"Imagen recibida - User: {user_id}, Tipo: {media_type}, Forward: {bool(message.forward_origin)}, Caption: {bool(message.caption)}")

        # Usar caption si existe, sino usar prompt por defecto
        if message.caption:
            prompt = message.caption
            logger.info(f"Usando caption personalizado: '{prompt[:50]}...'")
        else:
            prompt = DEFAULT_PROMPT
            # Informar al usuario que se está usando el prompt por defecto
            await message.reply_text(
                "🎬 **Procesando con prompt automático**\n\n"
                "No proporcionaste un caption, así que usaré un prompt cinematográfico predefinido.\n\n"
                "💡 **Tip:** Para personalizar el video, agrega un caption descriptivo a tu imagen."
            )
            logger.info("Usando prompt por defecto (sin caption proporcionado)")

        # Múltiples métodos de verificación de imagen
        is_image, image_type, error_msg = is_image_message(message)

        if not is_image:
            await message.reply_text(error_msg)
            return

        logger.info(f"Imagen detectada - Tipo: {image_type}, User: {user_id}")

        # Información adicional para forwards
        if message.forward_origin:
            logger.info(f"Procesando imagen forwardeada con caption: '{message.caption[:50]}...'")

        # Obtener la imagen según el tipo detectado
        if image_type == "photo":
            # Foto directa - obtener la mejor calidad
            photo = message.photo[-1]  # La última es la de mejor calidad
            photo_file = await context.bot.get_file(photo.file_id)
        elif image_type == "document":
            # Documento de imagen
            photo_file = await context.bot.get_file(message.document.file_id)
        elif image_type == "sticker":
            # Sticker estático
            photo_file = await context.bot.get_file(message.sticker.file_id)
        else:
            await message.reply_text("❌ Tipo de imagen no soportado.")
            return

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
        logger.info(f"Generando video con prompt: {prompt[:100]}...")

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

def create_app():
    """Crear aplicación Flask para webhooks y healthcheck"""
    app = Flask(__name__)

    # Healthcheck endpoint
    @app.route('/', methods=['GET'])
    def healthcheck():
        logger.info("Healthcheck endpoint called")
        return jsonify({
            "status": "healthy",
            "service": "TELEWAN Bot",
            "timestamp": datetime.now().isoformat()
        }), 200

    # Test endpoint
    @app.route('/test', methods=['GET'])
    def test():
        logger.info("Test endpoint called")
        return jsonify({"message": "TELEWAN Bot is running"}), 200

    return app

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
        logger.info("Configurando bot para usar WEBHOOKS con Flask")
        logger.info(f"WEBHOOK_URL: {Config.WEBHOOK_URL}")
        logger.info(f"WEBHOOK_PORT: {Config.WEBHOOK_PORT}")
        logger.info(f"WEBHOOK_PATH: {Config.WEBHOOK_PATH}")
        logger.info(f"PORT env: {os.getenv('PORT', 'not set')}")

        # Crear aplicación Flask
        app = create_app()

        # Crear aplicación de Telegram
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()

        # Agregar manejadores
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        # Múltiples handlers para diferentes tipos de imágenes
        application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        application.add_handler(MessageHandler(image_document_filter, handle_document_image))
        application.add_handler(MessageHandler(static_sticker_filter, handle_sticker_image))

        # Configurar webhook con Flask
        webhook_path = Config.WEBHOOK_PATH

        @app.route(webhook_path, methods=['POST'])
        def webhook_handler():
            """Manejar webhooks de Telegram"""
            try:
                # Verificar secret token si está configurado
                secret_token = os.getenv('WEBHOOK_SECRET_TOKEN')
                if secret_token:
                    received_token = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
                    if received_token != secret_token:
                        logger.warning("Invalid secret token received")
                        return jsonify({"error": "Unauthorized"}), 401

                # Procesar la actualización
                update_data = request.get_json()
                if update_data:
                    update = Update.de_json(update_data, application.bot)
                    application.process_update(update)
                    return jsonify({"status": "ok"}), 200
                else:
                    return jsonify({"error": "No update data"}), 400

            except Exception as e:
                logger.error(f"Error processing webhook: {e}")
                return jsonify({"error": "Internal server error"}), 500

        # Configurar webhook URL en Telegram
        if Config.WEBHOOK_URL:
            # Asegurar que la URL tenga https://
            webhook_base_url = Config.WEBHOOK_URL
            if not webhook_base_url.startswith('http'):
                webhook_base_url = f"https://{webhook_base_url}"

            webhook_url = f"{webhook_base_url}{webhook_path}"
            logger.info(f"Webhook URL completa: {webhook_url}")

            # Intentar configurar webhook en Telegram
            try:
                telegram_api_url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/setWebhook"
                payload = {"url": webhook_url}
                secret_token = os.getenv('WEBHOOK_SECRET_TOKEN')
                if secret_token:
                    payload["secret_token"] = secret_token

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

        # Iniciar servidor Flask
        logger.info(f"🚀 Iniciando servidor Flask en puerto {Config.WEBHOOK_PORT}")
        logger.info("Servidor web listo para recibir peticiones")

        try:
            app.run(host="0.0.0.0", port=Config.WEBHOOK_PORT, debug=False)
        except Exception as server_error:
            logger.error(f"Error iniciando servidor Flask: {server_error}")
            raise

    else:
        logger.info("Configurando bot para usar POLLING")
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()

        # Agregar manejadores
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
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
