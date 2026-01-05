"""
FastAPI Application for Event-Driven Architecture
Reemplaza Flask con FastAPI para arquitectura ASGI async
"""
import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn

# Imports de Telegram al inicio para evitar errores de scope
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from config import Config
from bot import (
    start, help_command, list_models_command, handle_text_video,
    handle_quality_video, handle_preview_video, handle_optimize,
    handle_photo, handle_document_image, handle_sticker_image,
    image_document_filter, static_sticker_filter
)

# Importar eventos con manejo de errores
try:
    from events import event_bus, init_event_bus, shutdown_event_bus, init_event_handlers, shutdown_event_handlers
    EVENTS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"⚠️ Sistema de eventos no disponible: {e}")
    EVENTS_AVAILABLE = False
    # Funciones dummy
    async def init_event_bus(): pass
    async def shutdown_event_bus(): pass
    async def init_event_handlers(): pass
    async def shutdown_event_handlers(): pass

# Configurar logging
logger = logging.getLogger(__name__)

async def setup_webhook(telegram_app):
    """Configurar webhook en Telegram"""
    try:
        # Asegurar que la URL tenga https://
        webhook_base_url = Config.WEBHOOK_URL
        if not webhook_base_url.startswith('http'):
            webhook_base_url = f"https://{webhook_base_url}"

        webhook_url = f"{webhook_base_url}{Config.WEBHOOK_PATH}"
        logger.info(f"Webhook URL completa: {webhook_url}")

        # Configurar webhook en Telegram
        await telegram_app.bot.set_webhook(
            url=webhook_url,
            secret_token=os.getenv('WEBHOOK_SECRET_TOKEN')
        )

        logger.info("✅ Webhook configurado exitosamente en Telegram")

    except Exception as e:
        logger.error(f"❌ Error configurando webhook: {e}")
        raise

