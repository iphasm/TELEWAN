#!/usr/bin/env python3
"""
Script para configurar webhooks de Telegram
Ejecutar después de desplegar con webhooks habilitados
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def setup_webhook():
    """Configura el webhook en Telegram"""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    webhook_url = os.getenv("WEBHOOK_URL")
    webhook_path = os.getenv("WEBHOOK_PATH", "/webhook")

    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN no configurado")
        return False

    if not webhook_url:
        print("❌ WEBHOOK_URL no configurado")
        return False

    # URL completa del webhook
    full_webhook_url = f"{webhook_url}{webhook_path}"

    # URL de la API de Telegram
    telegram_api_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"

    payload = {
        "url": full_webhook_url,
        "drop_pending_updates": True
    }

    # Agregar secret token si está configurado
    secret_token = os.getenv("WEBHOOK_SECRET_TOKEN")
    if secret_token:
        payload["secret_token"] = secret_token

    print(f"🔗 Configurando webhook en: {full_webhook_url}")
    print(f"📡 API URL: {telegram_api_url}")

    try:
        response = requests.post(telegram_api_url, json=payload)
        result = response.json()

        if result.get("ok"):
            print("✅ Webhook configurado exitosamente")
            print(f"📝 Descripción: {result.get('description', 'OK')}")
            return True
        else:
            print(f"❌ Error configurando webhook: {result.get('description')}")
            return False

    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def check_webhook():
    """Verifica el estado actual del webhook"""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN no configurado")
        return

    telegram_api_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"

    try:
        response = requests.get(telegram_api_url)
        result = response.json()

        if result.get("ok"):
            webhook_info = result.get("result", {})
            url = webhook_info.get("url", "No configurado")

            print("📊 Estado del Webhook:")
            print(f"  URL: {url}")
            print(f"  Pendientes: {webhook_info.get('pending_update_count', 0)}")
            print(f"  Último error: {webhook_info.get('last_error_message', 'Ninguno')}")

            if url:
                print("✅ Webhook activo")
            else:
                print("⚠️  Webhook no configurado")
        else:
            print(f"❌ Error obteniendo info: {result.get('description')}")

    except Exception as e:
        print(f"❌ Error de conexión: {e}")

def remove_webhook():
    """Elimina el webhook actual"""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN no configurado")
        return False

    telegram_api_url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"

    try:
        response = requests.post(telegram_api_url)
        result = response.json()

        if result.get("ok"):
            print("✅ Webhook eliminado exitosamente")
            return True
        else:
            print(f"❌ Error eliminando webhook: {result.get('description')}")
            return False

    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def main():
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "setup":
            return setup_webhook()
        elif command == "check":
            check_webhook()
            return True
        elif command == "remove":
            return remove_webhook()
        else:
            print("❌ Comando desconocido. Use: setup, check, o remove")
            return False
    else:
        print("🔧 Configurador de Webhooks para TELEWAN")
        print("=" * 45)
        print("Comandos disponibles:")
        print("  setup  - Configurar webhook")
        print("  check  - Verificar estado del webhook")
        print("  remove - Eliminar webhook")
        print()
        print("Ejemplos:")
        print("  python setup_webhook.py setup")
        print("  python setup_webhook.py check")
        print("  python setup_webhook.py remove")
        return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)





