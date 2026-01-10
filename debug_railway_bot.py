#!/usr/bin/env python3
"""
Script de diagnóstico específico para problemas del bot en Railway
"""

import os
import sys
import requests
import json
from datetime import datetime

def check_railway_environment():
    """Verificar variables de entorno de Railway"""
    print("🚂 VERIFICACIÓN DE ENTORNO RAILWAY")
    print("=" * 40)

    railway_vars = [
        'RAILWAY_ENVIRONMENT',
        'RAILWAY_PROJECT_ID',
        'RAILWAY_STATIC_URL',
        'PORT',
        'TELEGRAM_BOT_TOKEN',
        'WAVESPEED_API_KEY',
        'WEBHOOK_URL',
        'USE_WEBHOOK'
    ]

    found_vars = {}
    for var in railway_vars:
        value = os.getenv(var)
        if value:
            if 'TOKEN' in var or 'KEY' in var:
                masked = value[:10] + "***"
            else:
                masked = value
            found_vars[var] = masked
            print(f"✅ {var}: {masked}")
        else:
            print(f"❌ {var}: No configurada")

    return found_vars

def infer_webhook_url():
    """Intentar inferir la URL del webhook basada en variables de Railway"""
    print("\n🔗 INFERENCIA DE WEBHOOK URL")
    print("-" * 30)

    # Método 1: Usar WEBHOOK_URL si está configurada
    webhook_url = os.getenv('WEBHOOK_URL')
    if webhook_url:
        print(f"✅ WEBHOOK_URL configurada: {webhook_url}")
        return webhook_url

    # Método 2: Inferir de RAILWAY_STATIC_URL
    static_url = os.getenv('RAILWAY_STATIC_URL')
    if static_url:
        inferred = static_url.replace('https://', 'https://')
        print(f"🔄 Inferida de RAILWAY_STATIC_URL: {inferred}")
        return inferred

    # Método 3: Construir de RAILWAY_PROJECT_ID
    project_id = os.getenv('RAILWAY_PROJECT_ID')
    if project_id:
        inferred = f"https://{project_id}.up.railway.app"
        print(f"🔄 Inferida de RAILWAY_PROJECT_ID: {inferred}")
        return inferred

    print("❌ No se puede inferir WEBHOOK_URL")
    return None

def test_webhook_endpoint(webhook_url):
    """Probar si el endpoint del webhook responde"""
    print(f"\n🌐 PRUEBA DE ENDPOINT DE WEBHOOK: {webhook_url}")
    print("-" * 50)

    try:
        # Probar endpoint de health
        health_url = f"{webhook_url}/health"
        print(f"🔍 Probando health endpoint: {health_url}")

        response = requests.get(health_url, timeout=10)
        if response.status_code == 200:
            print("✅ Health endpoint responde correctamente")
            print(f"   Respuesta: {response.json()}")
        else:
            print(f"❌ Health endpoint retorna status {response.status_code}")
            print(f"   Respuesta: {response.text}")

        # Probar endpoint del webhook
        webhook_test_url = f"{webhook_url}/webhook"
        print(f"🔍 Probando webhook endpoint: {webhook_test_url}")

        response = requests.get(webhook_test_url, timeout=10)
        if response.status_code == 200:
            print("✅ Webhook endpoint responde correctamente")
            data = response.json()
            print(f"   Respuesta: {data}")
        else:
            print(f"❌ Webhook endpoint retorna status {response.status_code}")
            print(f"   Respuesta: {response.text}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Error conectando al webhook: {e}")
        return False

def check_telegram_webhook(token, webhook_url):
    """Verificar configuración del webhook en Telegram"""
    print(f"\n🤖 VERIFICACIÓN DE WEBHOOK EN TELEGRAM")
    print("-" * 45)

    if not token:
        print("❌ No hay token de Telegram configurado")
        return False

    try:
        # Obtener información del webhook
        url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                webhook_info = data.get('result', {})
                current_url = webhook_info.get('url', '')

                print(f"📡 Estado del webhook en Telegram:")
                print(f"   URL actual: {current_url}")
                print(f"   Pending updates: {webhook_info.get('pending_update_count', 0)}")

                if current_url:
                    if webhook_url and current_url.startswith(webhook_url.replace('/webhook', '')):
                        print("✅ Webhook configurado correctamente")
                        return True
                    else:
                        print(f"❌ Webhook configurado en URL diferente: {current_url}")
                        print(f"   Esperado: {webhook_url}")
                        return False
                else:
                    print("❌ No hay webhook configurado en Telegram")
                    return False
            else:
                print("❌ Error en respuesta de Telegram API")
                return False
        else:
            print(f"❌ Error HTTP {response.status_code} en Telegram API")
            return False

    except Exception as e:
        print(f"❌ Error verificando webhook en Telegram: {e}")
        return False

def suggest_fixes(found_vars, webhook_url, webhook_works, telegram_configured):
    """Sugerir soluciones basadas en el diagnóstico"""
    print(f"\n🔧 DIAGNÓSTICO Y SOLUCIONES")
    print("=" * 35)

    issues = []

    # Verificar variables críticas
    if not found_vars.get('TELEGRAM_BOT_TOKEN'):
        issues.append("TELEGRAM_BOT_TOKEN no configurada")

    if not found_vars.get('WAVESPEED_API_KEY'):
        issues.append("WAVESPEED_API_KEY no configurada")

    if not webhook_url:
        issues.append("WEBHOOK_URL no puede inferirse")

    if not webhook_works:
        issues.append("Endpoint del webhook no responde")

    if not telegram_configured:
        issues.append("Webhook no configurado en Telegram")

    if issues:
        print("❌ PROBLEMAS ENCONTRADOS:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")

        print("\n💡 SOLUCIONES RECOMENDADAS:")
        print("   1. Ve a Railway Dashboard > Tu proyecto > Variables")
        print("   2. Configura las variables faltantes:")
        if not found_vars.get('WEBHOOK_URL'):
            print("      • WEBHOOK_URL = https://[tu-proyecto].up.railway.app")
        print("   3. Redeploy: Railway redeploy automáticamente")
        print("   4. Revisa logs de Railway para errores de inicialización")

        return False
    else:
        print("✅ CONFIGURACIÓN CORRECTA")
        print("   Si el bot aún no funciona, revisa los logs detallados de Railway")
        return True

def main():
    print("🔍 DIAGNÓSTICO COMPLETO DEL BOT EN RAILWAY")
    print("=" * 50)

    # 1. Verificar entorno
    found_vars = check_railway_environment()

    # 2. Inferir webhook URL
    webhook_url = infer_webhook_url()

    # 3. Probar endpoint del webhook
    webhook_works = False
    if webhook_url:
        webhook_works = test_webhook_endpoint(webhook_url)

    # 4. Verificar configuración en Telegram
    telegram_configured = False
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if token and webhook_url:
        telegram_configured = check_telegram_webhook(token, webhook_url)

    # 5. Sugerir soluciones
    success = suggest_fixes(found_vars, webhook_url, webhook_works, telegram_configured)

    print(f"\n📊 RESUMEN FINAL:")
    print(f"   Variables configuradas: {len([v for v in found_vars.values() if v])}/8")
    print(f"   Webhook URL inferida: {'✅' if webhook_url else '❌'}")
    print(f"   Endpoint responde: {'✅' if webhook_works else '❌'}")
    print(f"   Telegram configurado: {'✅' if telegram_configured else '❌'}")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)