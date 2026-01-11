#!/usr/bin/env python3
"""
Script para debug detallado de respuestas del bot
Agrega logging adicional para diagnosticar por qué el bot no responde
"""

import os
import logging

# Configurar logging más detallado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def add_debug_to_bot():
    """Agregar debugging adicional al bot"""

    # Patch the start function to add more logging
    import bot

    original_start = bot.start

    async def debug_start(update, context):
        logger.info("🚀 START COMMAND RECEIVED")
        logger.info(f"   Update ID: {update.update_id}")
        logger.info(f"   User ID: {update.message.from_user.id if update.message else 'N/A'}")
        logger.info(f"   Chat ID: {update.message.chat.id if update.message else 'N/A'}")
        logger.info(f"   Message: {update.message.text if update.message else 'N/A'}")

        try:
            await original_start(update, context)
            logger.info("✅ START COMMAND PROCESSED SUCCESSFULLY")
        except Exception as e:
            logger.error(f"❌ ERROR IN START COMMAND: {e}")
            import traceback
            logger.error(f"   Traceback: {traceback.format_exc()}")

    # Replace the function
    bot.start = debug_start
    logger.info("🐛 Debug logging added to start command")

def test_bot_initialization():
    """Probar la inicialización del bot sin ejecutar la aplicación completa"""
    print("🧪 TESTING BOT INITIALIZATION")
    print("="*40)

    try:
        # Importar módulos necesarios
        from telegram import Update
        from telegram.ext import Application, CommandHandler, MessageHandler, filters
        from config import Config

        print("✅ Telegram modules imported")

        # Verificar configuración
        if not Config.TELEGRAM_BOT_TOKEN:
            print("❌ TELEGRAM_BOT_TOKEN not configured")
            return False

        print("✅ Configuration loaded")

        # Crear aplicación de prueba
        app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        print("✅ Application created")

        # Agregar un handler de prueba
        async def test_handler(update, context):
            print(f"🎯 TEST HANDLER CALLED: {update.message.text if update.message else 'No message'}")
            await update.message.reply_text("Test response")

        app.add_handler(CommandHandler("test", test_handler))
        print("✅ Test handler added")

        # Intentar inicializar
        import asyncio
        asyncio.run(app.initialize())
        print("✅ Application initialized")

        # Verificar bot info
        bot_info = app.bot.get_me()
        print(f"✅ Bot info: @{bot_info.username} (ID: {bot_info.id})")

        return True

    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        return False

def simulate_webhook_processing():
    """Simular el procesamiento de un webhook para testing"""
    print("\n🧪 SIMULATING WEBHOOK PROCESSING")
    print("="*40)

    try:
        import asyncio
        from telegram import Update
        from telegram.ext import Application
        from config import Config

        async def test_webhook():
            # Crear aplicación
            app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()

            # Agregar handlers como en fastapi_app.py
            from bot import (
                start, help_command, list_models_command, handle_text_video,
                handle_quality_video, handle_preview_video, handle_optimize, handle_lastvideo, handle_balance, handle_debug_files, handle_download, handle_social_url,
                handle_photo, handle_document_image, handle_sticker_image,
                image_document_filter, static_sticker_filter
            )

            app.add_handler(CommandHandler("start", start))
            app.add_handler(CommandHandler("help", help_command))
            print("✅ Handlers added to test application")

            # Crear una actualización de prueba
            test_update_data = {
                "update_id": 123456789,
                "message": {
                    "message_id": 123,
                    "from": {
                        "id": 123456789,
                        "is_bot": False,
                        "first_name": "Test",
                        "username": "test_user"
                    },
                    "chat": {
                        "id": 123456789,
                        "type": "private"
                    },
                    "date": 1640995200,  # Timestamp
                    "text": "/start"
                }
            }

            print("📨 Processing test update...")
            update = Update.de_json(test_update_data, app.bot)
            print(f"✅ Update object created: {type(update)}")

            # Procesar la actualización
            await app.process_update(update)
            print("✅ Update processed successfully")

        asyncio.run(test_webhook())
        return True

    except Exception as e:
        print(f"❌ Error in webhook simulation: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🔧 DEBUG BOT RESPONSES")
    print(f"🐍 Python: {__import__('sys').version.split()[0]}")
    print(f"📁 Working directory: {os.getcwd()}")
    print()

    # Test 1: Basic initialization
    init_success = test_bot_initialization()

    if not init_success:
        print("\n❌ BASIC INITIALIZATION FAILED - Check configuration")
        return 1

    # Test 2: Webhook processing simulation
    webhook_success = simulate_webhook_processing()

    if not webhook_success:
        print("\n❌ WEBHOOK PROCESSING FAILED - Check handlers")
        return 1

    print("\n✅ ALL TESTS PASSED")
    print("🤔 If the bot still doesn't respond in production:")
    print("   1. Check Railway logs for detailed error messages")
    print("   2. Verify WEBHOOK_URL is correctly configured")
    print("   3. Ensure the application is actually receiving webhooks")
    print("   4. Check if responses are being sent but not received by users")

    return 0

if __name__ == "__main__":
    exit(main())