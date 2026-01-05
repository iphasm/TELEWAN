#!/usr/bin/env python3
"""
Script para verificar el estado del despliegue de TELEWAN
Ejecutar para diagnosticar problemas post-deploy
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def check_railway_status():
    """Verificar estado general del despliegue"""
    print("🚂 Verificando estado de Railway...")

    # Verificar variables de entorno críticas
    required_vars = ['TELEGRAM_BOT_TOKEN', 'USE_WEBHOOK', 'WEBHOOK_URL']
    missing_vars = []

    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            # Mostrar preview para seguridad
            if 'TOKEN' in var and len(value) > 10:
                print(f"✅ {var}: {value[:10]}...{value[-5:]}")
            else:
                print(f"✅ {var}: {value}")

    if missing_vars:
        print(f"❌ Variables faltantes: {', '.join(missing_vars)}")
        return False

    print("✅ Todas las variables críticas están configuradas")
    return True

def check_webhook_status():
    """Verificar estado del webhook en Telegram"""
    print("\n🔗 Verificando estado del webhook en Telegram...")

    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ No hay token del bot configurado")
        return False

    try:
        # Verificar webhook actual
        get_webhook_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
        response = requests.get(get_webhook_url, timeout=10)
        result = response.json()

        if result.get("ok"):
            webhook_info = result.get("result", {})
            url = webhook_info.get("url", "")

            if url:
                print(f"✅ Webhook activo: {url}")
                print(f"📬 Pendientes: {webhook_info.get('pending_update_count', 0)}")
                print(f"⏰ Último: {webhook_info.get('last_synchronization_error_date', 'Nunca')}")
                return True
            else:
                print("❌ No hay webhook configurado")
                return False
        else:
            print(f"❌ Error consultando webhook: {result.get('description')}")
            return False

    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def check_health_endpoint():
    """Verificar endpoint de healthcheck"""
    print("\n🏥 Verificando endpoint de healthcheck...")

    webhook_url = os.getenv('WEBHOOK_URL')
    if not webhook_url:
        print("❌ WEBHOOK_URL no configurada")
        return False

    # Asegurar HTTPS
    if not webhook_url.startswith('http'):
        webhook_url = f"https://{webhook_url}"

    try:
        response = requests.get(webhook_url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            print("✅ Healthcheck exitoso:"            print(f"   Status: {data.get('status')}")
            print(f"   Service: {data.get('service')}")
            print(f"   Timestamp: {data.get('timestamp')}")
            return True
        else:
            print(f"❌ Healthcheck falló - Status: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Error conectando al healthcheck: {e}")
        return False
    except ValueError:
        print(f"❌ Respuesta no válida del healthcheck: {response.text}")
        return False

def test_bot_functionality():
    """Hacer una prueba básica del bot"""
    print("\n🤖 Probando funcionalidad básica del bot...")

    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ No hay token del bot")
        return False

    try:
        # Probar getMe
        me_url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(me_url, timeout=10)
        result = response.json()

        if result.get("ok"):
            bot_info = result.get("result", {})
            print(f"✅ Bot conectado: @{bot_info.get('username', 'Unknown')}")
            print(f"   Nombre: {bot_info.get('first_name', 'Unknown')}")
            return True
        else:
            print(f"❌ Error con el bot: {result.get('description')}")
            return False

    except Exception as e:
        print(f"❌ Error probando el bot: {e}")
        return False

def main():
    print("🔍 Diagnóstico Completo de TELEWAN")
    print("=" * 50)

    all_good = True

    # Verificaciones paso a paso
    checks = [
        ("Configuración de Railway", check_railway_status),
        ("Estado del Webhook", check_webhook_status),
        ("Endpoint de Healthcheck", check_health_endpoint),
        ("Funcionalidad del Bot", test_bot_functionality)
    ]

    for check_name, check_func in checks:
        print(f"\n🔍 {check_name}:")
        print("-" * (len(check_name) + 3))
        if not check_func():
            all_good = False

    print("\n" + "=" * 50)
    if all_good:
        print("🎉 ¡Todo está funcionando correctamente!")
        print("✅ El bot está listo para recibir mensajes")
    else:
        print("⚠️  Hay problemas que necesitan atención")
        print("💡 Revisa los errores arriba y solucionalos")

    print("\n📋 Comandos útiles:")
    print("  railway logs --follow          # Ver logs en tiempo real")
    print("  railway run python check_deployment.py  # Re-ejecutar este diagnóstico")
    print("  railway deploy                  # Redeploy si hiciste cambios")

if __name__ == "__main__":
    main()





