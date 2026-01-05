#!/usr/bin/env python3
"""
Debug script para Railway - ejecuta diagnóstico completo del bot
"""
import os
import sys
import asyncio
import logging
from datetime import datetime

# Configurar logging detallado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def debug_railway_bot():
    """Diagnóstico completo del bot en Railway"""
    print("🐛 DEBUG RAILWAY - TELEWAN BOT")
    print("=" * 60)
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    print(f"🐍 Python: {sys.version}")
    print(f"📁 Working Directory: {os.getcwd()}")
    print()

    # 1. Verificar variables de entorno
    print("📋 1. VARIABLES DE ENTORNO:")
    critical_vars = ['TELEGRAM_BOT_TOKEN', 'WAVESPEED_API_KEY', 'USE_WEBHOOK', 'WEBHOOK_URL']
    for var in critical_vars:
        value = os.getenv(var)
        if value:
            masked = value[:10] + "..." + value[-5:] if len(value) > 15 else value
            print(f"   ✅ {var}: {masked}")
        else:
            print(f"   ❌ {var}: NO CONFIGURADA")

    print()

    # 2. Verificar archivos
    print("📋 2. ARCHIVOS DEL SISTEMA:")
    files_to_check = [
        'fastapi_app.py',
        'bot.py',
        'config.py',
        'Procfile',
        'requirements.txt'
    ]

    for file in files_to_check:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"   ✅ {file}: {size} bytes")
        else:
            print(f"   ❌ {file}: NO ENCONTRADO")

    print()

    # 3. Verificar Procfile
    print("📋 3. PROCESO DE EJECUCIÓN:")
    if os.path.exists('Procfile'):
        with open('Procfile', 'r') as f:
            procfile_content = f.read().strip()
        print(f"   📄 Procfile: {procfile_content}")

        # Verificar qué comando se ejecutaría
        if 'fastapi_app.py' in procfile_content:
            print("   ✅ Procfile apunta a FastAPI")
        else:
            print("   ❌ Procfile NO apunta a FastAPI")
    else:
        print("   ❌ Procfile no encontrado")

    # Verificar qué proceso se está ejecutando
    try:
        current_pid = os.getpid()
        print(f"   🔄 PID actual: {current_pid}")
        print(f"   🔄 Comando ejecutado: python {sys.argv[0]}")
    except Exception as e:
        print(f"   ⚠️  No se puede verificar proceso: {e}")

    print()

    # 4. Verificar dependencias
    print("📋 4. DEPENDENCIAS:")
    dependencies = [
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('aiohttp', 'aiohttp'),
        ('telegram', 'python-telegram-bot'),
        ('redis', 'redis')
    ]

    for module, name in dependencies:
        try:
            __import__(module)
            print(f"   ✅ {name}: Instalado")
        except ImportError:
            print(f"   ❌ {name}: NO INSTALADO")

    print()

    # 5. Verificar configuración
    print("📋 5. CONFIGURACIÓN:")
    try:
        from config import Config
        print("   ✅ config.py importable")

        # Intentar validar configuración
        try:
            Config.validate()
            print("   ✅ Configuración válida")
        except ValueError as e:
            print(f"   ❌ Error de configuración: {e}")

        # Mostrar valores de configuración
        print(f"   🔗 WEBHOOK_URL: {Config.WEBHOOK_URL}")
        print(f"   🔌 WEBHOOK_PORT: {Config.WEBHOOK_PORT}")
        print(f"   📡 WEBHOOK_PATH: {Config.WEBHOOK_PATH}")
        print(f"   🤖 TELEGRAM_TOKEN: {'Configurado' if Config.TELEGRAM_BOT_TOKEN else 'NO CONFIGURADO'}")
        print(f"   🔑 WAVESPEED_API: {'Configurado' if Config.WAVESPEED_API_KEY else 'NO CONFIGURADO'}")

    except ImportError as e:
        print(f"   ❌ Error importando config: {e}")

    print()

    # 6. Verificar conectividad con Telegram
    print("📋 6. CONECTIVIDAD:")
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if token:
        try:
            import telegram
            bot = telegram.Bot(token=token)

            # Obtener información del bot
            bot_info = await bot.get_me()
            print(f"   ✅ Telegram Bot: @{bot_info.username} (ID: {bot_info.id})")
            print(f"   🤖 Nombre: {bot_info.first_name}")

            # Verificar webhook
            webhook_info = await bot.get_webhook_info()
            if webhook_info.url:
                print(f"   📡 Webhook configurado: {webhook_info.url}")
                if 'railway.app' in webhook_info.url:
                    print("   ✅ Webhook apunta a Railway")
                else:
                    print("   ⚠️  Webhook NO apunta a Railway")
            else:
                print("   ❌ Webhook NO configurado")

            # Verificar si el bot puede recibir updates
            try:
                updates = await bot.get_updates(timeout=5)
                print(f"   📨 Updates disponibles: {len(updates) if updates else 0}")
            except Exception as e:
                print(f"   ⚠️  No se pueden obtener updates: {e}")

        except Exception as e:
            print(f"   ❌ Error con Telegram: {e}")
    else:
        print("   ⚠️  No se puede verificar Telegram (sin token)")

    print()

    # 7. Verificar WaveSpeed API
    print("📋 7. WAVESPEED API:")
    api_key = os.getenv('WAVESPEED_API_KEY')
    if api_key:
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                headers = {'Authorization': f'Bearer {api_key}'}
                async with session.get('https://api.wavespeed.ai/api/v3/wavespeed-ai/models',
                                     headers=headers, timeout=10) as response:
                    if response.status == 200:
                        print("   ✅ WaveSpeed API: Conectado")
                    else:
                        print(f"   ❌ WaveSpeed API: Error HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ WaveSpeed API: Error de conexión - {e}")
    else:
        print("   ⚠️  No se puede verificar WaveSpeed (sin API key)")

    print()

    # 8. Verificar sistema de eventos
    print("📋 8. SISTEMA DE EVENTOS:")
    try:
        from events import event_bus, init_event_bus, shutdown_event_bus
        print("   ✅ Sistema de eventos importable")

        # Verificar Redis
        try:
            await init_event_bus()
            health = await event_bus.health_check()
            print(f"   ✅ EventBus inicializado: {health}")
            await shutdown_event_bus()
        except Exception as e:
            print(f"   ❌ Error con EventBus: {e}")

    except ImportError as e:
        print(f"   ❌ Sistema de eventos no disponible: {e}")

    print()
    print("=" * 60)
    print("🎯 RESUMEN DE DEBUG")
    print("=" * 60)

    # Verificar condiciones críticas
    critical_issues = []

    if not os.getenv('TELEGRAM_BOT_TOKEN'):
        critical_issues.append("TELEGRAM_BOT_TOKEN no configurado")

    if not os.getenv('WAVESPEED_API_KEY'):
        critical_issues.append("WAVESPEED_API_KEY no configurado")

    if not os.path.exists('fastapi_app.py'):
        critical_issues.append("fastapi_app.py no encontrado")

    if os.path.exists('Procfile') and 'fastapi_app.py' not in open('Procfile').read():
        critical_issues.append("Procfile no apunta a FastAPI")

    if critical_issues:
        print("❌ PROBLEMAS CRÍTICOS:")
        for issue in critical_issues:
            print(f"   • {issue}")

        print("\n🔧 SOLUCIONES:")
        print("   1. Configurar variables de entorno en Railway Dashboard")
        print("   2. Verificar que Procfile apunte a fastapi_app.py")
        print("   3. Redeploy: git push origin feature/event-driven")
        return False
    else:
        print("✅ CONFIGURACIÓN BÁSICA CORRECTA")
        print("   Si el bot no responde, verificar:")
        print("   • Que el webhook esté configurado correctamente")
        print("   • Que Railway esté ejecutando el proceso correcto")
        print("   • Logs de Railway para errores específicos")
        return True

def main():
    """Función principal"""
    try:
        success = asyncio.run(debug_railway_bot())
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n🛑 Debug cancelado por usuario")
        return 1
    except Exception as e:
        print(f"\n💥 Error fatal durante debug: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
