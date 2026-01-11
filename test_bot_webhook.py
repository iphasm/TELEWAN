#!/usr/bin/env python3
"""
Script para probar si el bot recibe actualizaciones via webhook
Ejecutar en Railway para verificar funcionalidad del webhook
"""

import os
import sys
import requests
import json
import time
from datetime import datetime

def test_webhook_functionality():
    """Probar funcionalidad del webhook del bot"""
    print("🧪 PRUEBA DE FUNCIONALIDAD DEL WEBHOOK")
    print("="*50)

    # Verificar variables críticas
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    webhook_url = os.getenv('WEBHOOK_URL')

    if not token:
        print("❌ TELEGRAM_BOT_TOKEN no configurada")
        return False

    if not webhook_url:
        print("❌ WEBHOOK_URL no configurada")
        return False

    if not webhook_url.startswith('http'):
        webhook_url = f"https://{webhook_url}"

    print(f"🤖 Bot Token: {token[:10]}***")
    print(f"🔗 Webhook URL: {webhook_url}")
    print()

    # Paso 1: Verificar que el bot esté registrado correctamente en Telegram
    print("1️⃣ VERIFICANDO REGISTRO DEL BOT EN TELEGRAM:")
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                webhook_info = data.get('result', {})
                current_url = webhook_info.get('url', '')
                pending = webhook_info.get('pending_update_count', 0)

                print(f"   ✅ Webhook configurado: {current_url}")
                print(f"   📊 Updates pendientes: {pending}")

                if current_url != f"{webhook_url}/webhook":
                    print("   ⚠️  La URL del webhook no coincide con la configurada")
                    print(f"   📝 Actual: {current_url}")
                    print(f"   🎯 Esperado: {webhook_url}/webhook")
                    return False
            else:
                print(f"   ❌ Error: {data.get('description')}")
                return False
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

    print()

    # Paso 2: Verificar que la aplicación esté respondiendo
    print("2️⃣ VERIFICANDO QUE LA APLICACIÓN RESPONDA:")
    try:
        health_url = f"{webhook_url}/health"
        response = requests.get(health_url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            status = data.get('status')
            components = data.get('components', {})
            telegram_status = components.get('telegram_bot')

            print(f"   ✅ Health check: {status}")
            print(f"   🤖 Bot status: {telegram_status}")

            if status == 'healthy' and telegram_status == 'operational':
                print("   ✅ Aplicación y bot operativos")
            else:
                print("   ❌ Aplicación o bot con problemas")
                return False
        else:
            print(f"   ❌ Health check falló: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error conectando a la aplicación: {e}")
        return False

    print()

    # Paso 3: Probar envío de actualización manual (simular Telegram)
    print("3️⃣ PROBANDO ENVÍO DE ACTUALIZACIÓN MANUAL:")
    print("   ℹ️  Esto simula lo que Telegram envía cuando recibe un mensaje")

    # Crear una actualización de prueba (mensaje de texto)
    test_update = {
        "update_id": 123456789,
        "message": {
            "message_id": 123,
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

    webhook_endpoint = f"{webhook_url}/webhook"

    try:
        print(f"   📤 Enviando actualización de prueba a: {webhook_endpoint}")
        print(f"   📝 Contenido: {json.dumps(test_update, indent=2)[:200]}...")

        response = requests.post(
            webhook_endpoint,
            json=test_update,
            headers={"Content-Type": "application/json"},
            timeout=15
        )

        print(f"   📥 Respuesta HTTP: {response.status_code}")

        if response.status_code == 200:
            try:
                response_data = response.json()
                print(f"   ✅ Respuesta del webhook: {response_data}")

                if response_data.get('status') == 'accepted':
                    print("   ✅ Webhook aceptó la actualización correctamente")
                    print("   🎉 ¡El bot debería haber procesado el mensaje!")
                    print()
                    print("📋 PRÓXIMOS PASOS:")
                    print("   1. Revisa los logs de Railway para ver si se procesó el mensaje")
                    print("   2. Envía un mensaje real al bot desde Telegram")
                    print("   3. Si no responde, el problema está en el procesamiento de mensajes")
                    return True
                else:
                    print("   ⚠️  Webhook respondió pero con status inesperado")
                    return False
            except:
                print(f"   📄 Respuesta raw: {response.text[:200]}")
                print("   ⚠️  Respuesta no es JSON válido")
                return False
        else:
            print(f"   ❌ Webhook rechazó la petición: HTTP {response.status_code}")
            print(f"   📄 Respuesta: {response.text[:200]}")
            return False

    except requests.exceptions.Timeout:
        print("   ❌ Timeout - El webhook tardó demasiado en responder")
        print("   💡 Posible problema de procesamiento en la aplicación")
        return False
    except Exception as e:
        print(f"   ❌ Error enviando actualización: {e}")
        return False

def test_real_bot_interaction():
    """Intentar interactuar con el bot de manera real"""
    print("\n4️⃣ PRUEBA DE INTERACCIÓN REAL CON EL BOT:")
    print("   ℹ️  Para probar completamente, necesitas:")
    print("   • El chat ID de un usuario que pueda interactuar con el bot")
    print("   • O enviar un mensaje real desde Telegram y verificar logs")
    print()
    print("   💡 PASOS PARA DIAGNOSTICAR:")
    print("   1. Envía /start al bot desde Telegram")
    print("   2. Revisa inmediatamente los logs de Railway")
    print("   3. Busca mensajes como '📨 Webhook recibido' o '🔄 Procesando update'")
    print("   4. Si no ves estos mensajes, el webhook no está funcionando")
    print("   5. Si los ves pero no hay respuesta, el problema está en el procesamiento")

def main():
    print("🚀 TEST DE FUNCIONALIDAD DEL WEBHOOK DEL BOT")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python: {sys.version.split()[0]}")
    print()

    success = test_webhook_functionality()

    if success:
        print("\n✅ WEBHOOK FUNCIONANDO CORRECTAMENTE")
        test_real_bot_interaction()
        return 0
    else:
        print("\n❌ PROBLEMAS ENCONTRADOS EN EL WEBHOOK")
        print("\n🔧 POSIBLES SOLUCIONES:")
        print("   1. Verificar que WEBHOOK_URL esté correcta en Railway")
        print("   2. Verificar que la aplicación esté ejecutándose")
        print("   3. Revisar logs de Railway para errores")
        print("   4. Verificar configuración del webhook en Telegram")
        return 1

if __name__ == "__main__":
    sys.exit(main())