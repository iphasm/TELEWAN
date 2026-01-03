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
    MAX_VIDEO_DURATION = 5  # segundos
    ASPECT_RATIO = "16:9"
    MAX_POLLING_ATTEMPTS = 30  # máximo 5 minutos de espera
    POLLING_INTERVAL = 10  # segundos entre checks

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
