"""
FastAPI Application for Event-Driven Architecture
Reemplaza Flask con FastAPI para arquitectura ASGI async
"""
import os
import uuid
import asyncio
import aiofiles
import base64
import json
import logging
from datetime import datetime, date
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Form, File, UploadFile
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
import uvicorn

# Translation imports
try:
    from deep_translator import GoogleTranslator
    from langdetect import detect
    TRANSLATION_AVAILABLE = True
    # Define exception for langdetect errors (langdetect doesn't export LangDetectError in some versions)
    LangDetectError = Exception
except ImportError as e:
    print(f"⚠️ Translation libraries import failed: {e}. Install with: pip install deep-translator langdetect")
    TRANSLATION_AVAILABLE = False
    GoogleTranslator = None
    detect = None
    LangDetectError = Exception

# Imports de Telegram al inicio para evitar errores de scope
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from config import Config
from bot import (
    start, help_command, list_models_command, handle_text_video,
    handle_quality_video, handle_preview_video, handle_optimize, handle_lastvideo, handle_balance, handle_debug_files, handle_download, handle_social_url,
    handle_photo, handle_document_image, handle_sticker_image,
    image_document_filter, static_sticker_filter
)

# Sistema de eventos DESHABILITADO temporalmente para debugging
# Los eventos requieren Redis que no está disponible en Railway free tier
EVENTS_AVAILABLE = False
async def init_event_bus(): pass
async def shutdown_event_bus(): pass
async def init_event_handlers(): pass
async def shutdown_event_handlers(): pass

# Configurar logging
logger = logging.getLogger(__name__)

# Funciones de utilidad (migradas de web_app.py)
def generate_fingerprint(client_ip: str, user_agent: str = "", fingerprint_data: Dict[str, Any] = None) -> str:
    """Generate a unique fingerprint for the user"""
    import hashlib

    # Create fingerprint from available data
    fingerprint_parts = [client_ip]

    if user_agent:
        fingerprint_parts.append(user_agent[:50])  # First 50 chars of user agent

    if fingerprint_data:
        # Add browser fingerprint data if available
        for key in ['canvas', 'webgl', 'screen', 'timezone']:
            if key in fingerprint_data:
                fingerprint_parts.append(str(fingerprint_data[key]))

    # Create hash
    fingerprint_string = "|".join(fingerprint_parts)
    return hashlib.sha256(fingerprint_string.encode()).hexdigest()[:16]

def associate_fingerprint_with_ip(usage_data: Dict[str, Any], client_ip: str, fingerprint: str):
    """Associate a fingerprint with an IP address for tracking"""
    ip_fingerprints = usage_data.setdefault("ip_fingerprints", {})
    if client_ip not in ip_fingerprints:
        ip_fingerprints[client_ip] = []

    if fingerprint not in ip_fingerprints[client_ip]:
        ip_fingerprints[client_ip].append(fingerprint)

def is_suspicious_user(usage_data: Dict[str, Any], fingerprint: str) -> bool:
    """Check if user is flagged as suspicious"""
    suspicious_users = usage_data.get("suspicious_users", {})
    return fingerprint in suspicious_users

def flag_suspicious_user(usage_data: Dict[str, Any], fingerprint: str, reason: str):
    """Flag a user as suspicious"""
    suspicious_users = usage_data.setdefault("suspicious_users", {})
    suspicious_users[fingerprint] = {
        "flagged_at": datetime.now().isoformat(),
        "reason": reason
    }
    save_usage_data(usage_data)

def detect_language(text: str) -> str:
    """Detect the language of the given text"""
    if not TRANSLATION_AVAILABLE:
        return "en"  # Default to English if translation not available

    try:
        detected = detect(text)
        logger.info(f"🌐 Language detected: {detected}")
        return detected
    except (LangDetectError, Exception) as e:
        logger.warning(f"⚠️ Language detection failed: {e}, defaulting to English")
        return "en"

def translate_to_english(text: str) -> tuple[str, bool]:
    """Translate text to English if not already in English"""
    if not TRANSLATION_AVAILABLE:
        return text, False

    try:
        detected_lang = detect_language(text)
        if detected_lang == "en":
            logger.info("🌐 Text already in English")
            return text, False

        logger.info(f"🌐 Translating from {detected_lang} to English")
        translator = GoogleTranslator(source=detected_lang, target="en")
        translated = translator.translate(text)

        logger.info(f"🌐 Translation: '{text[:50]}...' → '{translated[:50]}...'")
        return translated, True

    except Exception as e:
        logger.error(f"❌ Translation failed: {e}")
        return text, False

