#!/usr/bin/env python3
"""
Servidor web para TELEWAN Bot
Maneja healthcheck y webhooks de Telegram
Usar con: gunicorn app:app o python app.py
"""

import os
import logging
import asyncio
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Crear aplicación Flask
app = Flask(__name__)

# Variables de configuración
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
WEBHOOK_PATH = os.getenv('WEBHOOK_PATH', '/webhook')

# Bot de Telegram (cargado de forma lazy)
telegram_app = None

def get_telegram_app():
    """Obtener la aplicación de Telegram de forma lazy"""
    global telegram_app
    if telegram_app is None:
        try:
            from telegram.ext import Application, CommandHandler, MessageHandler, filters
            from bot import start, help_command, handle_photo

            telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
            telegram_app.add_handler(CommandHandler("start", start))
            telegram_app.add_handler(CommandHandler("help", help_command))
            telegram_app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
            logger.info("Aplicación de Telegram inicializada")
        except Exception as e:
            logger.error(f"Error inicializando Telegram app: {e}")
    return telegram_app

@app.route('/', methods=['GET'])
def healthcheck():
    """Endpoint de healthcheck para Railway"""
    logger.info("Healthcheck endpoint called")
    return jsonify({
        "status": "healthy",
        "service": "TELEWAN Bot",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }), 200

@app.route('/health', methods=['GET'])
def health():
    """Endpoint de health alternativo"""
    return jsonify({"status": "ok"}), 200

@app.route('/test', methods=['GET'])
def test():
    """Endpoint de prueba"""
    return jsonify({
        "message": "TELEWAN Bot is running",
        "bot_token_configured": bool(TELEGRAM_BOT_TOKEN),
        "webhook_path": WEBHOOK_PATH
    }), 200

@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    """Endpoint para webhooks de Telegram"""
    try:
        # Verificar secret token si está configurado
        secret_token = os.getenv('WEBHOOK_SECRET_TOKEN')
        if secret_token:
            received_token = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
            if received_token != secret_token:
                logger.warning("Invalid secret token received")
                return jsonify({"error": "Unauthorized"}), 401

        # Obtener datos del update
        update_data = request.get_json()

        if update_data:
            logger.info(f"Webhook received update: {update_data.get('update_id', 'unknown')}")

            # Procesar el update
            tg_app = get_telegram_app()
            if tg_app:
                try:
                    from telegram import Update
                    update = Update.de_json(update_data, tg_app.bot)

                    # Procesar de forma asíncrona
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(tg_app.process_update(update))
                    loop.close()

                    return jsonify({"status": "ok"}), 200
                except Exception as e:
                    logger.error(f"Error processing update: {e}")
                    return jsonify({"error": str(e)}), 500
            else:
                logger.error("Telegram app not initialized")
                return jsonify({"error": "Bot not initialized"}), 500
        else:
            return jsonify({"error": "No update data"}), 400

    except Exception as e:
        logger.error(f"Error in webhook handler: {e}")
        return jsonify({"error": "Internal server error"}), 500

def setup_webhook():
    """Configurar webhook en Telegram"""
    import requests

    webhook_url = os.getenv('WEBHOOK_URL')
    if not webhook_url:
        logger.warning("WEBHOOK_URL not configured")
        return False

    if not webhook_url.startswith('http'):
        webhook_url = f"https://{webhook_url}"

    full_url = f"{webhook_url}{WEBHOOK_PATH}"

    try:
        api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
        payload = {"url": full_url}

        secret_token = os.getenv('WEBHOOK_SECRET_TOKEN')
        if secret_token:
            payload["secret_token"] = secret_token

        response = requests.post(api_url, json=payload, timeout=10)
        result = response.json()

        if result.get("ok"):
            logger.info(f"✅ Webhook configurado: {full_url}")
            return True
        else:
            logger.error(f"❌ Error configurando webhook: {result}")
            return False

    except Exception as e:
        logger.error(f"Error configurando webhook: {e}")
        return False

# Configurar webhook al iniciar (solo si USE_WEBHOOK está habilitado)
if os.getenv('USE_WEBHOOK', 'false').lower() == 'true':
    setup_webhook()

if __name__ == "__main__":
    # Obtener puerto de Railway o usar 8443 por defecto
    port = int(os.getenv('PORT', os.getenv('WEBHOOK_PORT', '8443')))
    logger.info(f"🚀 Iniciando servidor en puerto {port}")

    # Ejecutar con Flask development server (para testing)
    app.run(host="0.0.0.0", port=port, debug=False)
