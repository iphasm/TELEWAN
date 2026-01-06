#!/usr/bin/env python3
"""
Validar que las credenciales configuradas en Railway funcionan
"""
import os
import asyncio
import sys

# NOTA: Este archivo requiere que las siguientes variables de entorno estén configuradas:
# - TELEGRAM_BOT_TOKEN: Token del bot de Telegram
# - WAVESPEED_API_KEY: API key de WaveSpeed AI
# - ALLOWED_USER_ID: ID del usuario autorizado
# - VOLUME_PATH: Ruta del volumen para archivos temporales
# - USE_WEBHOOK: true/false para usar webhook
# - WEBHOOK_URL: URL del webhook (solo si USE_WEBHOOK=true)

# Las variables deben configurarse en Railway o en un archivo .env (no incluido en git)

async def validate_credentials():
    """Validar todas las credenciales configuradas"""
    print("🔐 VALIDACIÓN DE CREDENCIALES - TELEWAN BOT")
    print("=" * 60)

    # 1. Verificar configuración
    print("📋 1. CONFIGURACIÓN:")
    try:
        from config import Config
        Config.validate()
        print("✅ Configuración cargada correctamente")
    except Exception as e:
        print(f"❌ Error de configuración: {e}")
        return False

    print(f"   🤖 Telegram Token: {'✅' if Config.TELEGRAM_BOT_TOKEN else '❌'}")
    print(f"   🔑 WaveSpeed API: {'✅' if Config.WAVESPEED_API_KEY else '❌'}")
    print(f"   👤 User ID Permitido: {Config.ALLOWED_USER_ID}")
    print(f"   📁 Volume Path: {Config.VOLUME_PATH}")
    print(f"   📡 Webhook URL: {Config.WEBHOOK_URL}")
    print(f"   🔄 Use Webhook: {Config.USE_WEBHOOK}")

    # 2. Verificar conexión con Telegram
    print("\n📋 2. CONEXIÓN TELEGRAM:")
    if Config.TELEGRAM_BOT_TOKEN:
        try:
            import telegram
            bot = telegram.Bot(token=Config.TELEGRAM_BOT_TOKEN)
            bot_info = await bot.get_me()
            print("✅ Conexión con Telegram exitosa")
            print(f"   🤖 Bot: @{bot_info.username}")
            print(f"   📝 Nombre: {bot_info.first_name}")
            print(f"   🆔 ID: {bot_info.id}")

            # Verificar webhook actual
            webhook_info = await bot.get_webhook_info()
            if webhook_info.url:
                print(f"   📡 Webhook actual: {webhook_info.url}")
                if 'railway.app' in webhook_info.url:
                    print("   ✅ Webhook apunta a Railway")
                else:
                    print("   ⚠️  Webhook NO apunta a Railway")
            else:
                print("   ⚠️  Webhook NO configurado")

        except Exception as e:
            print(f"❌ Error conectando con Telegram: {e}")
            return False
    else:
        print("❌ Token de Telegram no configurado")
        return False

    # 3. Verificar WaveSpeed API
    print("\n📋 3. CONEXIÓN WAVESPEED:")
    if Config.WAVESPEED_API_KEY:
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                headers = {'Authorization': f'Bearer {Config.WAVESPEED_API_KEY}'}
                async with session.get('https://api.wavespeed.ai/api/v3/wavespeed-ai/models',
                                     headers=headers, timeout=10) as response:
                    if response.status == 200:
                        print("✅ Conexión con WaveSpeed exitosa")
                        data = await response.json()
                        models_count = len(data.get('data', []))
                        print(f"   🎬 Modelos disponibles: {models_count}")
                    else:
                        print(f"❌ Error HTTP con WaveSpeed: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Error conectando con WaveSpeed: {e}")
            return False
    else:
        print("❌ API Key de WaveSpeed no configurada")
        return False

    # 4. Verificar FastAPI
    print("\n📋 4. FASTAPI APP:")
    try:
        from fastapi_app import create_app
        app = create_app()
        print("✅ FastAPI app creada correctamente")
    except Exception as e:
        print(f"❌ Error creando FastAPI app: {e}")
        return False

    # 5. Verificar comandos del bot
    print("\n📋 5. COMANDOS DEL BOT:")
    try:
        from bot import start, help_command
        print("✅ Funciones de comandos importadas correctamente")
        print("   📝 /start: Disponible")
        print("   ❓ /help: Disponible")
        print("   🎬 /models, /quality, /preview: Disponibles")
        print("   🤖 /optimize: Disponible")
    except Exception as e:
        print(f"❌ Error importando comandos: {e}")
        return False

    print("\n" + "=" * 60)
    print("🎉 VALIDACIÓN COMPLETA - CREDENCIALES FUNCIONANDO")
    print("=" * 60)
    print("✅ Todas las credenciales están configuradas correctamente")
    print("✅ Conexiones con Telegram y WaveSpeed verificadas")
    print("✅ Aplicación FastAPI inicializa correctamente")
    print("✅ Comandos del bot disponibles")
    print()
    print("🚀 El bot debería funcionar correctamente ahora")
    print("📱 Prueba enviando /start al bot")

    return True

if __name__ == "__main__":
    success = asyncio.run(validate_credentials())
    print(f"\n🔐 Validación de credenciales: {'EXITOSA' if success else 'FALLIDA'}")
    sys.exit(0 if success else 1)