def load_usage_data() -> Dict[str, Any]:
    """Load usage data from file"""
    try:
        with open("usage_data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"daily_usage": {}, "ip_fingerprints": {}, "suspicious_users": {}}
    except Exception as e:
        logger.error(f"Error loading usage data: {e}")
        return {"daily_usage": {}, "ip_fingerprints": {}, "suspicious_users": {}}

def save_usage_data(data: Dict[str, Any]):
    """Save usage data to file"""
    try:
        with open("usage_data.json", "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving usage data: {e}")

def check_rate_limit_advanced(client_ip: str, fingerprint: str, user_agent: str = "") -> tuple[bool, int, int, bool]:
    """Advanced rate limiting with fingerprinting and VPN detection"""
    usage_data = load_usage_data()
    today = date.today().isoformat()

    # Initialize today's data
    if today not in usage_data["daily_usage"]:
        usage_data["daily_usage"][today] = {}

    today_usage = usage_data["daily_usage"][today]

    # Associate fingerprint with IP
    associate_fingerprint_with_ip(usage_data, client_ip, fingerprint)

    # Check for suspicious activity
    ip_fingerprints = usage_data.get("ip_fingerprints", {}).get(client_ip, [])
    is_vpn_suspicious = len(ip_fingerprints) > 3  # More than 3 fingerprints from same IP

    # Check usage for this fingerprint
    fingerprint_usage = today_usage.get(fingerprint, 0)

    # Allow 5 videos per day per fingerprint
    limit = 5
    remaining = max(0, limit - fingerprint_usage)

    # Apply rate limit
    if fingerprint_usage >= limit:
        logger.warning(f"🚫 Rate limit exceeded for fingerprint {fingerprint[:8]}...: {fingerprint_usage}/{limit}")
        return False, remaining, fingerprint_usage, is_vpn_suspicious

    # Check for suspicious patterns
    if is_vpn_suspicious and not is_suspicious_user(usage_data, fingerprint):
        logger.warning(f"🚨 Suspicious activity detected: IP {client_ip} has {len(ip_fingerprints)} fingerprints")
        flag_suspicious_user(usage_data, fingerprint, f"Multiple fingerprints from IP: {len(ip_fingerprints)}")

    return True, remaining, fingerprint_usage, is_vpn_suspicious

def increment_usage_advanced(fingerprint: str):
    """Increment usage counter for a fingerprint"""
    usage_data = load_usage_data()
    today = date.today().isoformat()

    if today not in usage_data["daily_usage"]:
        usage_data["daily_usage"][today] = {}

    usage_data["daily_usage"][today][fingerprint] = usage_data["daily_usage"][today].get(fingerprint, 0) + 1
    save_usage_data(usage_data)

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

# Gestión de tareas de video (migrado de web_app.py)
tasks: Dict[str, Dict[str, Any]] = {}

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

    # Startup: Inicializar bot de Telegram (eventos deshabilitados temporalmente)
    try:
        logger.info("ℹ️  Sistema de eventos deshabilitado - usando modo directo")

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
            telegram_app.add_handler(CommandHandler("lastvideo", handle_lastvideo))
            telegram_app.add_handler(CommandHandler("balance", handle_balance))
            telegram_app.add_handler(CommandHandler("debugfiles", handle_debug_files))
            telegram_app.add_handler(CommandHandler("download", handle_download))

            # Handler automático para URLs de redes sociales (PRIORIDAD ALTA)
            telegram_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_social_url))

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
            if Config.USE_WEBHOOK:
                # Verificar que WEBHOOK_URL esté configurada
                if not Config.WEBHOOK_URL:
                    if os.getenv('RAILWAY_ENVIRONMENT'):
                        logger.error("❌ WEBHOOK_URL no configurada - REQUERIDA para Railway")
                        logger.error("💡 Configurar en Railway Dashboard > Variables > WEBHOOK_URL")
                        logger.error("💡 Formato esperado: https://tu-proyecto.up.railway.app")
                        logger.error("💡 El nombre del proyecto se encuentra en la URL de Railway")
                        raise ValueError("WEBHOOK_URL requerida para Railway pero no configurada")
                    else:
                        logger.warning("⚠️  WEBHOOK_URL no configurada - usando modo local sin webhook")

                if Config.WEBHOOK_URL:
                    try:
                        await setup_webhook(telegram_app)
                        logger.info("✅ Webhook configurado correctamente")
                    except Exception as webhook_error:
                        logger.error(f"❌ Error configurando webhook: {webhook_error}")
                        logger.warning("⚠️  El bot no funcionará sin webhook en Railway")
                        raise webhook_error  # En Railway, webhook es obligatorio
                else:
                    logger.error("❌ WEBHOOK_URL no configurada - requerida para Railway")
                    logger.error("💡 Configura WEBHOOK_URL en las variables de entorno de Railway")
                    raise ValueError("WEBHOOK_URL requerida para funcionamiento en Railway")
            else:
                logger.warning("⚠️  USE_WEBHOOK=false - el bot no funcionará en Railway sin webhooks")

            logger.info("🎯 Sistema Event-Driven operativo")

        except Exception as telegram_error:
            logger.error(f"❌ Error inicializando Telegram: {telegram_error}")
            app_state["telegram_error"] = str(telegram_error)
            logger.warning("⚠️  Continuando sin Telegram - solo endpoints básicos disponibles")

    except Exception as e:
        logger.error(f"❌ Error inicializando componentes: {e}")
        raise

    # Ejecutar diagnóstico automático al iniciar
    logger.info("🔍 Ejecutando diagnóstico automático de inicio...")
    try:
        await run_startup_diagnosis()
    except Exception as diag_error:
        logger.error(f"❌ Error en diagnóstico de inicio: {diag_error}")

    yield

    # Shutdown: Limpiar recursos en orden inverso
    logger.info("🛑 Apagando aplicación FastAPI")

    try:
        # Cerrar aplicación de Telegram
        if app_state["telegram_app"]:
            await app_state["telegram_app"].shutdown()
            logger.info("✅ Aplicación de Telegram cerrada correctamente")
    except Exception as e:
        logger.error(f"❌ Error durante shutdown: {e}")

