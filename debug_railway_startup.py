#!/usr/bin/env python3
"""
Script de diagnóstico que se ejecuta al inicio en Railway
Se agrega al principio de bot.py para debuggear problemas de inicialización
"""

import os
import sys
import logging

# Configurar logging básico
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_railway_environment():
    """Debug detallado del entorno Railway"""
    print("=" * 60)
    print("🚂 DEBUG RAILWAY STARTUP")
    print("=" * 60)

    # Todas las variables de entorno
    print("📋 TODAS LAS VARIABLES DE ENTORNO:")
    for key, value in sorted(os.environ.items()):
        if any(secret in key.upper() for secret in ['TOKEN', 'KEY', 'SECRET', 'PASSWORD']):
            masked = value[:10] + "***" if len(value) > 10 else value
            print(f"   {key} = {masked}")
        else:
            print(f"   {key} = {value}")
    print()

    # Variables críticas específicamente
    critical_vars = [
        'TELEGRAM_BOT_TOKEN',
        'WAVESPEED_API_KEY',
        'WEBHOOK_URL',
        'USE_WEBHOOK',
        'PORT',
        'RAILWAY_ENVIRONMENT',
        'RAILWAY_PROJECT_ID',
        'RAILWAY_STATIC_URL'
    ]

    print("🎯 VARIABLES CRÍTICAS:")
    missing = []
    for var in critical_vars:
        value = os.getenv(var)
        if value:
            if 'TOKEN' in var or 'KEY' in var:
                masked = value[:10] + "***"
                print(f"   ✅ {var}: {masked}")
            else:
                print(f"   ✅ {var}: {value}")
        else:
            print(f"   ❌ {var}: NO CONFIGURADA")
            missing.append(var)
    print()

    # Detectar Railway
    is_railway = os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RAILWAY_PROJECT_ID')
    print(f"🚂 ¿Es Railway?: {'✅ SÍ' if is_railway else '❌ NO'}")

    if is_railway:
        print("   Railway Environment:", os.getenv('RAILWAY_ENVIRONMENT'))
        print("   Railway Project ID:", os.getenv('RAILWAY_PROJECT_ID', 'None'))
        print("   Railway Static URL:", os.getenv('RAILWAY_STATIC_URL', 'None'))
    print()

    # Verificar conectividad básica
    print("🌐 PRUEBAS DE CONECTIVIDAD:")
    try:
        import requests
        # Probar Telegram API
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if token:
            try:
                response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('ok'):
                        bot_username = data['result'].get('username', 'Unknown')
                        print(f"   ✅ Telegram API: Conectado (@{bot_username})")
                    else:
                        print("   ❌ Telegram API: Token inválido")
                else:
                    print(f"   ❌ Telegram API: Error HTTP {response.status_code}")
            except Exception as e:
                print(f"   ❌ Telegram API: Error de conexión - {e}")
        else:
            print("   ⚠️  Telegram: Token no disponible para prueba")

        # Probar WaveSpeed API
        api_key = os.getenv('WAVESPEED_API_KEY')
        if api_key:
            try:
                headers = {'Authorization': f'Bearer {api_key}'}
                response = requests.get('https://api.wavespeed.ai/api/v3/wavespeed-ai/models',
                                      headers=headers, timeout=5)
                if response.status_code == 200:
                    print("   ✅ WaveSpeed API: Conectado")
                else:
                    print(f"   ❌ WaveSpeed API: Error HTTP {response.status_code}")
            except Exception as e:
                print(f"   ❌ WaveSpeed API: Error de conexión - {e}")
        else:
            print("   ⚠️  WaveSpeed: API key no disponible para prueba")

    except ImportError:
        print("   ⚠️  Requests no disponible para pruebas")
    print()

    print("=" * 60)
    return missing

if __name__ == "__main__":
    missing = debug_railway_environment()
    if missing:
        print(f"❌ VARIABLES FALTANTES: {', '.join(missing)}")
        print("💡 Configura estas variables en Railway Dashboard > Variables")
        sys.exit(1)
    else:
        print("✅ TODAS LAS VARIABLES CONFIGURADAS")
        sys.exit(0)