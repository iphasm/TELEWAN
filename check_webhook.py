#!/usr/bin/env python3
"""
Script para verificar el estado del webhook del bot de Telegram
"""

import os
import requests
import sys

def check_webhook_status():
    """Verificar el estado del webhook del bot"""
    print("🔍 VERIFICACIÓN DE WEBHOOK DE TELEGRAM")
    print("=" * 40)

    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN no configurado")
        return False

    try:
        # Obtener información del webhook
        response = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo", timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                webhook_info = data.get('result', {})

                print("📡 Información del Webhook:")
                webhook_url = webhook_info.get('url', '')
                if webhook_url:
                    print(f"   ✅ URL configurada: {webhook_url}")
                    print(f"   📊 Pending updates: {webhook_info.get('pending_update_count', 0)}")
                    print(f"   ⏰ Last error date: {webhook_info.get('last_error_date', 'None')}")
                    if webhook_info.get('last_error_message'):
                        print(f"   ❌ Last error: {webhook_info.get('last_error_message')}")

                    # Verificar si la URL es accesible
                    try:
                        health_response = requests.get(f"{webhook_url.replace('/webhook', '')}/health", timeout=5)
                        if health_response.status_code == 200:
                            print("   ✅ Webhook URL responde correctamente")
                        else:
                            print(f"   ❌ Webhook URL retorna status {health_response.status_code}")
                    except Exception as e:
                        print(f"   ❌ Error accediendo a webhook URL: {e}")

                    return True
                else:
                    print("   ❌ No hay webhook configurado")
                    print("   💡 El bot está en modo polling (no funcionará en Railway)")
                    return False
            else:
                print("❌ Error en respuesta de Telegram API")
                return False
        else:
            print(f"❌ Error HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error verificando webhook: {e}")
        return False

def main():
    success = check_webhook_status()

    if not success:
        print("\n🔧 POSIBLES SOLUCIONES:")
        print("1. Asegúrate de que WEBHOOK_URL esté configurada en Railway")
        print("2. Verifica que la URL sea accesible (https://tu-app.railway.app)")
        print("3. Reinicia la aplicación en Railway para que configure el webhook")
        print("4. Revisa los logs de Railway para errores de webhook")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)