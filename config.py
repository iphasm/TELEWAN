import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    # Telegram Bot Token
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

    # Wavespeed API
    WAVESPEED_API_KEY = os.getenv('WAVESPEED_API_KEY')
    WAVESPEED_BASE_URL = os.getenv('WAVESPEED_BASE_URL', 'https://api.wavespeed.ai')

    # Configuración del bot
    MAX_VIDEO_DURATION = 8  # segundos
    ASPECT_RATIO = "16:9"
    MAX_POLLING_ATTEMPTS = 160  # máximo ~1 minuto 20 segundos de espera (160 * 0.5s)
    POLLING_INTERVAL = 0.5  # segundos entre checks (como en el ejemplo)

    # Negative prompt automática para todas las solicitudes
    NEGATIVE_PROMPT = "low quality, worst quality, blurry, artifacts, distortion, deformed, disfigured, ugly, extra limbs, mutated hands, malformed, poor anatomy, distorted face, distorted features, melting face, face morphing, changing face, changing identity, different person, text, watermark, logo, censored, mosaic, black bars, static camera, looped motion, bad transitions, fade transitions, jitter, flicker, clothing, underwear, bra, panties, shirt, pants, accessories, watch, smartwatch, cartoon, 3d render, doll, plastic skin, overexposed, underexposed, cluttered background"

    # Almacenamiento (para Railway u otros servicios)
    VOLUME_PATH = os.getenv('VOLUME_PATH', './storage')  # Default: ./storage

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
