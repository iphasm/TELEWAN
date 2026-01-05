#!/usr/bin/env python3
"""
Script para verificar el estado del webhook de Telegram
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'telewan-production.up.railway.app')

def check_webhook():
    """Verificar el webhook actual configurado en Telegram"""
    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN no configurado")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getWebhookInfo"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if data.get('ok'):
            webhook_info = data.get('result', {})
            print("📡 Estado del Webhook:")
            print(f"  URL: {webhook_info.get('url', 'No configurado')}")
            print(f"  Tiene certificado: {webhook_info.get('has_custom_certificate', False)}")
            print(f"  Máximo conexiones: {webhook_info.get('max_connections', 'N/A')}")
            print(f"  Allowed updates: {webhook_info.get('allowed_updates', 'Todas')}")
            print(f"  Pending updates: {webhook_info.get('pending_update_count', 0)}")
            print(f"  Último error: {webhook_info.get('last_error_message', 'Ninguno')}")
            print(f"  Fecha último error: {webhook_info.get('last_error_date', 'Ninguno')}")
        else:
            print(f"❌ Error de Telegram: {data.get('description', 'Unknown error')}")
    else:
        print(f"❌ Error HTTP: {response.status_code}")

def test_webhook_endpoint():
    """Probar el endpoint del webhook"""
    test_url = f"https://{WEBHOOK_URL}/webhook"
    print(f"\n🧪 Probando endpoint: {test_url}")

    # Crear un update de prueba (simulando un mensaje de texto)
    test_update = {
        "update_id": 999999,
        "message": {
            "message_id": 123,
            "from": {
                "id": 1265547936,
                "is_bot": False,
                "first_name": "Test User"
            },
            "chat": {
                "id": 1265547936,
                "type": "private"
            },
            "date": 1640995200,
            "text": "/start"
        }
    }

    response = requests.post(test_url, json=test_update, timeout=10)
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.text[:200]}...")

if __name__ == "__main__":
    print("🔍 Diagnóstico del Webhook de Telegram\n")
    check_webhook()
    test_webhook_endpoint()
