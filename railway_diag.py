#!/usr/bin/env python3
"""
Diagnóstico específico para Railway - ejecutar en logs de Railway
"""
import os
import sys
import asyncio

async def railway_diagnostic():
    """Diagnóstico completo para Railway"""
    print("🚂 RAILWAY DIAGNOSTIC - TELEWAN BOT")
    print("=" * 50)

    # 1. Información del entorno
    print("📋 1. ENTORNO RAILWAY:")
    print(f"   🐍 Python: {sys.version}")
    print(f"   📁 PWD: {os.getcwd()}")
    print(f"   👤 USER: {os.getenv('USER', 'unknown')}")
    print(f"   🏠 HOME: {os.getenv('HOME', 'unknown')}")
    print(f"   🚂 RAILWAY_PROJECT_ID: {os.getenv('RAILWAY_PROJECT_ID', 'not set')}")
    print(f"   🔌 PORT: {os.getenv('PORT', 'not set')}")

    # 2. Variables críticas
    print("\n📋 2. VARIABLES DE ENTORNO:")
    critical_vars = {
        'TELEGRAM_BOT_TOKEN': 'Bot token',
        'WAVESPEED_API_KEY': 'WaveSpeed API',
        'WEBHOOK_URL': 'URL del webhook',
        'USE_WEBHOOK': 'Modo webhook',
        'PORT': 'Puerto Railway'
    }

    for var, description in critical_vars.items():
        value = os.getenv(var)
        if value:
            if var in ['TELEGRAM_BOT_TOKEN', 'WAVESPEED_API_KEY']:
                masked = value[:10] + "..." + value[-5:] if len(value) > 15 else value
            else:
                masked = value
            print(f"   ✅ {var}: {masked}")
        else:
            print(f"   ❌ {var}: NO CONFIGURADO - {description}")

    # 3. Verificar archivos
    print("\n📋 3. ARCHIVOS:")
    files_to_check = [
        'fastapi_app.py',
        'Procfile',
        'requirements.txt',
        'config.py'
    ]

    for file in files_to_check:
        exists = os.path.exists(file)
        size = os.path.getsize(file) if exists else 0
        status = "✅" if exists else "❌"
        print(f"   {status} {file}: {'SI' if exists else 'NO'} ({size} bytes)")

    # 4. Verificar Procfile
    print("\n📋 4. PROCESO DE EJECUCIÓN:")
    if os.path.exists('Procfile'):
        with open('Procfile', 'r') as f:
            procfile_content = f.read().strip()
        print(f"   📄 Procfile: {procfile_content}")

        expected = "web: python fastapi_app.py"
        if procfile_content == expected:
            print("   ✅ Procfile correcto")
        else:
            print(f"   ⚠️  Procfile incorrecto - esperado: {expected}")
    else:
        print("   ❌ Procfile no encontrado")

    # 5. Verificar imports críticos
    print("\n📋 5. IMPORTS CRÍTICOS:")
    imports_to_check = [
        ('fastapi', 'FastAPI web framework'),
        ('uvicorn', 'ASGI server'),
        ('aiohttp', 'Async HTTP client'),
        ('telegram', 'Telegram Bot API'),
        ('config', 'Configuración local')
    ]

    for module, description in imports_to_check.items():
        try:
            if module == 'config':
                from config import Config
                print(f"   ✅ {module}: {description}")
            else:
                __import__(module)
                print(f"   ✅ {module}: {description}")
        except ImportError as e:
            print(f"   ❌ {module}: ERROR - {e}")

    # 6. Verificar configuración
    print("\n📋 6. CONFIGURACIÓN:")
    try:
        from config import Config
        token_ok = bool(Config.TELEGRAM_BOT_TOKEN)
        api_ok = bool(Config.WAVESPEED_API_KEY)
        webhook_ok = bool(Config.WEBHOOK_URL)

        print(f"   🤖 Token configurado: {'✅' if token_ok else '❌'}")
        print(f"   🔑 API key configurada: {'✅' if api_ok else '❌'}")
        print(f"   📡 Webhook URL: {Config.WEBHOOK_URL or '❌ NO CONFIGURADA'}")
        print(f"   🔄 Modo webhook: {Config.USE_WEBHOOK}")

        if token_ok and api_ok:
            print("   ✅ Configuración básica OK")
        else:
            print("   ❌ Configuración INCOMPLETA")

    except Exception as e:
        print(f"   ❌ Error cargando configuración: {e}")

    # 7. Test básico de FastAPI
    print("\n📋 7. TEST FASTAPI:")
    try:
        from fastapi_app import create_app
        app = create_app()
        print("   ✅ FastAPI app creada correctamente")
        print("   🎯 Aplicación debería iniciar correctamente")
    except Exception as e:
        print(f"   ❌ Error creando FastAPI app: {e}")
        print("   💥 Este es el problema más probable")

    # 8. Diagnóstico final
    print("\n" + "=" * 50)
    print("🎯 DIAGNÓSTICO FINAL:")
    print("=" * 50)

    issues = []

    if not os.getenv('TELEGRAM_BOT_TOKEN'):
        issues.append("TELEGRAM_BOT_TOKEN no configurado en Railway")

    if not os.getenv('WAVESPEED_API_KEY'):
        issues.append("WAVESPEED_API_KEY no configurado en Railway")

    if not os.path.exists('fastapi_app.py'):
        issues.append("fastapi_app.py no encontrado")

    if os.path.exists('Procfile'):
        with open('Procfile', 'r') as f:
            if 'fastapi_app.py' not in f.read():
                issues.append("Procfile no apunta a fastapi_app.py")

    if issues:
        print("❌ PROBLEMAS CRÍTICOS:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")

        print("\n🔧 SOLUCIONES:")
        print("   1. Configurar variables de entorno en Railway Dashboard")
        print("   2. Verificar que Procfile sea: web: python fastapi_app.py")
        print("   3. Redeploy: git push origin feature/event-driven")
        print("   4. Revisar logs de Railway para errores específicos")

        return False
    else:
        print("✅ CONFIGURACIÓN CORRECTA")
        print("   Si Railway falla, revisar:")
        print("   • Logs detallados de Railway")
        print("   • Conectividad de red desde Railway")
        print("   • Límites de Railway (CPU/memoria)")
        print("   • Variables de entorno correctas")

        return True

if __name__ == "__main__":
    success = asyncio.run(railway_diagnostic())
    print(f"\n🚂 Railway diagnostic: {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
