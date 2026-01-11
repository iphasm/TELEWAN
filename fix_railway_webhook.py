#!/usr/bin/env python3
"""
Script para corregir problemas de webhook en Railway
Ejecutar después de configurar las variables correctamente
"""

import os
import requests
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_railway_webhook():
    """Corregir configuración de webhook para Railway"""
    print("🔧 CORRECCIÓN DE WEBHOOK PARA RAILWAY")
    print("="*50)

    # Verificar que estamos en Railway
    railway_env = os.getenv('RAILWAY_ENVIRONMENT')
    railway_project_id = os.getenv('RAILWAY_PROJECT_ID')
    railway_static_url = os.getenv('RAILWAY_STATIC_URL')

    print("📋 VARIABLES DE RAILWAY:")
    print(f"   RAILWAY_ENVIRONMENT: {railway_env}")
    print(f"   RAILWAY_PROJECT_ID: {railway_project_id}")
    print(f"   RAILWAY_STATIC_URL: {railway_static_url}")

    if not railway_env and not railway_project_id:
        print("❌ No se detecta entorno Railway")
        print("💡 Este script debe ejecutarse en Railway")
        return False

    # Verificar variables críticas
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    webhook_url = os.getenv('WEBHOOK_URL')
    port = os.getenv('PORT', '8080')

    print("\n🔑 VARIABLES CRÍTICAS:")
    if token:
        print(f"   ✅ TELEGRAM_BOT_TOKEN: {token[:10]}***")
    else:
        print("   ❌ TELEGRAM_BOT_TOKEN no configurada")
        print("   💡 Configurar en Railway Dashboard > Variables")
        return False

    if webhook_url:
        print(f"   ✅ WEBHOOK_URL: {webhook_url}")
    else:
        print("   ❌ WEBHOOK_URL no configurada")
        print("   💡 Configurar en Railway Dashboard > Variables")
        print("   💡 Formato: https://tu-proyecto.up.railway.app")
        print(f"   💡 Puerto actual: {port}")
        return False

    # Verificar conectividad básica
    print("\n📡 VERIFICANDO CONECTIVIDAD:")
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_username = data['result'].get('username')
                print(f"   ✅ Bot conectado: @{bot_username}")
            else:
                print(f"   ❌ Token inválido: {data.get('description')}")
                return False
        else:
            print(f"   ❌ Error HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error conectando: {e}")
        return False

    # Verificar estado actual del webhook
    print("\n🔗 ESTADO ACTUAL DEL WEBHOOK:")
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                webhook_info = data.get('result', {})
                current_url = webhook_info.get('url', '')
                pending = webhook_info.get('pending_update_count', 0)

                print(f"   URL actual: {current_url or 'Ninguna'}")
                print(f"   Updates pendientes: {pending}")
            else:
                print(f"   ❌ Error obteniendo webhook info: {data.get('description')}")
                return False
    except Exception as e:
        print(f"   ❌ Error verificando webhook: {e}")
        return False

    # Verificar que la aplicación esté corriendo
    print("\n🌐 VERIFICANDO APLICACIÓN:")
    if not webhook_url.startswith('http'):
        webhook_url = f"https://{webhook_url}"

    health_url = f"{webhook_url}/health"
    try:
        print(f"   Probando: {health_url}")
        response = requests.get(health_url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            status = data.get('status')
            components = data.get('components', {})
            telegram_status = components.get('telegram_bot')

            print(f"   ✅ Health check: {status}")
            print(f"   🤖 Bot status: {telegram_status}")

            if status == 'healthy' and telegram_status == 'operational':
                print("   ✅ APLICACIÓN OPERATIVA")
            else:
                print("   ❌ APLICACIÓN CON PROBLEMAS")
                print("   💡 Revisar logs de Railway para errores de inicialización")
                return False
        else:
            print(f"   ❌ Health check falló: HTTP {response.status_code}")
            print("   💡 La aplicación no está respondiendo")
            return False
    except Exception as e:
        print(f"   ❌ Error accediendo a la aplicación: {e}")
        print("   💡 Verificar que la URL del webhook sea correcta")
        return False

    # Configurar webhook correctamente
    print("\n⚙️  CONFIGURANDO WEBHOOK:")
    webhook_endpoint = f"{webhook_url}/webhook"
    set_webhook_url = f"https://api.telegram.org/bot{token}/setWebhook"

    payload = {"url": webhook_endpoint}
    secret_token = os.getenv('WEBHOOK_SECRET_TOKEN')
    if secret_token:
        payload["secret_token"] = secret_token
        print(f"   Usando secret token: {secret_token[:10]}***")

    print(f"   Endpoint del webhook: {webhook_endpoint}")

    try:
        response = requests.post(set_webhook_url, json=payload, timeout=15)

        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                print("   ✅ WEBHOOK CONFIGURADO EXITOSAMENTE")
                print(f"   📝 Respuesta: {data.get('description', 'OK')}")
            else:
                print(f"   ❌ Error configurando webhook: {data.get('description')}")
                return False
        else:
            print(f"   ❌ Error HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error en configuración: {e}")
        return False

    # Verificación final
    print("\n🎯 VERIFICACIÓN FINAL:")
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                webhook_info = data.get('result', {})
                final_url = webhook_info.get('url', '')
                final_pending = webhook_info.get('pending_update_count', 0)

                if final_url == webhook_endpoint:
                    print("   ✅ WEBHOOK VERIFICADO Y FUNCIONANDO")
                    print(f"   📊 Mensajes pendientes: {final_pending}")

                    if final_pending > 0:
                        print("   ⏳ Procesando mensajes pendientes...")
                    else:
                        print("   🎉 ¡LISTO! El bot debería responder a comandos")

                    return True
                else:
                    print(f"   ❌ URL del webhook no coincide: {final_url}")
                    print(f"   ❌ Esperado: {webhook_endpoint}")
                    return False
    except Exception as e:
        print(f"   ❌ Error en verificación final: {e}")
        return False

def main():
    print("🚀 CORRECCIÓN DE WEBHOOK PARA TELEWAN BOT")
    print(f"⏰ Ejecutando en: {os.popen('date').read().strip() if os.name != 'nt' else 'Windows'}")
    print(f"🐍 Python: {sys.version.split()[0]}")
    print()

    success = fix_railway_webhook()

    print("\n" + "="*50)
    if success:
        print("✅ CORRECCIÓN COMPLETADA - BOT FUNCIONANDO")
        print("🎉 El bot de Telegram debería responder a comandos ahora")
        print("\n📝 PRUEBA:")
        print("   Envía /start al bot para verificar que funciona")
        return 0
    else:
        print("❌ CORRECCIÓN FALLIDA")
        print("\n🔧 VERIFICAR:")
        print("   1. Variables de entorno en Railway Dashboard")
        print("   2. Logs de Railway para errores")
        print("   3. Conectividad de red")
        print("   4. Configuración del dominio")
        return 1

if __name__ == "__main__":
    sys.exit(main())