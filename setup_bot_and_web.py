#!/usr/bin/env python3
"""
Script para configurar y verificar que tanto el bot como la web funcionen
"""

import os
import sys
import asyncio
import requests

def check_env_vars():
    """Verificar variables de entorno requeridas"""
    print("🔧 VERIFICACIÓN DE VARIABLES DE ENTORNO")
    print("=" * 50)

    # Detectar si estamos en Railway
    is_railway = os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RAILWAY_PROJECT_ID')
    if is_railway:
        print("🚂 Detectado entorno Railway - usando configuración optimizada")
    else:
        print("💻 Entorno local detectado")

    required_vars = {
        'TELEGRAM_BOT_TOKEN': 'Token del bot de Telegram (requerido para el bot)',
        'WAVESPEED_API_KEY': 'API Key de WaveSpeed AI (requerido para generar videos)',
    }

    # WEBHOOK_URL solo requerida en Railway
    if is_railway:
        required_vars['WEBHOOK_URL'] = 'URL completa de tu app en Railway (requerido para Railway)'

    missing = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            masked = value[:10] + "***" if len(value) > 10 else value
            print(f"✅ {var}: {masked}")
        else:
            print(f"❌ {var}: NO CONFIGURADO")
            print(f"   💡 {description}")
            missing.append(var)

    # Mostrar configuración de webhook
    use_webhook = os.getenv('USE_WEBHOOK', 'true' if is_railway else 'false').lower() == 'true'
    print(f"🔗 USE_WEBHOOK: {'✅ Activado' if use_webhook else '❌ Desactivado'}")
    if is_railway and not use_webhook:
        print("   ⚠️  ADVERTENCIA: En Railway, webhooks son obligatorios")
        missing.append('USE_WEBHOOK')

    print()
    return missing

def show_railway_setup_instructions(missing_vars):
    """Mostrar instrucciones para configurar Railway"""
    if not missing_vars:
        return

    print("📋 INSTRUCCIONES PARA CONFIGURAR RAILWAY:")
    print("1. Ve a https://railway.app/dashboard")
    print("2. Selecciona tu proyecto TELEWAN")
    print("3. Ve a la pestaña 'Variables' en el menú lateral")
    print("4. Agrega estas variables faltantes:")
    print()

    for var in missing_vars:
        if var == 'TELEGRAM_BOT_TOKEN':
            print(f"   • {var} = [tu_token_del_bot]")
            print("     💡 Cómo obtener:")
            print("       1. Abre Telegram y busca @BotFather")
            print("       2. Escribe /newbot")
            print("       3. Elige un nombre para tu bot")
            print("       4. Copia el token que te da BotFather")
            print()
        elif var == 'WAVESPEED_API_KEY':
            print(f"   • {var} = [tu_api_key_wavespeed]")
            print("     💡 Cómo obtener:")
            print("       1. Ve a https://wavespeed.ai/dashboard/api-keys")
            print("       2. Crea una nueva API key")
            print("       3. Copia la key generada")
            print()
        elif var == 'WEBHOOK_URL':
            print(f"   • {var} = https://[tu-proyecto].up.railway.app")
            print("     💡 Cómo obtener:")
            print("       1. En Railway dashboard, ve a tu proyecto")
            print("       2. Copia el dominio que aparece (ej: telewan-production.up.railway.app)")
            print("       3. Agrega https:// al inicio")
            print("       4. Ejemplo: https://telewan-production.up.railway.app")
            print()
        elif var == 'USE_WEBHOOK':
            print("   • USE_WEBHOOK = true")
            print("     💡 En Railway, webhooks son obligatorios")
            print()

    print("5. Después de agregar las variables:")
    print("   • Railway redeploy automáticamente")
    print("   • O haz click en 'Deploy' manualmente")
    print()

async def test_bot_functionality():
    """Probar funcionalidad del bot"""
    print("🤖 PRUEBA DE FUNCIONALIDAD DEL BOT")
    print("-" * 40)

    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("❌ No se puede probar el bot: TELEGRAM_BOT_TOKEN no configurado")
        return False

    try:
        # Probar conectividad con Telegram API
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                username = bot_info.get('username', 'Unknown')
                print(f"✅ Telegram API: Conectado (@{username})")
                return True
            else:
                print("❌ Telegram API: Token inválido")
                return False
        else:
            print(f"❌ Telegram API: Error HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error conectando a Telegram: {e}")
        return False

async def test_wavespeed_api():
    """Probar conectividad con WaveSpeed API"""
    print("🌊 PRUEBA DE WAVESPEED API")
    print("-" * 30)

    api_key = os.getenv('WAVESPEED_API_KEY')
    if not api_key:
        print("❌ No se puede probar WaveSpeed: API_KEY no configurado")
        return False

    try:
        headers = {'Authorization': f'Bearer {api_key}'}
        response = requests.get('https://api.wavespeed.ai/api/v3/wavespeed-ai/models',
                              headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ WaveSpeed API: Conectado")
            return True
        else:
            print(f"❌ WaveSpeed API: Error HTTP {response.status_code}")
            if response.status_code == 401:
                print("   💡 Verifica que tu API key sea correcta")
            return False
    except Exception as e:
        print(f"❌ Error conectando a WaveSpeed: {e}")
        return False

def show_final_status():
    """Mostrar estado final y próximos pasos"""
    print("\n" + "=" * 50)
    print("🎯 ESTADO FINAL Y PRÓXIMOS PASOS")
    print("=" * 50)

    all_good = True
    missing_vars = check_env_vars()

    if missing_vars:
        all_good = False
        print(f"\n❌ FALTAN {len(missing_vars)} VARIABLES:")
        for var in missing_vars:
            print(f"   • {var}")

    # Ejecutar pruebas async
    async def run_tests():
        bot_ok = await test_bot_functionality()
        wavespeed_ok = await test_wavespeed_api()
        return bot_ok, wavespeed_ok

    import asyncio
    bot_ok, wavespeed_ok = asyncio.run(run_tests())

    if not bot_ok:
        all_good = False
    if not wavespeed_ok:
        all_good = False

    if all_good:
        print("\n✅ ¡TODO CONFIGURADO CORRECTAMENTE!")
        print("\n🚀 Tu aplicación debería funcionar con:")
        print("   • 🌐 Web App: https://[tu-app].railway.app")
        print("   • 🤖 Bot de Telegram: @tu_bot_username")
        print("\n💡 Para probar el bot:")
        print("   1. Abre Telegram")
        print("   2. Busca tu bot por username")
        print("   3. Envía /start")
        print("   4. Envía una foto con un caption descriptivo")
    else:
        print("\n❌ CONFIGURACIÓN INCOMPLETA")
        print("\n🔧 Sigue las instrucciones arriba para configurar las variables faltantes")

    return all_good

if __name__ == "__main__":
    print("🚀 CONFIGURACIÓN BOT + WEB PARA TELEWAN")
    print("=" * 50)

    missing_vars = check_env_vars()
    if missing_vars:
        show_railway_setup_instructions(missing_vars)

    success = show_final_status()
    sys.exit(0 if success else 1)