# Estado global de la aplicación
app_state = {
    "telegram_app": None,
    "start_time": datetime.now(),
    "processed_updates": 0
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejador de ciclo de vida de la aplicación"""
    logger.info("🚀 Iniciando aplicación FastAPI para TELEWAN Bot")

    # Verificar credenciales críticas antes de inicializar
    if not Config.TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN no configurado - aplicación no puede inicializarse")
        app_state["error"] = "TELEGRAM_BOT_TOKEN missing"
        yield
        return

    if not Config.WAVESPEED_API_KEY:
        logger.warning("⚠️  WAVESPEED_API_KEY no configurado - funcionalidades limitadas")

    # Startup: Inicializar componentes del sistema event-driven
    try:
        # 1. Inicializar Event Bus (siempre, no requiere credenciales)
        try:
            await init_event_bus()
            logger.info("✅ Event Bus inicializado correctamente")
        except Exception as e:
            logger.warning(f"⚠️  Event Bus no disponible (Redis): {e} - usando modo sin eventos")
            logger.info("ℹ️  El bot funcionará normalmente sin sistema de eventos avanzado")

        # 2. Inicializar Event Handlers (opcional)
        try:
            await init_event_handlers()
            logger.info("✅ Event Handlers registrados correctamente")
        except Exception as e:
            logger.warning(f"⚠️  Event Handlers no disponibles: {e} - continuando sin handlers")

        # 3. Inicializar aplicación de Telegram (requiere token)
        try:
            # Usar imports del inicio del archivo (no re-importar)
            telegram_app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()

            # Agregar manejadores de comandos
            telegram_app.add_handler(CommandHandler("start", start))
            telegram_app.add_handler(CommandHandler("help", help_command))
            telegram_app.add_handler(CommandHandler("models", list_models_command))
            telegram_app.add_handler(CommandHandler("textvideo", handle_text_video))
            telegram_app.add_handler(CommandHandler("quality", handle_quality_video))
            telegram_app.add_handler(CommandHandler("preview", handle_preview_video))
            telegram_app.add_handler(CommandHandler("optimize", handle_optimize))

            # Agregar manejadores de mensajes (photos, documents, stickers)
            telegram_app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
            telegram_app.add_handler(MessageHandler(image_document_filter, handle_document_image))
            telegram_app.add_handler(MessageHandler(static_sticker_filter, handle_sticker_image))

            # ¡CRÍTICO! Inicializar la aplicación de Telegram para webhook
            await telegram_app.initialize()
            logger.info("✅ Telegram Application inicializado (initialize() llamado)")

            app_state["telegram_app"] = telegram_app
            logger.info("✅ Aplicación de Telegram registrada en app_state")

            # Configurar webhook si está habilitado
            if Config.WEBHOOK_URL:
                try:
                    await setup_webhook(telegram_app)
                except Exception as webhook_error:
                    logger.warning(f"⚠️  Webhook no configurado: {webhook_error} - usando polling")

            logger.info("🎯 Sistema Event-Driven operativo")

        except Exception as telegram_error:
            logger.error(f"❌ Error inicializando Telegram: {telegram_error}")
            app_state["telegram_error"] = str(telegram_error)
            logger.warning("⚠️  Continuando sin Telegram - solo endpoints básicos disponibles")

    except Exception as e:
        logger.error(f"❌ Error inicializando componentes: {e}")
        raise

    yield

    # Shutdown: Limpiar recursos en orden inverso
    logger.info("🛑 Apagando aplicación FastAPI")

    try:
        # 1. Cerrar aplicación de Telegram
        if app_state["telegram_app"]:
            await app_state["telegram_app"].shutdown()
            logger.info("✅ Aplicación de Telegram cerrada correctamente")

        # 2. Cerrar Event Handlers
        await shutdown_event_handlers()
        logger.info("✅ Event Handlers cerrados correctamente")

        # 3. Cerrar Event Bus
        await shutdown_event_bus()
        logger.info("✅ Event Bus cerrado correctamente")

    except Exception as e:
        logger.error(f"❌ Error durante shutdown: {e}")

# Crear aplicación FastAPI
app = FastAPI(
    title="TELEWAN Bot API",
    description="API REST para bot de Telegram que genera videos con IA",
    version="2.0.0",
    lifespan=lifespan
)

@app.get("/", tags=["Health"])
async def root():
    """Endpoint de healthcheck básico - siempre responde"""
    try:
        # Respuesta básica que siempre funciona
        return {
            "status": "ok",
            "service": "TELEWAN Bot API",
            "version": "2.0.0",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": (datetime.now() - app_state["start_time"]).total_seconds(),
            "processed_updates": app_state.get("processed_updates", 0)
        }
    except Exception as e:
        # Fallback si algo falla
        return {
            "status": "error",
            "service": "TELEWAN Bot API",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/health", tags=["Health"])
async def health_check():
    """Healthcheck detallado"""
    components = {
        "fastapi_server": "operational",
        "uptime_seconds": (datetime.now() - app_state["start_time"]).total_seconds()
    }

    # Verificar estado de componentes
    if app_state.get("telegram_app"):
        components["telegram_bot"] = "operational"
    elif app_state.get("telegram_error"):
        components["telegram_bot"] = f"error: {app_state['telegram_error']}"
    else:
        components["telegram_bot"] = "not_initialized"

    # Verificar estado general
    has_critical_errors = (
        app_state.get("telegram_error") or
        not Config.TELEGRAM_BOT_TOKEN
    )

    status = "unhealthy" if has_critical_errors else "healthy"

    response = {
        "status": status,
        "service": "TELEWAN Bot",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "components": components,
        "metrics": {
            "processed_updates": app_state["processed_updates"],
            "start_time": app_state["start_time"].isoformat()
        }
    }

    # Agregar información de errores si existen
    if app_state.get("error"):
        response["error"] = app_state["error"]
    if app_state.get("telegram_error"):
        response["telegram_error"] = app_state["telegram_error"]

    return response

@app.post("/webhook", tags=["Telegram"])
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Endpoint de webhook para recibir actualizaciones de Telegram
    Procesa las actualizaciones de manera asíncrona con BackgroundTasks
    """
    try:
        # Verificar secret token si está configurado
        secret_token = os.getenv('WEBHOOK_SECRET_TOKEN')
        if secret_token:
            received_token = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
            if received_token != secret_token:
                logger.warning("❌ Webhook token inválido")
                raise HTTPException(status_code=401, detail="Invalid webhook token")

        # Obtener datos del webhook
        update_data = await request.json()
        update_id = update_data.get('update_id', 'unknown')

        # Log detallado del update
        message = update_data.get('message', {})
        text = message.get('text', '[no text]') if message else '[no message]'
        from_user = message.get('from', {}) if message else {}
        user_id = from_user.get('id', 'unknown')

        logger.info(f"📨 Webhook recibido: update_id={update_id}, text='{text[:30]}...', user={user_id}")

        # Incrementar contador
        app_state["processed_updates"] += 1

        # Procesar actualización en background
        telegram_app = app_state.get("telegram_app")
        if telegram_app:
            logger.info(f"✅ Enviando update {update_id} a procesamiento")
            background_tasks.add_task(process_telegram_update, update_data)
        else:
            logger.error("❌ Aplicación de Telegram no inicializada - no se puede procesar")
            raise HTTPException(status_code=503, detail="Telegram app not ready")

        return {"status": "accepted", "update_id": update_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error procesando webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def process_telegram_update(update_data: Dict[str, Any]):
    """
    Procesa una actualización de Telegram de manera asíncrona
    """
    try:
        # Update ya está importado al inicio del archivo
        update_id = update_data.get('update_id')
        logger.info(f"🔄 Procesando update {update_id}...")

        # Verificar que la aplicación está lista
        telegram_app = app_state.get("telegram_app")
        if not telegram_app:
            logger.error(f"❌ Telegram app no disponible para update {update_id}")
            return

        # Crear objeto Update desde los datos
        update = Update.de_json(update_data, telegram_app.bot)

        # Verificar si es un mensaje con texto
        if update.message and update.message.text:
            text = update.message.text
            user_id = update.message.from_user.id if update.message.from_user else 'unknown'
            logger.info(f"📨 Mensaje: '{text[:50]}' de user_id={user_id}")

        # Procesar la actualización con el bot
        await telegram_app.process_update(update)

        logger.info(f"✅ Update {update_id} procesado correctamente")

    except Exception as e:
        logger.error(f"❌ Error procesando update {update_data.get('update_id')}: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")

@app.get("/stats", tags=["Monitoring"])
async def get_stats():
    """Estadísticas de la aplicación"""
    return {
        "processed_updates": app_state.get("processed_updates", 0),
        "uptime": (datetime.now() - app_state["start_time"]).total_seconds(),
        "telegram_bot_ready": app_state.get("telegram_app") is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/debug", tags=["Debug"])
async def debug_info():
    """Información de debug para troubleshooting"""
    return {
        "timestamp": datetime.now().isoformat(),
        "environment": {
            "telegram_token": bool(Config.TELEGRAM_BOT_TOKEN),
            "wavespeed_key": bool(Config.WAVESPEED_API_KEY),
            "webhook_url": Config.WEBHOOK_URL,
            "webhook_enabled": Config.USE_WEBHOOK
        },
        "app_state": {
            "telegram_app": app_state.get("telegram_app") is not None,
            "processed_updates": app_state.get("processed_updates", 0),
            "has_error": bool(app_state.get("error")),
            "has_telegram_error": bool(app_state.get("telegram_error"))
        },
        "errors": {
            "config_error": app_state.get("error"),
            "telegram_error": app_state.get("telegram_error")
        }
    }

# Removidos @app.on_event deprecados - usando lifespan en su lugar

def create_app() -> FastAPI:
    """Factory function para crear la aplicación FastAPI"""
    return app

def run_server():
    """Ejecutar servidor con configuración optimizada para producción"""
    try:
        port = int(os.getenv('PORT', Config.WEBHOOK_PORT))
        host = "0.0.0.0"

        logger.info(f"🚀 Iniciando servidor FastAPI en {host}:{port}")
        logger.info(f"📊 Puerto configurado: {port} (usando PORT env si existe)")

        # Usar app directamente para evitar problemas de re-importación
        uvicorn.run(
            app,  # Pasar la instancia directamente
            host=host,
            port=port,
            log_level="info",
            access_log=True,
            server_header=False,  # No exponer información del servidor
            date_header=False,
        )
    except Exception as e:
        logger.error(f"💥 Error fatal iniciando servidor: {e}")
        raise

if __name__ == "__main__":
    run_server()
