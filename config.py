import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    # Telegram Bot Token
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

    # Autenticación - ID de usuario permitido (opcional)
    ALLOWED_USER_ID = os.getenv('ALLOWED_USER_ID')  # Si no se configura, permite a todos

    # Wavespeed API
    WAVESPEED_API_KEY = os.getenv('WAVESPEED_API_KEY')
    WAVESPEED_BASE_URL = os.getenv('WAVESPEED_BASE_URL', 'https://api.wavespeed.ai')

    # Modelos disponibles de Wavespeed
    AVAILABLE_MODELS = {
        'ultra_fast': 'wan-2.2/i2v-480p-ultra-fast',
        'fast': 'wan-2.2/i2v-480p-fast',
        'quality': 'wan-2.2/i2v-720p-quality',
        'text_to_video': 'wan-2.2/t2v-480p-ultra-fast'
    }

    # Modelo por defecto
    DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'ultra_fast')

    # Configuración del bot
    MAX_VIDEO_DURATION = 8  # segundos
    ASPECT_RATIO = "16:9"
    MAX_POLLING_ATTEMPTS = 240  # máximo ~2 minutos de espera (240 * 0.5s) - más tiempo para videos complejos
    POLLING_INTERVAL = 0.5  # segundos entre checks (como en el ejemplo)

    # Negative prompt automática para todas las solicitudes (configurable via env)
    NEGATIVE_PROMPT = os.getenv('NEGATIVE_PROMPT', '')

    # Mensajes del bot (con valores por defecto razonables)
    WELCOME_MESSAGE = os.getenv('WELCOME_MESSAGE',
        "¡Hola! Soy un bot que transforma fotos en videos usando IA.\n\n"
        "📸 **Cómo usar:**\n"
        "1. Envía una foto con un caption descriptivo\n"
        "2. El bot usará el texto del caption como prompt para generar un video\n"
        "3. Espera a que se procese (puede tomar unos minutos)\n\n"
        "**Ejemplo:**\n"
        "Envía una foto de un paisaje con el caption: \"Un amanecer sobre las montañas con nubes moviéndose suavemente\"\n\n"
        "¡Prueba enviando una foto ahora!"
    )

    HELP_MESSAGE = os.getenv('HELP_MESSAGE',
        "🤖 **Comandos disponibles:**\n\n"
        "/start - Inicia el bot y muestra instrucciones\n"
        "/help - Muestra esta ayuda\n\n"
        "🎬 **Modelos de video:**\n"
        "/models - Ver todos los modelos disponibles\n"
        "/preview - Modo preview rápida (480p ultra fast)\n"
        "/quality - Videos de alta calidad (720p) - más tiempo pero mejor calidad\n\n"
        "🎨 **Optimización:**\n"
        "/optimize - Activar/desactivar optimización IA automática\n\n"
        "💰 **Cuenta:**\n"
        "/balance - Consultar saldo disponible en Wavespeed\n\n"
        "🔄 **Recuperación:**\n"
        "/lastvideo - Recuperar el último video procesado\n\n"
        "🔧 **Diagnóstico:**\n"
        "/debugfiles - Información sobre formatos de archivo soportados\n\n"
        "📥 **Descargas de Videos:**\n"
        "• Envía directamente una URL de Facebook, Instagram, X/Twitter, Reddit o TikTok\n"
        "• O usa: `/download [URL]` para descarga manual\n\n"
        "📝 **Cómo usar:**\n"
        "• Envía una foto con un caption descriptivo\n"
        "• El bot genera un video basado en tu descripción\n"
        "• Los videos tardan entre 30 segundos y 5 minutos\n\n"
        "💡 **Tips:**\n"
        "• Sé descriptivo en tus captions\n"
        "• Incluye detalles de movimiento y estilo\n"
        "• Usa /preview para pruebas rápidas\n"
        "• Usa /quality para resultados finales\n"
        "• Si no recibes un video, usa /lastvideo para recuperarlo"
    )

    NO_CAPTION_MESSAGE = os.getenv('NO_CAPTION_MESSAGE',
        "❌ **Error**: Enviaste una imagen sin descripción (caption).\n\n"
        "Por favor, incluye una descripción detallada de lo que quieres generar, por ejemplo:\n"
        "• 'Una mujer caminando por la ciudad con estilo fashion'\n"
        "• 'Retrato de una persona sonriendo'\n\n"
        "O configura la variable de entorno `DEFAULT_PROMPT` en Railway para usar un prompt automático."
    )

    PROCESSING_MESSAGE = os.getenv('PROCESSING_MESSAGE',
        "🎬 Procesando tu imagen... Esto puede tomar unos minutos."
    )

    ACCESS_DENIED_MESSAGE = os.getenv('ACCESS_DENIED_MESSAGE',
        "❌ Lo siento, este bot es privado y solo puede ser usado por usuarios autorizados."
    )

    # Almacenamiento (para Railway u otros servicios)
    VOLUME_PATH = os.getenv('VOLUME_PATH', './storage')  # Default: ./storage

    # Webhook configuration
    USE_WEBHOOK = os.getenv('USE_WEBHOOK', 'false').lower() == 'true'
    WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # URL completa del webhook
    # Railway asigna el puerto automáticamente mediante la variable PORT
    WEBHOOK_PORT = int(os.getenv('PORT', os.getenv('WEBHOOK_PORT', '8443')))
    WEBHOOK_PATH = os.getenv('WEBHOOK_PATH', '/webhook')

    @classmethod
    def validate(cls):
        """Valida que todas las configuraciones requeridas estén presentes"""
        required_vars = ['TELEGRAM_BOT_TOKEN', 'WAVESPEED_API_KEY']

        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)

        if missing_vars:
            raise ValueError(f"Variables de entorno requeridas faltantes: {', '.join(missing_vars)}")

        return True
