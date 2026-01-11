#!/usr/bin/env python3
"""
Diagnóstico EN VIVO del bot de Telegram en Railway
Ejecutar este script en Railway para ver el estado actual del bot
"""

import os
import sys
import requests
import json
import time
import asyncio
from datetime import datetime

def check_railway_environment():
    """Verificar que estamos en Railway y tenemos las variables correctas"""
    print("🌐 VERIFICANDO ENTORNO RAILWAY")
    print("="*40)

    required_vars = ['TELEGRAM_BOT_TOKEN', 'WEBHOOK_URL', 'USE_WEBHOOK']
    missing = []

    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var == 'TELEGRAM_BOT_TOKEN':
                print(f"✅ {var}: {value[:10]}***")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NO CONFIGURADA")
            missing.append(var)

    if missing:
        print(f"\n❌ VARIABLES FALTANTES: {', '.join(missing)}")
        print("💡 Configurar en Railway Dashboard > Variables")
        return False

    print("✅ Todas las variables requeridas están configuradas")
    return True

def check_application_health():
    """Verificar que la aplicación esté ejecutándose correctamente"""
    print("\n🏥 VERIFICANDO SALUD DE LA APLICACIÓN")
    print("="*40)

    webhook_url = os.getenv('WEBHOOK_URL')
    if not webhook_url.startswith('http'):
        webhook_url = f"https://{webhook_url}"

    health_url = f"{webhook_url}/health"

    try:
        print(f"🔍 Probando endpoint: {health_url}")
        response = requests.get(health_url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            print("✅ Aplicación responde correctamente")

            # Verificar componentes
            components = data.get('components', {})
            telegram_bot = components.get('telegram_bot', 'unknown')

            print(f"🤖 Estado del bot: {telegram_bot}")

            if telegram_bot == 'operational':
                print("✅ Bot operativo en la aplicación")
                return True
            else:
                print(f"❌ Bot no operativo: {telegram_bot}")
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error conectando: {e}")
        return False

def check_telegram_webhook():
    """Verificar configuración del webhook en Telegram"""
    print("\n📡 VERIFICANDO WEBHOOK EN TELEGRAM")
    print("="*40)

    token = os.getenv('TELEGRAM_BOT_TOKEN')
    webhook_url = os.getenv('WEBHOOK_URL')

    if not webhook_url.startswith('http'):
        webhook_url = f"https://{webhook_url}"

    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo", timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                webhook_info = data.get('result', {})
                current_url = webhook_info.get('url', '')
                pending = webhook_info.get('pending_update_count', 0)

                print(f"🔗 URL configurada en Telegram: {current_url}")
                print(f"📨 Updates pendientes: {pending}")

                expected_url = f"{webhook_url}/webhook"
                if current_url == expected_url:
                    print("✅ Webhook URL correcta")
                else:
                    print("❌ Webhook URL incorrecta")
                    print(f"   Esperada: {expected_url}")
                    print(f"   Actual: {current_url}")
                    return False

                if pending > 0:
                    print(f"⚠️  HAY {pending} MENSAJES PENDIENTES")
                    print("   El bot no está procesando actualizaciones")
                    return False

                print("✅ Webhook configurado correctamente")
                return True
            else:
                print(f"❌ Error de Telegram: {data.get('description')}")
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error conectando a Telegram: {e}")
        return False

def test_webhook_endpoint():
    """Probar el endpoint del webhook directamente"""
    print("\n🔗 PROBANDO ENDPOINT DEL WEBHOOK")
    print("="*40)

    webhook_url = os.getenv('WEBHOOK_URL')
    if not webhook_url.startswith('http'):
        webhook_url = f"https://{webhook_url}"

    webhook_endpoint = f"{webhook_url}/webhook"

    # Crear una actualización de prueba
    test_update = {
        "update_id": int(time.time()),  # Unique ID
        "message": {
            "message_id": 999,
            "from": {
                "id": 123456789,
                "is_bot": False,
                "first_name": "Test",
                "username": "test_user"
            },
            "chat": {
                "id": 123456789,
                "type": "private"
            },
            "date": int(time.time()),
            "text": "/start"
        }
    }

    try:
        print(f"📤 Enviando actualización de prueba a: {webhook_endpoint}")
        response = requests.post(
            webhook_endpoint,
            json=test_update,
            headers={"Content-Type": "application/json"},
            timeout=15
        )

        print(f"📥 Respuesta HTTP: {response.status_code}")

        if response.status_code == 200:
            try:
                response_data = response.json()
                print(f"✅ Respuesta del webhook: {json.dumps(response_data, indent=2)}")

                if response_data.get('status') == 'accepted':
                    print("✅ Webhook aceptó la actualización")
                    return True
                else:
                    print("⚠️  Webhook respondió pero con status inesperado")
                    return False
            except:
                print(f"📄 Respuesta raw: {response.text}")
                return False
        else:
            print(f"❌ Webhook rechazó la petición: HTTP {response.status_code}")
            print(f"📄 Respuesta: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("❌ Timeout - El webhook tardó demasiado en responder")
        return False
    except Exception as e:
        print(f"❌ Error enviando actualización: {e}")
        return False

def check_logs_recommendations():
    """Dar recomendaciones para revisar logs"""
    print("\n📋 RECOMENDACIONES PARA REVISAR LOGS")
    print("="*40)

    print("🔍 Para diagnosticar completamente:")
    print("1. Ve a Railway Dashboard > Tu proyecto > Logs")
    print("2. Envía un mensaje al bot (/start)")
    print("3. Busca inmediatamente en los logs:")
    print("   • '🔗 Webhook request received'")
    print("   • '📨 Webhook recibido: update_id=...'")
    print("   • '🔄 Procesando update ...'")
    print("   • '✅ Update ... procesado correctamente'")
    print("   • '🚀 START COMMAND RECEIVED'")
    print()
    print("❌ Si NO ves '🔗 Webhook request received':")
    print("   → El webhook no está llegando a la aplicación")
    print("   → Verificar WEBHOOK_URL en Railway")
    print()
    print("❌ Si ves el webhook pero NO 'procesado correctamente':")
    print("   → Error en el procesamiento del mensaje")
    print("   → Revisar logs para errores específicos")
    print()
    print("❌ Si ves procesamiento pero el bot NO responde:")
    print("   → Error en el envío de respuestas")
    print("   → Revisar permisos del bot o errores de red")

def main():
    print("🔍 DIAGNÓSTICO EN VIVO DEL BOT DE TELEGRAM")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python: {sys.version.split()[0]}")
    print()

    # Verificar entorno
    if not check_railway_environment():
        print("\n❌ CONFIGURACIÓN INCOMPLETA")
        return 1

    # Verificar aplicación
    if not check_application_health():
        print("\n❌ APLICACIÓN CON PROBLEMAS")
        return 1

    # Verificar webhook en Telegram
    if not check_telegram_webhook():
        print("\n❌ WEBHOOK MAL CONFIGURADO EN TELEGRAM")
        return 1

    # Probar endpoint del webhook
    if not test_webhook_endpoint():
        print("\n❌ ENDPOINT DEL WEBHOOK CON PROBLEMAS")
        return 1

    print("\n🎉 DIAGNÓSTICO COMPLETADO - TODO PARECE CORRECTO")
    print("🤔 Si el bot aún no responde:")
    print("   1. Revisa los logs de Railway después de enviar un mensaje")
    print("   2. Busca los mensajes de log mencionados arriba")
    print("   3. Comparte los logs específicos para diagnóstico avanzado")

    check_logs_recommendations()
    return 0

if __name__ == "__main__":
    sys.exit(main())