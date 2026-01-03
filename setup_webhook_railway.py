#!/usr/bin/env python3
"""
Script para configurar webhooks directamente en Railway
Ejecutar con: railway run python setup_webhook_railway.py
"""

import os
import requests
import json

def get_railway_url():
    """Obtener la URL del proyecto Railway"""
    # Intentar obtener desde variables de entorno
    railway_url = os.getenv('RAILWAY_STATIC_URL') or os.getenv('RAILWAY_PROJECT_DOMAIN')

    if railway_url:
        # Si ya incluye https, usar directamente
        if railway_url.startswith('https://'):
            return railway_url
        else:
            return f"https://{railway_url}"

    # Si no está disponible, pedir al usuario
    print("🔗 No se pudo detectar automáticamente la URL de Railway")
    url = input("Ingresa la URL completa de tu proyecto Railway (ej: https://telewan-production.up.railway.app): ").strip()
    return url

def setup_webhook():
    """Configurar webhook completo"""

    print("🚀 Configuración automática de Webhooks para TELEWAN")
    print("=" * 55)

    # Obtener token del bot
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN no encontrado")
        print("💡 Asegúrate de configurar la variable en Railway")
        return False

    # Obtener URL de Railway
    railway_url = get_railway_url()
    if not railway_url:
        print("❌ No se pudo obtener la URL de Railway")
        return False

    webhook_url = f"{railway_url}/webhook"
    print(f"📡 Webhook URL: {webhook_url}")

    # Configurar webhook en Telegram
    telegram_api_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    payload = {
        "url": webhook_url,
        "drop_pending_updates": True
    }

    # Agregar secret token si existe
    secret_token = os.getenv('WEBHOOK_SECRET_TOKEN')
    if secret_token:
        payload["secret_token"] = secret_token
        print("🔐 Usando token secreto")

    print("🔗 Configurando webhook en Telegram...")
    try:
        response = requests.post(telegram_api_url, json=payload, timeout=30)
        result = response.json()

        if result.get("ok"):
            print("✅ Webhook configurado exitosamente")
            print(f"📍 URL: {webhook_url}")
            print(f"🤖 Bot: {bot_token[:10]}...{bot_token[-5:]}")
            return True
        else:
            print(f"❌ Error: {result.get('description')}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False

def verify_setup():
    """Verificar que la configuración es correcta"""

    print("\n📊 Verificando configuración...")

    # Verificar variables
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    use_webhook = os.getenv('USE_WEBHOOK', 'false').lower() == 'true'

    print(f"🤖 Token del bot: {'✅' if bot_token else '❌'}")
    print(f"🔗 Modo webhook: {'✅' if use_webhook else '❌'}")

    if not bot_token or not use_webhook:
        print("⚠️  Variables faltantes. Configura:")
        if not bot_token:
            print("  - TELEGRAM_BOT_TOKEN")
        if not use_webhook:
            print("  - USE_WEBHOOK=true")
        return False

    # Verificar webhook
    telegram_api_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"

    try:
        response = requests.get(telegram_api_url, timeout=10)
        result = response.json()

        if result.get("ok"):
            webhook_info = result.get("result", {})
            url = webhook_info.get("url", "")

            if url:
                print(f"✅ Webhook activo: {url}")
                print(f"📬 Pendientes: {webhook_info.get('pending_update_count', 0)}")
                return True
            else:
                print("❌ Webhook no configurado")
                return False
        else:
            print(f"❌ Error al verificar: {result.get('description')}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False

def main():
    print("🔧 Setup Automático de Webhooks - TELEWAN")
    print("=" * 45)

    # Verificar configuración actual
    if not verify_setup():
        print("\n🔧 Configurando webhook...")
        if setup_webhook():
            print("\n🎉 ¡Configuración completada!")
            verify_setup()
        else:
            print("\n❌ Falló la configuración")
            print("💡 Verifica que las variables de entorno estén correctas")
    else:
        print("\n✅ Webhook ya está configurado correctamente")

    print("\n📋 Para verificar manualmente:")
    print("  railway run python setup_webhook.py check")

if __name__ == "__main__":
    main()
