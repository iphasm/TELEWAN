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
        # Modelos actuales
        'ultra_fast': 'wan-2.2/i2v-480p-ultra-fast',
        'fast': 'wan-2.2/i2v-480p-fast',
        'quality': 'wan-2.2/i2v-720p-ultra-fast',  # Modelo ultra-fast en 720p (según código oficial)
        'text_to_video': 'wan-2.2/t2v-480p-ultra-fast',

        # Modelos expandidos (futuros)
        'cinematic_1080p': 'wan-2.2/i2v-1080p-cinematic',  # Propuesta 1
        'animation_4k': 'wan-2.2/i2v-4k-animation',       # Propuesta 2
        'long_video_60s': 'wan-2.2/i2v-720p-60s-extended', # Propuesta 3
        'stylized_art': 'wan-2.2/i2v-720p-stylized',      # Propuesta 1 variante
        'music_video': 'wan-2.2/i2v-1080p-music-sync',    # Propuesta 2 variante
    }

    # Modelo por defecto
    DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'ultra_fast')

    # ============================================================================
    # 🎬 PROPUESTAS DE EXPANSIÓN PARA EL BOT TELEWAN
    # ============================================================================
    #
    # ANÁLISIS ACTUAL:
    # - 4 modelos básicos: ultra_fast(480p), fast(480p), quality(720p), text_to_video(480p)
    # - Limitaciones: resolución máxima 720p, duración máxima 8s, estilos limitados
    # - Mercado: creciente demanda de video de alta calidad para redes sociales
    #
    # ============================================================================
    # 📊 PROPUESTA 1: MODO CINEMÁTICO 1080P - "CINEBOT"
    # ============================================================================
    #
    # 🎯 OBJETIVO: Videos profesionales de alta calidad para creadores de contenido
    #
    # MODELOS PROPUESTOS:
    # - 'cinematic_1080p': wan-2.2/i2v-1080p-cinematic (FullHD profesional)
    # - 'stylized_art': wan-2.2/i2v-720p-stylized (estilos artísticos únicos)
    #
    # 🎨 CARACTERÍSTICAS:
    # - Resolución: 1080p (FullHD) para YouTube/TikTok profesionales
    # - Estilos: cinematográfico, artístico, comercial
    # - Duración: hasta 15 segundos
    # - Calidad: efectos de iluminación profesional, depth of field
    #
    # 💰 MONETIZACIÓN:
    # - Premium: $0.50 por video (vs $0.10 estándar)
    # - Suscripción mensual: $9.99 para creadores
    # - Templates premium para diferentes industrias
    #
    # 📈 MERCADO OBJETIVO:
    # - Youtubers, TikTok creators, agencias de marketing
    # - Pequeñas empresas que necesitan videos profesionales
    #
    # ============================================================================
    # 🎭 PROPUESTA 2: ANIMACIÓN Y EFECTOS ESPECIALES - "ANIMEBOT"
    # ============================================================================
    #
    # 🎯 OBJETIVO: Contenido animado y efectos visuales para redes sociales
    #
    # MODELOS PROPUESTOS:
    # - 'animation_4k': wan-2.2/i2v-4k-animation (animación de ultra alta calidad)
    # - 'music_video': wan-2.2/i2v-1080p-music-sync (videos sincronizados con música)
    #
    # 🎨 CARACTERÍSTICAS:
    # - Resolución: hasta 4K para animaciones detalladas
    # - Estilos: anime, cartoon, motion graphics, efectos especiales
    # - Sincronización: beats musicales, ritmo automático
    # - Efectos: transiciones suaves, particle effects, morphing
    #
    # 💰 MONETIZACIÓN:
    # - Viral content: $0.30 por video + comisiones por views
    # - NFT creation: integración con OpenSea para arte generado
    # - API para desarrolladores: $99/mes para apps de animación
    #
    # 📈 MERCADO OBJETIVO:
    # - Gamers, animadores, artistas digitales
    # - Creadores de memes y contenido viral
    # - Desarrolladores de juegos indie
    #
    # ============================================================================
    # 🎬 PROPUESTA 3: VIDEOS LARGOS Y NARRATIVOS - "STORYBOT"
    # ============================================================================
    #
    # 🎯 OBJETIVO: Contenido largo para storytelling y educación
    #
    # MODELOS PROPUESTOS:
    # - 'long_video_60s': wan-2.2/i2v-720p-60s-extended (videos narrativos largos)
    # - 'educational': wan-2.2/i2v-720p-educational (contenido educativo)
    # - 'documentary': wan-2.2/i2v-1080p-documentary (estilo documental)
    #
    # 🎨 CARACTERÍSTICAS:
    # - Duración: hasta 60 segundos (7x más que actual)
    # - Narrativa: escenas conectadas, transiciones suaves
    # - Estilos: educativo, documental, tutoriales
    # - Resolución: 720p-1080p manteniendo calidad en videos largos
    #
    # 💰 MONETIZACIÓN:
    # - Educational: $1.00 por video largo (educación premium)
    # - Business: $2.50 por video corporativo (marketing)
    # - API enterprise: $299/mes para empresas
    #
    # 📈 MERCADO OBJETIVO:
    # - Educadores, profesores, e-learning platforms
    # - Empresas B2B, consultores, coaches
    # - Creadores de documentales y contenido educativo
    #
    # ============================================================================
    # 🚀 IMPLEMENTACIÓN TÉCNICA PROPUESTA
    # ============================================================================
    #
    # 1. SISTEMA DE SUSCRIPCIONES:
    #    - Freemium: 5 videos gratis/día
    #    - Pro: $4.99/mes (videos ilimitados básicos)
    #    - Creator: $9.99/mes (acceso a modelos premium)
    #    - Enterprise: $49.99/mes (API + modelos exclusivos)
    #
    # 2. INTERFAZ DE USUARIO:
    #    - Comando /premium para ver opciones disponibles
    #    - Inline keyboard para seleccionar modelo y estilo
    #    - Preview de costos antes de generar
    #
    # 3. OPTIMIZACIONES TÉCNICAS:
    #    - Queue inteligente por tipo de modelo
    #    - Compresión automática para videos largos
    #    - CDN para distribución global
    #
    # ============================================================================
    # 📊 IMPACTO ESPERADO
    # ============================================================================
    #
    # USUARIOS ACTIVOS: +300% (de casuales a creadores profesionales)
    # INGRESOS MENSUALES: +500% (de freemium a modelo premium)
    # MERCADO ALCANZADO: De hobby a herramienta profesional
    # POSICIONAMIENTO: De bot básico a suite creativa completa
    #
    # ============================================================================

    # Configuración del bot
    MAX_VIDEO_DURATION = 8  # segundos
    ASPECT_RATIO = "16:9"
    MAX_POLLING_ATTEMPTS = 240  # máximo ~4-5 minutos de espera con polling inteligente
    POLLING_INTERVAL = 0.5  # segundos base entre checks

    # Configuración de procesamiento asíncrono
    USE_ASYNC_PROCESSING = os.getenv('USE_ASYNC_PROCESSING', 'true').lower() == 'true'
    MAX_ASYNC_WORKERS = int(os.getenv('MAX_ASYNC_WORKERS', '3'))  # Número máximo de workers asíncronos
    ASYNC_TASK_TIMEOUT = int(os.getenv('ASYNC_TASK_TIMEOUT', '300'))  # Timeout para tareas asíncronas (segundos)

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
        "💰 **Cuenta y Premium:**\n"
        "/balance - Consultar saldo disponible en Wavespeed\n"
        "/premium - Explorar modelos premium y opciones avanzadas\n\n"
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
