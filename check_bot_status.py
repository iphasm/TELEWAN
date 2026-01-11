#!/usr/bin/env python3
"""
Script para verificar el estado del bot de Telegram en Railway
Ejecutar después del deploy para diagnosticar problemas
"""

import os
import requests
import sys

def check_bot_status():
    """Verificar estado completo del bot"""
    print("🤖 VERIFICACIÓN DE ESTADO DEL BOT")
    print("=" * 40)

    # Verificar si estamos en Railway
    is_railway = os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RAILWAY_PROJECT_ID')
    if is_railway:
        print("🚂 Ejecutándose en Railway")
    else:
        print("💻 Ejecutándose localmente")
        print("⚠️  Para diagnóstico completo, ejecuta en Railway")
    print()

    # Verificar variables críticas
    print("🔑 VARIABLES DE ENTORNO:")
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    api_key = os.getenv('WAVESPEED_API_KEY')
    webhook_url = os.getenv('WEBHOOK_URL')

    if token:
        masked_token = token[:10] + "***"
        print(f"   ✅ TELEGRAM_BOT_TOKEN: {masked_token}")
    else:
        print("   ❌ TELEGRAM_BOT_TOKEN: No configurada")
        return False

    if api_key:
        masked_key = api_key[:10] + "***"
        print(f"   ✅ WAVESPEED_API_KEY: {masked_key}")
    else:
        print("   ❌ WAVESPEED_API_KEY: No configurada")
        return False

    if webhook_url:
        print(f"   ✅ WEBHOOK_URL: {webhook_url}")
    else:
        print("   ⚠️  WEBHOOK_URL: No configurada (se intentará inferir)")
    print()

    # Probar conectividad con Telegram
    print("📡 CONECTIVIDAD CON TELEGRAM:")
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                username = bot_info.get('username', 'Unknown')
                print(f"   ✅ Bot conectado: @{username}")
                print(f"   🤖 Bot ID: {bot_info.get('id')}")
            else:
                print("   ❌ Token de bot inválido")
                return False
        else:
            print(f"   ❌ Error HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error conectando a Telegram: {e}")
        return False
    print()

    # Verificar configuración del webhook
    print("🔗 CONFIGURACIÓN DEL WEBHOOK:")
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                webhook_info = data.get('result', {})
                current_webhook = webhook_info.get('url', '')

                if current_webhook:
                    print(f"   ✅ Webhook configurado: {current_webhook}")
                    print(f"   📊 Updates pendientes: {webhook_info.get('pending_update_count', 0)}")

                    # Verificar si el webhook responde
                    try:
                        health_response = requests.get(f"{current_webhook.replace('/webhook', '')}/health", timeout=5)
                        if health_response.status_code == 200:
                            print("   ✅ Endpoint del webhook responde")
                        else:
                            print(f"   ❌ Endpoint retorna status {health_response.status_code}")
                    except Exception as e:
                        print(f"   ❌ Error accediendo al webhook: {e}")
                else:
                    print("   ❌ No hay webhook configurado en Telegram")
                    print("   💡 El bot no puede recibir mensajes")
            else:
                print("   ❌ Error obteniendo info del webhook")
        else:
            print(f"   ❌ Error HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error verificando webhook: {e}")
    print()

    # Verificar aplicación corriendo
    print("🌐 ESTADO DE LA APLICACIÓN:")
    if webhook_url:
        try:
            # Intentar acceder a la aplicación
            app_url = webhook_url.replace('/webhook', '')
            response = requests.get(f"{app_url}/health", timeout=5)
            if response.status_code == 200:
                print(f"   ✅ Aplicación corriendo en: {app_url}")
            else:
                print(f"   ❌ Aplicación retorna status {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error accediendo a la aplicación: {e}")
    else:
        print("   ⚠️  No se puede verificar aplicación (WEBHOOK_URL no disponible)")
    print()

    print("📋 RESUMEN:")
    print("   • Variables de entorno: ✅"    print("   • Conectividad Telegram: ✅"    print("   • Webhook configurado: Verificar arriba"    print("   • Aplicación corriendo: Verificar arriba"
    return True

def main():
    success = check_bot_status()
    if not success:
        print("\n❌ DIAGNÓSTICO FALLIDO")
        print("Revisa la configuración de variables de entorno en Railway")
        return 1

    print("\n✅ DIAGNÓSTICO COMPLETADO")
    print("Si el bot aún no funciona, revisa los logs detallados de Railway")
    return 0

if __name__ == "__main__":
    sys.exit(main())