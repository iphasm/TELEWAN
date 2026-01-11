#!/usr/bin/env python3
"""
Script para configurar las variables de entorno faltantes en Railway
Ejecutar después de hacer deploy para verificar configuración
"""

import os
import sys
import requests

def check_railway_env():
    """Verifica la configuración de Railway"""
    print("🔧 VERIFICACIÓN DE CONFIGURACIÓN RAILWAY")
    print("=" * 50)

    # Variables requeridas
    required_vars = {
        'TELEGRAM_BOT_TOKEN': 'Token del bot de Telegram (obtener en @BotFather)',
        'WAVESPEED_API_KEY': 'API Key de WaveSpeed AI',
        'WEBHOOK_URL': 'URL completa de tu app en Railway (opcional para webhook)',
    }

    missing = []
    configured = []

    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            masked = value[:10] + "***" if len(value) > 10 else value
            print(f"✅ {var}: {masked}")
            configured.append(var)
        else:
            print(f"❌ {var}: NO CONFIGURADO")
            print(f"   💡 {description}")
            missing.append(var)

    print("\n" + "=" * 50)

    if missing:
        print(f"❌ FALTAN {len(missing)} VARIABLES:")
        for var in missing:
            print(f"   • {var}")

        print("\n📋 INSTRUCCIONES PARA CONFIGURAR EN RAILWAY:")
        print("1. Ve a https://railway.app/dashboard")
        print("2. Selecciona tu proyecto TELEWAN")
        print("3. Ve a la pestaña 'Variables'")
        print("4. Agrega las siguientes variables:")

        for var in missing:
            if var == 'TELEGRAM_BOT_TOKEN':
                print(f"   • {var} = [tu_token_del_bot]")
                print("     💡 Obtener en Telegram: mensaje a @BotFather con /newbot")
            elif var == 'WAVESPEED_API_KEY':
                print(f"   • {var} = [tu_api_key_wavespeed]")
                print("     💡 Obtener en: https://wavespeed.ai/dashboard/api-keys")
            elif var == 'WEBHOOK_URL':
                print(f"   • {var} = https://[tu-app].railway.app")
                print("     💡 Reemplaza [tu-app] con el nombre de tu app en Railway")

        print("\n5. Después de agregar las variables:")
        print("   • Haz click en 'Deploy' para redeploy")
        print("   • O ejecuta: git commit --allow-empty -m 'update env' && git push")

        return False
    else:
        print("✅ TODAS LAS VARIABLES CONFIGURADAS")
        return True

def test_connectivity():
    """Prueba la conectividad con los servicios externos"""
    print("\n🔗 PRUEBA DE CONECTIVIDAD")
    print("-" * 30)

    # Test Telegram
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if token:
        try:
            response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    username = data['result'].get('username', 'Unknown')
                    print(f"✅ Telegram: Conectado (@{username})")
                else:
                    print("❌ Telegram: Token inválido")
            else:
                print(f"❌ Telegram: Error HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Telegram: Error de conexión - {e}")
    else:
        print("⚠️  Telegram: Saltando prueba (sin token)")

    # Test WaveSpeed
    api_key = os.getenv('WAVESPEED_API_KEY')
    if api_key:
        try:
            headers = {'Authorization': f'Bearer {api_key}'}
            response = requests.get('https://api.wavespeed.ai/api/v3/wavespeed-ai/models',
                                  headers=headers, timeout=5)
            if response.status_code == 200:
                print("✅ WaveSpeed: Conectado")
            else:
                print(f"❌ WaveSpeed: Error HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ WaveSpeed: Error de conexión - {e}")
    else:
        print("⚠️  WaveSpeed: Saltando prueba (sin API key)")

if __name__ == "__main__":
    success = check_railway_env()
    if success:
        test_connectivity()
    sys.exit(0 if success else 1)