# Crear aplicación FastAPI
app = FastAPI(
    title="TELEWAN Bot API",
    description="API REST para bot de Telegram que genera videos con IA",
    version="2.0.0",
    lifespan=lifespan
)

# Endpoint raíz duplicado eliminado - causa conflicto con endpoint que sirve HTML

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

@app.post("/wavespeed-webhook", tags=["Wavespeed"])
async def wavespeed_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Endpoint para recibir webhooks de Wavespeed AI cuando los videos estén listos
    (Funcionalidad futura - Wavespeed aún no soporta webhooks)
    """
    try:
        webhook_data = await request.json()
        logger.info(f"🎣 Webhook recibido de Wavespeed: {webhook_data}")

        # Aquí iría la lógica para procesar notificaciones de Wavespeed
        # Por ahora solo loggeamos y retornamos OK

        return {"status": "received", "message": "Webhook processed successfully"}

    except Exception as e:
        logger.error(f"❌ Error procesando webhook de Wavespeed: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")

@app.post("/webhook", tags=["Telegram"])
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Endpoint de webhook para recibir actualizaciones de Telegram
    Procesa las actualizaciones de manera asíncrona con BackgroundTasks
    """
    try:
        # Log detallado de la request para debugging
        logger.info("🔗 Webhook request received")
        logger.info(f"   Method: {request.method}")
        logger.info(f"   URL: {request.url}")
        logger.info(f"   Headers: {dict(request.headers)}")
        logger.info(f"   Content-Type: {request.headers.get('content-type', 'unknown')}")

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
        logger.info(f"   Message keys: {list(message.keys()) if message else 'No message'}")

        # Incrementar contador
        app_state["processed_updates"] += 1

        # Procesar actualización en background
        telegram_app = app_state.get("telegram_app")
        if telegram_app:
            logger.info(f"✅ Enviando update {update_id} a procesamiento")
            logger.info("🔍 Detalles del update a procesar:")
            logger.info(f"   Update ID: {update_id}")
            logger.info(f"   Message: {text}")
            logger.info(f"   User ID: {user_id}")
            background_tasks.add_task(process_telegram_update, update_data)
        else:
            logger.error("❌ Aplicación de Telegram no inicializada - no se puede procesar")
            logger.error(f"   app_state keys: {list(app_state.keys())}")
            logger.error(f"   telegram_app in app_state: {'telegram_app' in app_state}")
            raise HTTPException(status_code=503, detail="Telegram app not ready")

        return {"status": "accepted", "update_id": update_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error procesando webhook: {e}")
        import traceback
        logger.error(f"   Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/webhook", tags=["Telegram"])
async def telegram_webhook_get():
    """
    Endpoint GET para webhook (por compatibilidad)
    Telegram a veces hace requests GET para verificar
    """
    logger.info("🔗 Webhook GET request (verificación de Telegram)")
    return {"status": "webhook_endpoint_active"}

async def process_telegram_update(update_data: Dict[str, Any]):
    """
    Procesa una actualización de Telegram de manera asíncrona
    """
    try:
        # Update ya está importado al inicio del archivo
        update_id = update_data.get('update_id')
        logger.info(f"🔄 Procesando update {update_id}...")
        logger.info(f"   Update keys: {list(update_data.keys())}")

        # Verificar que la aplicación está lista
        telegram_app = app_state.get("telegram_app")
        if not telegram_app:
            logger.error(f"❌ Telegram app no disponible para update {update_id}")
            return

        # Crear objeto Update desde los datos
        update = Update.de_json(update_data, telegram_app.bot)
        logger.info(f"   Update object created: {type(update)}")

        # Log detallado del tipo de update
        if update.message:
            logger.info(f"   Tipo: Message")
            if update.message.photo:
                logger.info(f"   Contiene: Photo ({len(update.message.photo)} tamaños)")
                if update.message.caption:
                    logger.info(f"   Caption: '{update.message.caption[:50]}...'")
                else:
                    logger.info(f"   Caption: None (sin caption)")
            elif update.message.document:
                logger.info(f"   Contiene: Document ({update.message.document.mime_type})")
            elif update.message.sticker:
                logger.info(f"   Contiene: Sticker (animated: {update.message.sticker.is_animated})")
            elif update.message.text:
                logger.info(f"   Contiene: Text '{update.message.text[:50]}...'")
            else:
                logger.info(f"   Contiene: Otro tipo de mensaje")

            user_id = update.message.from_user.id if update.message.from_user else 'unknown'
            logger.info(f"   De usuario: {user_id}")
        elif update.callback_query:
            logger.info(f"   Tipo: Callback Query")
        else:
            logger.info(f"   Tipo: Otro ({type(update).__name__})")

        # Procesar la actualización con el bot
        logger.info(f"   🔄 Enviando a telegram_app.process_update()...")
        logger.info(f"   📋 Handlers registrados: {len(telegram_app.handlers[0])}")

        try:
            await telegram_app.process_update(update)
            logger.info(f"✅ Update {update_id} procesado correctamente por telegram_app")

            # Verificar si se envió respuesta
            if update.message:
                logger.info(f"   📤 Verificando si se envió respuesta al mensaje {update.message.message_id}")

        except Exception as process_error:
            logger.error(f"❌ Error procesando update {update_id}: {process_error}")
            import traceback
            logger.error(f"   📄 Traceback: {traceback.format_exc()}")
            raise

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

async def run_startup_diagnosis():
    """Ejecutar diagnóstico automáticamente al iniciar"""
    print("\n" + "="*60)
    print("🔍 DIAGNÓSTICO AUTOMÁTICO DE INICIO")
    print("="*60)

    try:
        # Verificar variables críticas
        print("📋 VERIFICANDO VARIABLES:")
        token = Config.TELEGRAM_BOT_TOKEN
        webhook_url = Config.WEBHOOK_URL

        if token:
            print(f"   ✅ TELEGRAM_BOT_TOKEN: {token[:10]}***")
        else:
            print("   ❌ TELEGRAM_BOT_TOKEN: NO CONFIGURADA")

        if webhook_url:
            print(f"   ✅ WEBHOOK_URL: {webhook_url}")
        else:
            print("   ❌ WEBHOOK_URL: NO CONFIGURADA")

        if Config.USE_WEBHOOK:
            print("   ✅ USE_WEBHOOK: true (modo webhook)")
        else:
            print("   ⚠️  USE_WEBHOOK: false (modo polling)")

        # Verificar conectividad con Telegram
        if token:
            print("\n🤖 VERIFICANDO CONECTIVIDAD CON TELEGRAM:")
            try:
                import requests
                response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('ok'):
                        bot_username = data['result'].get('username')
                        print(f"   ✅ Bot conectado: @{bot_username}")
                    else:
                        print(f"   ❌ Token inválido: {data.get('description')}")
                else:
                    print(f"   ❌ Error HTTP {response.status_code}")
            except Exception as e:
                print(f"   ❌ Error conectando: {e}")

        # Verificar webhook si está configurado
        if token and webhook_url:
            print("\n🔗 VERIFICANDO CONFIGURACIÓN DEL WEBHOOK:")
            try:
                response = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('ok'):
                        webhook_info = data.get('result', {})
                        current_url = webhook_info.get('url', '')
                        pending = webhook_info.get('pending_update_count', 0)

                        if current_url:
                            expected_url = f"{webhook_url}/webhook" if not webhook_url.endswith('/webhook') else webhook_url
                            if current_url == expected_url:
                                print(f"   ✅ Webhook configurado correctamente: {current_url}")
                            else:
                                print(f"   ❌ Webhook URL incorrecta: {current_url} (esperada: {expected_url})")

                            if pending > 0:
                                print(f"   ⚠️  HAY {pending} MENSAJES PENDIENTES - EL BOT NO ESTÁ PROCESANDO")
                        else:
                            print("   ❌ NO HAY WEBHOOK CONFIGURADO EN TELEGRAM")
                    else:
                        print(f"   ❌ Error obteniendo webhook info: {data.get('description')}")
                else:
                    print(f"   ❌ Error HTTP {response.status_code}")
            except Exception as e:
                print(f"   ❌ Error verificando webhook: {e}")

        print("\n✅ DIAGNÓSTICO DE INICIO COMPLETADO")
        print("📊 Revisa los logs de Railway para ver los resultados detallados")

    except Exception as e:
        print(f"❌ Error en diagnóstico de inicio: {e}")

@app.get("/test", tags=["Test"])
async def test_endpoint():
    """Endpoint de prueba simple"""
    return {"status": "ok", "message": "Test endpoint working", "timestamp": datetime.now().isoformat()}

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

@app.get("/diagnose", tags=["Diagnosis"])
async def run_live_diagnosis():
    """Endpoint de diagnóstico accesible via web"""
    print("\n🔍 EJECUTANDO DIAGNÓSTICO VIA WEB ENDPOINT")
    print("="*50)

    diagnosis_results = {
        "timestamp": datetime.now().isoformat(),
        "status": "running",
        "checks": {}
    }

    try:
        # Verificar variables
        diagnosis_results["checks"]["variables"] = {
            "telegram_token": bool(Config.TELEGRAM_BOT_TOKEN),
            "webhook_url": bool(Config.WEBHOOK_URL),
            "use_webhook": Config.USE_WEBHOOK,
            "wavespeed_key": bool(Config.WAVESPEED_API_KEY)
        }

        print("📋 Variables verificadas")

        # Verificar aplicación
        diagnosis_results["checks"]["application"] = {
            "telegram_app_initialized": app_state.get("telegram_app") is not None,
            "processed_updates": app_state.get("processed_updates", 0),
            "has_error": bool(app_state.get("error")),
            "has_telegram_error": bool(app_state.get("telegram_error"))
        }

        print("🏥 Estado de aplicación verificado")

        # Verificar Telegram API
        if Config.TELEGRAM_BOT_TOKEN:
            try:
                import requests
                response = requests.get(f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/getMe", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('ok'):
                        diagnosis_results["checks"]["telegram_api"] = {
                            "connected": True,
                            "bot_username": data['result'].get('username'),
                            "bot_id": data['result'].get('id')
                        }
                        print("🤖 API de Telegram OK")
                    else:
                        diagnosis_results["checks"]["telegram_api"] = {
                            "connected": False,
                            "error": data.get('description')
                        }
                else:
                    diagnosis_results["checks"]["telegram_api"] = {
                        "connected": False,
                        "error": f"HTTP {response.status_code}"
                    }
            except Exception as e:
                diagnosis_results["checks"]["telegram_api"] = {
                    "connected": False,
                    "error": str(e)
                }
        else:
            diagnosis_results["checks"]["telegram_api"] = {
                "connected": False,
                "error": "No token configured"
            }

        # Verificar webhook
        if Config.TELEGRAM_BOT_TOKEN and Config.WEBHOOK_URL:
            try:
                response = requests.get(f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/getWebhookInfo", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('ok'):
                        webhook_info = data.get('result', {})
                        current_url = webhook_info.get('url', '')
                        pending = webhook_info.get('pending_update_count', 0)

                        expected_url = Config.WEBHOOK_URL
                        if not expected_url.endswith('/webhook'):
                            expected_url += '/webhook'

                        diagnosis_results["checks"]["webhook"] = {
                            "configured": bool(current_url),
                            "current_url": current_url,
                            "expected_url": expected_url,
                            "url_matches": current_url == expected_url,
                            "pending_updates": pending,
                            "has_pending": pending > 0
                        }

                        print("🔗 Webhook verificado")
                    else:
                        diagnosis_results["checks"]["webhook"] = {
                            "configured": False,
                            "error": data.get('description')
                        }
                else:
                    diagnosis_results["checks"]["webhook"] = {
                        "configured": False,
                        "error": f"HTTP {response.status_code}"
                    }
            except Exception as e:
                diagnosis_results["checks"]["webhook"] = {
                    "configured": False,
                    "error": str(e)
                }
        else:
            diagnosis_results["checks"]["webhook"] = {
                "configured": False,
                "error": "Missing token or webhook URL"
            }

        # Probar endpoint del webhook
        if Config.WEBHOOK_URL:
            try:
                webhook_url = Config.WEBHOOK_URL
                if not webhook_url.startswith('http'):
                    webhook_url = f"https://{webhook_url}"

                health_url = f"{webhook_url}/health"
                response = requests.get(health_url, timeout=5)

                if response.status_code == 200:
                    data = response.json()
                    diagnosis_results["checks"]["webhook_endpoint"] = {
                        "reachable": True,
                        "status": data.get('status'),
                        "telegram_bot_status": data.get('components', {}).get('telegram_bot')
                    }
                    print("🌐 Endpoint del webhook accesible")
                else:
                    diagnosis_results["checks"]["webhook_endpoint"] = {
                        "reachable": False,
                        "error": f"HTTP {response.status_code}"
                    }
            except Exception as e:
                diagnosis_results["checks"]["webhook_endpoint"] = {
                    "reachable": False,
                    "error": str(e)
                }
        else:
            diagnosis_results["checks"]["webhook_endpoint"] = {
                "reachable": False,
                "error": "No webhook URL"
            }

        # Calcular estado general
        all_checks = diagnosis_results["checks"]
        has_critical_errors = (
            not all_checks.get("variables", {}).get("telegram_token", False) or
            not all_checks.get("telegram_api", {}).get("connected", False) or
            not all_checks.get("webhook", {}).get("configured", False) or
            all_checks.get("webhook", {}).get("has_pending", False) or
            not all_checks.get("webhook_endpoint", {}).get("reachable", False)
        )

        diagnosis_results["status"] = "error" if has_critical_errors else "ok"

        print("✅ Diagnóstico completado via web")
        print(f"📊 Estado: {diagnosis_results['status']}")

        return diagnosis_results

    except Exception as e:
        print(f"❌ Error en diagnóstico web: {e}")
        diagnosis_results["status"] = "error"
        diagnosis_results["error"] = str(e)
        return diagnosis_results

@app.get("/diagnose/text", tags=["Diagnosis"])
async def diagnose_text():
    """Diagnóstico en formato texto simple (para curl)"""
    lines = ["🔍 DIAGNÓSTICO DEL BOT TELEWAN", "="*50]

    try:
        # Variables
        lines.append("📋 VARIABLES:")
        lines.append(f"   TELEGRAM_BOT_TOKEN: {'✅' if Config.TELEGRAM_BOT_TOKEN else '❌'}")
        lines.append(f"   WEBHOOK_URL: {'✅' if Config.WEBHOOK_URL else '❌'}")
        lines.append(f"   USE_WEBHOOK: {'✅' if Config.USE_WEBHOOK else '❌'}")

        # Aplicación
        lines.append("\n🏥 APLICACIÓN:")
        lines.append(f"   Telegram App: {'✅' if app_state.get('telegram_app') else '❌'}")
        lines.append(f"   Updates procesados: {app_state.get('processed_updates', 0)}")

        # Telegram API
        if Config.TELEGRAM_BOT_TOKEN:
            lines.append("\n🤖 TELEGRAM API:")
            try:
                import requests
                response = requests.get(f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/getMe", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('ok'):
                        bot_username = data['result'].get('username')
                        lines.append(f"   Conectado: ✅ (@{bot_username})")
                    else:
                        lines.append(f"   Conectado: ❌ ({data.get('description')})")
                else:
                    lines.append(f"   Conectado: ❌ (HTTP {response.status_code})")
            except Exception as e:
                lines.append(f"   Conectado: ❌ ({str(e)})")
        else:
            lines.append("\n🤖 TELEGRAM API: ❌ (No token)")

        # Webhook
        if Config.TELEGRAM_BOT_TOKEN and Config.WEBHOOK_URL:
            lines.append("\n🔗 WEBHOOK:")
            try:
                response = requests.get(f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/getWebhookInfo", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('ok'):
                        webhook_info = data.get('result', {})
                        current_url = webhook_info.get('url', '')
                        pending = webhook_info.get('pending_update_count', 0)

                        if current_url:
                            expected_url = Config.WEBHOOK_URL
                            if not expected_url.endswith('/webhook'):
                                expected_url += '/webhook'
                            url_ok = current_url == expected_url
                            lines.append(f"   Configurado: ✅")
                            lines.append(f"   URL correcta: {'✅' if url_ok else '❌'}")
                            if pending > 0:
                                lines.append(f"   Mensajes pendientes: ⚠️ ({pending})")
                        else:
                            lines.append("   Configurado: ❌")
            except Exception as e:
                lines.append(f"   Error: ❌ ({str(e)})")
        else:
            lines.append("\n🔗 WEBHOOK: ❌ (Faltan credenciales)")

        lines.append("\n✅ DIAGNÓSTICO COMPLETADO")
        return {"diagnosis": "\n".join(lines)}

    except Exception as e:
        return {"diagnosis": f"❌ Error en diagnóstico: {str(e)}"}

# Función de procesamiento de video (migrada de web_app.py)
async def process_video_generation(task_id: str):
    """Process video generation in background"""
    try:
        task = tasks[task_id]
        logger.info(f"🎬 Starting video generation for task {task_id}")

        # Import async functions
        from async_wavespeed import generate_video, add_audio_to_video, upscale_video_to_1080p

        # Step 1: Generate base video
        logger.info("🎬 Generating base video...")
        result = await generate_video(
            prompt=task["final_prompt"],
            model=task["model"],
            image_url=task.get("image_url")
        )

        if not result or "video_url" not in result:
            raise Exception(f"Video generation failed: {result}")

        video_url = result["video_url"]
        logger.info(f"✅ Base video generated: {video_url}")

        # Step 2: Add audio if requested
        if task.get("add_audio"):
            logger.info("🎵 Adding audio to video...")
            audio_result = await add_audio_to_video(video_url, task["final_prompt"])

            if audio_result and "video_url" in audio_result:
                video_url = audio_result["video_url"]
                logger.info(f"✅ Audio added: {video_url}")
            else:
                logger.warning(f"⚠️ Audio addition failed: {audio_result}")

        # Step 3: Upscale to 1080p if requested
        if task.get("upscale_1080p"):
            logger.info("📈 Upscaling video to 1080p...")
            upscale_result = await upscale_video_to_1080p(video_url)

            if upscale_result and "video_url" in upscale_result:
                video_url = upscale_result["video_url"]
                logger.info(f"✅ Video upscaled: {video_url}")
            else:
                logger.warning(f"⚠️ Upscaling failed: {upscale_result}")

        # Update task as completed
        task["status"] = "completed"
        task["video_url"] = video_url
        task["completed_at"] = datetime.now().isoformat()

        logger.info(f"🎉 Task {task_id} completed successfully")

    except Exception as e:
        logger.error(f"❌ Task {task_id} failed: {e}")
        task = tasks.get(task_id)
        if task:
            task["status"] = "failed"
            task["error"] = str(e)

# Endpoints del frontend (migrados de web_app.py)

@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
async def root():
    """Serve the main web interface"""
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="index.html not found")

@app.get("/diagnose.html", response_class=HTMLResponse, tags=["Diagnosis"])
async def diagnose_page():
    """Serve the diagnosis web interface"""
    try:
        with open("diagnose.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="diagnose.html not found")

@app.post("/generate", tags=["Video Generation"])
async def generate_video(
    background_tasks: BackgroundTasks,
    image: Optional[UploadFile] = File(None),
    prompt: str = Form(...),
    model: str = Form("ultra_fast"),
    auto_optimize: bool = Form(False),
    add_audio: bool = Form(False),
    upscale_1080p: bool = Form(False),
    fingerprint: str = Form(""),  # Browser fingerprint
    request: Request = None  # For getting client IP
):
    """
    Start video generation process
    """
    try:
        # Get client IP and user agent for advanced rate limiting
        client_ip = request.client.host if request else "unknown"
        user_agent = request.headers.get("user-agent", "") if request else ""

        # Generate or use provided fingerprint
        if not fingerprint:
            fingerprint = generate_fingerprint(client_ip, user_agent)

        logger.info(f"🎯 Request from IP: {client_ip}, Fingerprint: {fingerprint[:16]}...")

        # Check rate limit
        allowed, remaining, used, is_vpn_suspicious = check_rate_limit_advanced(client_ip, fingerprint, user_agent)
        if not allowed:
            return {
                "error": f"Rate limit exceeded. Used {used}/5 videos today. Try again tomorrow.",
                "remaining": remaining,
                "is_vpn_suspicious": is_vpn_suspicious
            }

        # Validate inputs
        if not prompt.strip():
            return {"error": "Prompt cannot be empty"}

        if model not in Config.AVAILABLE_MODELS:
            return {"error": f"Invalid model. Available: {list(Config.AVAILABLE_MODELS.keys())}"}

        # Handle image upload
        image_url = None
        if image:
            # Save uploaded image
            image_filename = f"input_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.jpg"
            image_path = Path(Config.VOLUME_PATH) / image_filename

            # Ensure storage directory exists
            image_path.parent.mkdir(exist_ok=True)

            # Save image
            async with aiofiles.open(image_path, 'wb') as f:
                content = await image.read()
                await f.write(content)

            # Create URL for the image
            image_url = f"/images/{image_filename}"
            logger.info(f"🖼️ Image saved: {image_path}")

        # Process prompt
        original_prompt = prompt
        translated_prompt = None
        optimized_prompt = None

        # Detect language and translate if needed
        detected_lang = detect_language(prompt)
        if detected_lang != "en":
            translated_prompt, was_translated = translate_to_english(prompt)
            if was_translated:
                prompt = translated_prompt
                logger.info(f"🌐 Translated prompt: {prompt[:100]}...")

        # Optimize prompt if requested
        if auto_optimize:
            try:
                logger.info("🤖 Optimizing prompt...")
                from async_wavespeed import optimize_prompt_v3

                if image_url:
                    # Image-to-video with optimization
                    result = await optimize_prompt_v3(prompt, image_url)
                else:
                    # Text-to-video with optimization
                    result = await optimize_prompt_v3(prompt)

                if result and "optimized_prompt" in result:
                    optimized_prompt = result["optimized_prompt"]
                    logger.info(f"✅ Prompt optimized: {optimized_prompt[:100]}...")
                else:
                    logger.warning("⚠️ Prompt optimization failed")

            except Exception as e:
                logger.error(f"❌ Prompt optimization error: {e}")

        # Use optimized prompt if available, otherwise translated or original
        final_prompt = optimized_prompt or translated_prompt or original_prompt

        # Create task
        task_id = str(uuid.uuid4())
        task = {
            "id": task_id,
            "status": "processing",
            "original_prompt": original_prompt,
            "translated_prompt": translated_prompt,
            "optimized_prompt": optimized_prompt,
            "final_prompt": final_prompt,
            "model": model,
            "image_url": image_url,
            "add_audio": add_audio,
            "upscale_1080p": upscale_1080p,
            "created_at": datetime.now().isoformat(),
            "client_ip": client_ip,
            "fingerprint": fingerprint,
            "user_agent": user_agent
        }

        tasks[task_id] = task
        logger.info(f"📋 Task created: {task_id}")

        # Start background processing
        background_tasks.add_task(process_video_generation, task_id)

        # Increment usage counter
        increment_usage_advanced(fingerprint)

        return {
            "task_id": task_id,
            "status": "processing",
            "message": "Video generation started",
            "remaining_today": remaining - 1  # Already used one
        }

    except Exception as e:
        logger.error(f"❌ Error in generate_video: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/status/{task_id}", tags=["Video Generation"])
async def get_task_status(task_id: str):
    """
    Get the status of a video generation task
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = tasks[task_id]

    # If completed, return final result
    if task["status"] == "completed":
        return {
            "status": "completed",
            "video_url": task["video_url"],
            "prompt_used": task["optimized_prompt"] or task["translated_prompt"] or task["original_prompt"],
            "model": task["model"],
            "was_optimized": bool(task.get("optimized_prompt"))
        }
    elif task["status"] == "failed":
        return {
            "status": "failed",
            "error": task["error"]
        }
    else:
        # Still processing
        return {
            "status": "processing",
            "message": "Video is being generated...",
            "progress": "Processing with AI model"
        }

@app.get("/videos/{filename}", tags=["Static Files"])
async def get_video(filename: str):
    """Serve generated video files"""
    video_path = Path(Config.VOLUME_PATH) / filename
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")

    return FileResponse(
        path=video_path,
        media_type="video/mp4",
        filename=filename
    )

@app.get("/images/{filename}", tags=["Static Files"])
async def get_image(filename: str):
    """Serve uploaded image files"""
    image_path = Path(Config.VOLUME_PATH) / filename
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(
        path=image_path,
        media_type="image/jpeg",
        filename=filename
    )

@app.get("/usage", tags=["Monitoring"])
async def get_usage_stats():
    """Get usage statistics"""
    usage_data = load_usage_data()
    today = date.today().isoformat()

    today_usage = usage_data.get("daily_usage", {}).get(today, {})
    total_today = sum(today_usage.values())

    return {
        "total_videos_today": total_today,
        "remaining_limit": max(0, 5 - total_today),  # 5 videos per day limit
        "daily_usage": today_usage,
        "suspicious_users": len(usage_data.get("suspicious_users", {})),
        "timestamp": datetime.now().isoformat()
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
