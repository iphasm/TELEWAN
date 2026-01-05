#!/usr/bin/env python3
"""
Script para verificar que todas las importaciones funcionan correctamente
"""
import sys

def verify_imports():
    """Verificar todas las importaciones críticas"""
    print("🔍 VERIFICANDO IMPORTACIONES CRÍTICAS")
    print("=" * 40)

    imports_to_test = [
        ("fastapi", "FastAPI web framework"),
        ("uvicorn", "ASGI server"),
        ("telegram", "Telegram Bot API"),
        ("aiohttp", "Async HTTP client"),
        ("config", "Configuración local"),
        ("events", "Sistema de eventos"),
        ("bot", "Funciones del bot"),
    ]

    all_good = True

    for module, description in imports_to_test:
        try:
            if module == "events":
                # Verificar importaciones específicas del módulo events
                from events import (
                    event_bus, init_event_bus, shutdown_event_bus,
                    init_event_handlers, shutdown_event_handlers,
                    EventHandlers, event_handlers
                )
                print(f"✅ {module}: {description} - Todas las funciones disponibles")
            elif module == "config":
                from config import Config
                print(f"✅ {module}: {description}")
            else:
                __import__(module)
                print(f"✅ {module}: {description}")
        except ImportError as e:
            print(f"❌ {module}: ERROR - {e}")
            all_good = False

    # Verificar fastapi_app
    try:
        from fastapi_app import create_app
        print("✅ fastapi_app: Aplicación FastAPI")
    except Exception as e:
        print(f"❌ fastapi_app: ERROR - {e}")
        all_good = False

    print("\n" + "=" * 40)
    if all_good:
        print("🎉 TODAS LAS IMPORTACIONES FUNCIONAN CORRECTAMENTE")
        print("🚀 La aplicación debería iniciar sin problemas")
        return True
    else:
        print("❌ HAY ERRORES DE IMPORTACIÓN")
        print("🔧 Revisar dependencias faltantes")
        return False

if __name__ == "__main__":
    success = verify_imports()
    sys.exit(0 if success else 1)
