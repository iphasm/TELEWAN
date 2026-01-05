#!/usr/bin/env python3
"""
Diagnóstico rápido para el comando /start
"""
import os
import asyncio

# Simular las variables de entorno que deberían estar en Railway
os.environ['ALLOWED_USER_ID'] = "1265547936"
os.environ['TELEGRAM_BOT_TOKEN'] = "8279313475:AAGqfBXqX41HLlM5MCDUPmlukQ62-8NSjnw"
os.environ['VOLUME_PATH'] = "/app/storage"
os.environ['WAVESPEED_API_KEY'] = "92047d175a3908df00b119fdd4660ef2f1a2c312da1e93406dce24d1342cb402"
os.environ['USE_WEBHOOK'] = "true"
os.environ['WEBHOOK_URL'] = "telewan-production.up.railway.app"

async def test_start_command():
    """Test básico del comando /start"""
    print("🔍 DIAGNÓSTICO COMANDO /start")
    print("=" * 40)

    try:
        # 1. Verificar que podemos importar las funciones
        from bot import start
        print("✅ Función start importada correctamente")

        # 2. Verificar configuración
        from config import Config
        if Config.TELEGRAM_BOT_TOKEN:
            print("✅ TELEGRAM_BOT_TOKEN configurado")
        else:
            print("❌ TELEGRAM_BOT_TOKEN NO configurado")
            return False

        # 3. Verificar que podemos crear la app
        from fastapi_app import create_app
        app = create_app()
        print("✅ FastAPI app creada correctamente")

        # 4. Verificar conexión con Telegram
        import telegram
        bot = telegram.Bot(token=Config.TELEGRAM_BOT_TOKEN)
        bot_info = await bot.get_me()
        print(f"✅ Bot conectado: @{bot_info.username} (ID: {bot_info.id})")

        # 5. Verificar webhook
        webhook_info = await bot.get_webhook_info()
        if webhook_info.url:
            print(f"✅ Webhook configurado: {webhook_info.url}")
        else:
            print("⚠️  Webhook NO configurado")

        # 6. Simular el comando /start
        print("\n🧪 SIMULANDO COMANDO /start...")

        # Crear un mock update
        class MockUser:
            def __init__(self):
                self.id = 1265547936  # ALLOWED_USER_ID

        class MockMessage:
            def __init__(self):
                self.text = "/start"
                self.from_user = MockUser()

            async def reply_text(self, text, **kwargs):
                print(f"📤 RESPUESTA DEL BOT: {text[:100]}...")
                return None

        class MockUpdate:
            def __init__(self):
                self.message = MockMessage()
                self.effective_user = MockUser()

        # Mock context
        class MockContext:
            def __init__(self):
                self.user_data = {}

        update = MockUpdate()
        context = MockContext()

        # Ejecutar el comando /start
        await start(update, context)
        print("✅ Comando /start ejecutado sin errores")

        print("\n🎉 DIAGNÓSTICO COMPLETADO")
        print("Si este script funciona, el problema está en Railway")
        print("Si falla, hay un problema en el código")

        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_start_command())
    print(f"\nResultado: {'✅ ÉXITO' if success else '❌ FALLO'}")
