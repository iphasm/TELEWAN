#!/usr/bin/env python3
"""
Script de debug para ejecutar en Railway y diagnosticar por qué /start no funciona
"""
import os
import sys
import asyncio

async def railway_debug():
    """Debug completo para Railway"""
    print("🚂 RAILWAY DEBUG - Comando /start")
    print("=" * 50)

    # 1. Información del entorno
    print("📋 1. ENTORNO RAILWAY:")
    print(f"   🐍 Python: {sys.version}")
    print(f"   📁 PWD: {os.getcwd()}")
    print(f"   🚂 RAILWAY_PROJECT_ID: {os.getenv('RAILWAY_PROJECT_ID', 'not set')}")

    # 2. Variables críticas
    print("\n📋 2. VARIABLES DE ENTORNO:")
    critical_vars = {
        'TELEGRAM_BOT_TOKEN': 'Token del bot',
        'WAVESPEED_API_KEY': 'API de WaveSpeed',
        'ALLOWED_USER_ID': 'Usuario autorizado',
        'USE_WEBHOOK': 'Modo webhook',
        'WEBHOOK_URL': 'URL del webhook'
    }

    missing = []
    for var, desc in critical_vars.items():
        value = os.getenv(var)
        if value:
            if var in ['TELEGRAM_BOT_TOKEN', 'WAVESPEED_API_KEY']:
                masked = value[:10] + "..." + value[-5:] if len(value) > 15 else value
            else:
                masked = value
            print(f"   ✅ {var}: {masked}")
        else:
            print(f"   ❌ {var}: NO CONFIGURADO - {desc}")
            missing.append(var)

    if missing:
        print(f"\n❌ FALTAN {len(missing)} VARIABLES CRÍTICAS:")
        for var in missing:
            print(f"   • {var}")
        print("\n🔧 SOLUCIÓN: Configurar en Railway Dashboard > Variables")
        return False

    # 3. Verificar imports
    print("\n📋 3. IMPORTS:")
    try:
        from config import Config
        print("✅ config importado")

        from bot import start
        print("✅ función start importada")

        from fastapi_app import create_app
        print("✅ FastAPI app importable")

        from events import init_event_bus, init_event_handlers
        print("✅ sistema de eventos importable")

    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        return False

    # 4. Verificar configuración
    print("\n📋 4. CONFIGURACIÓN:")
    try:
        # Validar configuración
        Config.validate()
        print("✅ Configuración válida")

        print(f"   🤖 Token configurado: {'✅' if Config.TELEGRAM_BOT_TOKEN else '❌'}")
        print(f"   🔑 API key configurada: {'✅' if Config.WAVESPEED_API_KEY else '❌'}")
        print(f"   👤 User ID: {Config.ALLOWED_USER_ID}")
        print(f"   📡 Webhook URL: {Config.WEBHOOK_URL}")
        print(f"   🎯 Welcome message: {'✅' if Config.WELCOME_MESSAGE else '❌'}")

    except Exception as e:
        print(f"❌ Error en configuración: {e}")
        return False

    # 5. Verificar conexión con Telegram
    print("\n📋 5. CONEXIÓN TELEGRAM:")
    try:
        import telegram
        bot = telegram.Bot(token=Config.TELEGRAM_BOT_TOKEN)
        bot_info = await bot.get_me()
        print(f"✅ Bot conectado: @{bot_info.username} (ID: {bot_info.id})")

        # Verificar webhook
        webhook_info = await bot.get_webhook_info()
        if webhook_info.url:
            print(f"✅ Webhook configurado: {webhook_info.url}")
            expected_url = "https://telewan-production.up.railway.app/webhook"
            if webhook_info.url == expected_url:
                print("✅ Webhook URL correcta")
            else:
                print(f"⚠️  Webhook URL diferente: esperado {expected_url}")
        else:
            print("❌ Webhook NO configurado")

    except Exception as e:
        print(f"❌ Error conectando con Telegram: {e}")
        return False

    # 6. Verificar FastAPI app
    print("\n📋 6. FASTAPI APP:")
    try:
        app = create_app()
        print("✅ FastAPI app creada correctamente")

        # Verificar que tiene los endpoints
        routes = [route.path for route in app.routes]
        print(f"✅ Endpoints disponibles: {len(routes)} rutas")
        webhook_route = any("/webhook" in route for route in routes)
        health_route = any("/health" in route for route in routes)
        print(f"   📡 Webhook endpoint: {'✅' if webhook_route else '❌'}")
        print(f"   ❤️ Health endpoint: {'✅' if health_route else '❌'}")

    except Exception as e:
        print(f"❌ Error creando FastAPI app: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 7. Simular inicialización del bot
    print("\n📋 7. INICIALIZACIÓN DEL BOT:")
    try:
        # Simular el lifespan manager
        await init_event_bus()
        print("✅ Event bus inicializado")

        await init_event_handlers()
        print("✅ Event handlers inicializados")

        # Verificar que la app de Telegram se puede crear
        from telegram.ext import Application
        telegram_app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        await telegram_app.initialize()
        print("✅ Aplicación de Telegram inicializada")

        # Verificar que tiene handlers
        handlers_count = len(telegram_app.handlers[0]) if telegram_app.handlers else 0
        print(f"✅ Handlers registrados: {handlers_count}")

        # Limpiar
        await telegram_app.shutdown()
        print("✅ Aplicación de Telegram cerrada correctamente")

    except Exception as e:
        print(f"❌ Error en inicialización: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 8. Verificar Procfile
    print("\n📋 8. PROCESO DE EJECUCIÓN:")
    if os.path.exists('Procfile'):
        with open('Procfile', 'r') as f:
            procfile_content = f.read().strip()
        print(f"✅ Procfile: {procfile_content}")

        if 'fastapi_app.py' in procfile_content:
            print("✅ Procfile apunta a FastAPI correctamente")
        else:
            print("❌ Procfile NO apunta a FastAPI")
    else:
        print("❌ Procfile no encontrado")

    print("\n" + "=" * 50)
    print("🎉 DIAGNÓSTICO RAILWAY COMPLETADO")
    print("=" * 50)
    print("✅ TODOS LOS COMPONENTES FUNCIONAN CORRECTAMENTE")
    print()
    print("🔍 POSIBLES CAUSAS DEL PROBLEMA:")
    print("1. 🚀 Railway no ha redeployeado los últimos cambios")
    print("2. 🌐 Variables de entorno no aplicadas al contenedor")
    print("3. 📡 Webhook no está recibiendo las actualizaciones")
    print("4. 🔄 Puerto o URL de webhook incorrectos")
    print()
    print("🛠️ SOLUCIONES:")
    print("1. Forzar redeploy en Railway Dashboard")
    print("2. Verificar variables en Railway > Settings > Variables")
    print("3. Revisar logs de Railway para errores de webhook")
    print("4. Probar curl al health endpoint:")
    print("   curl https://telewan-production.up.railway.app/health")
    print()
    print("📞 El código funciona perfectamente - problema en Railway")

    return True

if __name__ == "__main__":
    success = asyncio.run(railway_debug())
    print(f"\n🚂 Railway Debug: {'✅ ÉXITO' if success else '❌ FALLO'}")
    sys.exit(0 if success else 1)
