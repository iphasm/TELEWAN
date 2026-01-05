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

from config import Config
from bot import (
    start, help_command, list_models_command, handle_text_video,
    handle_quality_video, handle_preview_video, handle_optimize
)
from events import event_bus, init_event_bus, shutdown_event_bus, init_event_handlers, shutdown_event_handlers

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

    # Startup: Inicializar componentes del sistema event-driven
    try:
        # 1. Inicializar Event Bus
        await init_event_bus()
        logger.info("✅ Event Bus inicializado correctamente")

        # 2. Inicializar Event Handlers
        await init_event_handlers()
        logger.info("✅ Event Handlers registrados correctamente")

        # 3. Inicializar aplicación de Telegram
        from telegram.ext import Application
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
        from telegram.ext import MessageHandler, filters
        from bot import handle_photo, handle_document_image, handle_sticker_image
        from bot import image_document_filter, static_sticker_filter

        telegram_app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        telegram_app.add_handler(MessageHandler(image_document_filter, handle_document_image))
        telegram_app.add_handler(MessageHandler(static_sticker_filter, handle_sticker_image))

        app_state["telegram_app"] = telegram_app
        logger.info("✅ Aplicación de Telegram inicializada correctamente")

        # Configurar webhook si está habilitado
        if Config.WEBHOOK_URL:
            await setup_webhook(telegram_app)

        logger.info("🎯 Sistema Event-Driven completamente operativo")

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
    """Endpoint de healthcheck básico"""
    return {
        "status": "healthy",
        "service": "TELEWAN Bot API",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": (datetime.now() - app_state["start_time"]).total_seconds(),
        "processed_updates": app_state["processed_updates"]
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Healthcheck detallado"""
    telegram_status = "operational" if app_state["telegram_app"] else "initializing"

    return {
        "status": "healthy",
        "service": "TELEWAN Bot",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "telegram_bot": telegram_status,
            "fastapi_server": "operational",
            "uptime_seconds": (datetime.now() - app_state["start_time"]).total_seconds()
        },
        "metrics": {
            "processed_updates": app_state["processed_updates"],
            "start_time": app_state["start_time"].isoformat()
        }
    }

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
        logger.info(f"📨 Webhook recibido: {update_data.get('update_id', 'unknown')}")

        # Incrementar contador
        app_state["processed_updates"] += 1

        # Procesar actualización en background
        if app_state["telegram_app"]:
            background_tasks.add_task(process_telegram_update, update_data)
        else:
            logger.error("❌ Aplicación de Telegram no inicializada")
            raise HTTPException(status_code=503, detail="Telegram app not ready")

        return {"status": "accepted", "update_id": update_data.get("update_id")}

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
        from telegram import Update

        # Crear objeto Update desde los datos
        update = Update.de_json(update_data, app_state["telegram_app"].bot)

        # Procesar la actualización
        await app_state["telegram_app"].process_update(update)

        logger.info(f"✅ Update {update_data.get('update_id')} procesado correctamente")

    except Exception as e:
        logger.error(f"❌ Error procesando update {update_data.get('update_id')}: {e}")

@app.get("/stats", tags=["Monitoring"])
async def get_stats():
    """Estadísticas de la aplicación"""
    return {
        "processed_updates": app_state["processed_updates"],
        "uptime": (datetime.now() - app_state["start_time"]).total_seconds(),
        "telegram_bot_ready": app_state["telegram_app"] is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.on_event("startup")
async def startup_event():
    """Evento de startup adicional"""
    logger.info("🎯 FastAPI startup event - aplicación lista")

@app.on_event("shutdown")
async def shutdown_event():
    """Evento de shutdown"""
    logger.info("🛑 FastAPI shutdown event - limpiando recursos")

def create_app() -> FastAPI:
    """Factory function para crear la aplicación FastAPI"""
    return app

def run_server():
    """Ejecutar servidor con configuración optimizada para producción"""
    port = Config.WEBHOOK_PORT
    host = "0.0.0.0"

    logger.info(f"🚀 Iniciando servidor FastAPI en {host}:{port}")

    uvicorn.run(
        "fastapi_app:app",
        host=host,
        port=port,
        reload=False,  # Desactivar reload en producción
        log_level="info",
        access_log=True,
        server_header=False,  # No exponer información del servidor
        date_header=False
    )

if __name__ == "__main__":
    run_server()
