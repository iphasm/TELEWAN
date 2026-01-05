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
    NEGATIVE_PROMPT = os.getenv('NEGATIVE_PROMPT',
        "low quality, worst quality, blurry, artifacts, distortion, deformed, disfigured, ugly, extra limbs, mutated hands, malformed, poor anatomy, distorted face, distorted features, melting face, face morphing, changing face, changing identity, different person, text, watermark, logo, censored, mosaic, black bars, static camera, looped motion, bad transitions, fade transitions, jitter, flicker, clothing, underwear, bra, panties, shirt, pants, accessories, watch, smartwatch, cartoon, 3d render, doll, plastic skin, overexposed, underexposed, cluttered background"
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
