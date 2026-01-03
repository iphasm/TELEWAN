#!/usr/bin/env python3
"""
Servidor web para TELEWAN Bot
Maneja healthcheck y webhooks de Telegram
Usar con: gunicorn app:app o python app.py
"""

import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify

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

@app.route('/', methods=['GET'])
def healthcheck():
    """Endpoint de healthcheck para Railway"""
    return jsonify({
        "status": "healthy",
        "service": "TELEWAN Bot",
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/health', methods=['GET'])
def health():
    """Endpoint de health alternativo"""
    return jsonify({"status": "ok"}), 200

@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    """Endpoint para webhooks de Telegram"""
    try:
        update_data = request.get_json()
        if update_data:
            logger.info(f"Received update: {update_data.get('update_id', 'unknown')}")
            # Por ahora solo log, la lógica del bot se implementará después
            return jsonify({"status": "ok"}), 200
        return jsonify({"error": "No data"}), 400
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv('PORT', '8443'))
    logger.info(f"Starting on port {port}")
    app.run(host="0.0.0.0", port=port)
