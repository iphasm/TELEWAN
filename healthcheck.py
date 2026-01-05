#!/usr/bin/env python3
"""
Healthcheck simple para verificar que el bot está funcionando
Ejecutar: python healthcheck.py
"""
import os
import asyncio

async def health_check():
    """Verificación básica de que el bot puede inicializarse"""
    print("🏥 HEALTH CHECK - TELEWAN BOT")
    print("=" * 40)

    # Verificar credenciales básicas
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    api_key = os.getenv('WAVESPEED_API_KEY')

    if not token:
        print("❌ FALTA: TELEGRAM_BOT_TOKEN")
        return False

    if not api_key:
        print("❌ FALTA: WAVESPEED_API_KEY")
        return False

    print("✅ Credenciales configuradas")

    # Verificar imports
    try:
        from config import Config
        Config.validate()
        print("✅ Configuración válida")
    except Exception as e:
        print(f"❌ Error de configuración: {e}")
        return False

    # Verificar FastAPI
    try:
        from fastapi_app import create_app
        app = create_app()
        print("✅ FastAPI app creada correctamente")
    except Exception as e:
        print(f"❌ Error creando FastAPI app: {e}")
        return False

    # Verificar conexión con Telegram
    try:
        import telegram
        bot = telegram.Bot(token=token)
        bot_info = await bot.get_me()
        print(f"✅ Telegram bot conectado: @{bot_info.username}")
    except Exception as e:
        print(f"❌ Error conectando con Telegram: {e}")
        return False

    # Verificar webhook
    try:
        webhook_info = await bot.get_webhook_info()
        if webhook_info.url:
            print(f"✅ Webhook configurado: {webhook_info.url}")
        else:
            print("⚠️  Webhook NO configurado (usando polling)")
    except Exception as e:
        print(f"⚠️  Error verificando webhook: {e}")

    print("✅ HEALTH CHECK PASSED")
    print("🎯 El bot debería estar funcionando correctamente")
    return True

if __name__ == "__main__":
    success = asyncio.run(health_check())
    exit(0 if success else 1)
