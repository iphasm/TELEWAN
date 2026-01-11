#!/usr/bin/env python3
"""
Diagnóstico específico para problemas de webhook en Railway
Ejecutar en Railway para identificar el problema exacto
"""

import os
import requests
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def diagnose_webhook_issues():
    """Diagnóstico específico de problemas de webhook"""
    print("🔍 DIAGNÓSTICO DE PROBLEMAS DE WEBHOOK")
    print("="*50)

    # 1. Verificar variables críticas
    print("\n1. 📋 VERIFICACIÓN DE VARIABLES:")
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    webhook_url = os.getenv('WEBHOOK_URL')
    port = os.getenv('PORT', '8080')

    if token:
        print(f"   ✅ TELEGRAM_BOT_TOKEN: {token[:10]}***")
    else:
        print("   ❌ TELEGRAM_BOT_TOKEN: No configurada")
        return False

    if webhook_url:
        print(f"   ✅ WEBHOOK_URL: {webhook_url}")
    else:
        print("   ❌ WEBHOOK_URL: No configurada")
        print("   💡 POSIBLE SOLUCIÓN: Configurar en Railway Dashboard")
        print("      Railway URL típica: https://[project-name].up.railway.app")
        return False

    print(f"   ✅ PORT: {port}")

    # 2. Verificar conectividad con Telegram
    print("\n2. 📡 CONECTIVIDAD CON TELEGRAM:")
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

    # 3. Verificar configuración actual del webhook
    print("\n3. 🔗 CONFIGURACIÓN ACTUAL DEL WEBHOOK:")
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

                if current_url:
                    print("   ✅ Webhook configurado")
                    if pending > 0:
                        print(f"   ⚠️  HAY {pending} MENSAJES PENDIENTES - EL BOT NO ESTÁ PROCESANDO")
                else:
                    print("   ❌ NO HAY WEBHOOK CONFIGURADO - EL BOT NO PUEDE RECIBIR MENSAJES")
            else:
                print(f"   ❌ Error obteniendo webhook info: {data.get('description')}")
        else:
            print(f"   ❌ Error HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error verificando webhook: {e}")

    # 4. Verificar que el endpoint del webhook responda
    print("\n4. 🌐 VERIFICACIÓN DEL ENDPOINT:")
    if not webhook_url.startswith('http'):
        webhook_url = f"https://{webhook_url}"

    webhook_endpoint = f"{webhook_url}/webhook"
    health_endpoint = f"{webhook_url}/health"

    # Probar health endpoint
    try:
        print(f"   Probando health endpoint: {health_endpoint}")
        response = requests.get(health_endpoint, timeout=10)

        if response.status_code == 200:
            data = response.json()
            status = data.get('status', 'unknown')
            components = data.get('components', {})
            telegram_status = components.get('telegram_bot', 'unknown')

            print(f"   ✅ Health check: {status}")
            print(f"   🤖 Bot status: {telegram_status}")

            if status == 'healthy' and telegram_status == 'operational':
                print("   ✅ SERVIDOR Y BOT OPERATIVOS")
            else:
                print("   ❌ PROBLEMA EN LA INICIALIZACIÓN DEL BOT")
                return False
        else:
            print(f"   ❌ Health check falló: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error accediendo al endpoint: {e}")
        return False

    # 5. Intentar configurar el webhook manualmente
    print("\n5. 🔧 INTENTO DE CONFIGURACIÓN MANUAL:")
    try:
        set_webhook_url = f"https://api.telegram.org/bot{token}/setWebhook"
        payload = {"url": webhook_endpoint}

        secret_token = os.getenv('WEBHOOK_SECRET_TOKEN')
        if secret_token:
            payload["secret_token"] = secret_token
            print(f"   Usando secret token: {secret_token[:10]}***")

        print(f"   Configurando webhook: {webhook_endpoint}")
        response = requests.post(set_webhook_url, json=payload, timeout=15)

        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                print("   ✅ Webhook configurado exitosamente")
                print(f"   📝 Respuesta: {data.get('description', 'OK')}")
            else:
                print(f"   ❌ Error configurando webhook: {data.get('description', 'Unknown')}")
                return False
        else:
            print(f"   ❌ Error HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error en configuración: {e}")
        return False

    # 6. Verificación final
    print("\n6. 🎯 VERIFICACIÓN FINAL:")
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                webhook_info = data.get('result', {})
                final_url = webhook_info.get('url', '')
                final_pending = webhook_info.get('pending_update_count', 0)

                if final_url == webhook_endpoint:
                    print("   ✅ WEBHOOK CONFIGURADO CORRECTAMENTE")
                    if final_pending == 0:
                        print("   ✅ SIN MENSAJES PENDIENTES")
                        return True
                    else:
                        print(f"   ⚠️  AÚN HAY {final_pending} MENSAJES PENDIENTES")
                        print("   💡 El bot debería empezar a procesar mensajes pronto")
                        return True
                else:
                    print(f"   ❌ URL del webhook no coincide: {final_url}")
                    return False
    except Exception as e:
        print(f"   ❌ Error en verificación final: {e}")
        return False

def main():
    print("🚀 DIAGNÓSTICO DE WEBHOOK PARA TELEWAN BOT")
    print(f"⏰ {os.popen('date').read().strip()}")
    print(f"🐍 Python: {sys.version.split()[0]}")
    print(f"📍 Directorio: {os.getcwd()}")
    print()

    success = diagnose_webhook_issues()

    print("\n" + "="*50)
    if success:
        print("✅ DIAGNÓSTICO COMPLETADO - WEBHOOK FUNCIONANDO")
        print("🎉 El bot debería responder a comandos ahora")
        return 0
    else:
        print("❌ DIAGNÓSTICO COMPLETADO - PROBLEMAS ENCONTRADOS")
        print("\n🔧 POSIBLES SOLUCIONES:")
        print("   1. Verificar que WEBHOOK_URL esté correcta en Railway")
        print("   2. Revisar logs de Railway para errores de inicialización")
        print("   3. Verificar que el puerto PORT sea correcto")
        print("   4. Comprobar que el dominio esté accesible desde internet")
        print("   5. Revisar configuración de firewall en Railway")
        return 1

if __name__ == "__main__":
    sys.exit(main())