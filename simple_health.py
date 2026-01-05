#!/usr/bin/env python3
"""
Health check simple para diagnosticar problemas en Railway
"""
import os
import sys

def simple_health():
    """Verificación simple sin async"""
    print("🏥 SIMPLE HEALTH CHECK")
    print("=" * 30)

    # Verificar Python version
    print(f"🐍 Python: {sys.version}")

    # Verificar variables críticas
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    api_key = os.getenv('WAVESPEED_API_KEY')

    print(f"🤖 Token: {'✅' if token else '❌'}")
    print(f"🔑 API Key: {'✅' if api_key else '❌'}")

    # Verificar imports básicos
    try:
        import fastapi
        print("✅ FastAPI importable")
    except ImportError as e:
        print(f"❌ FastAPI no disponible: {e}")
        return False

    try:
        import uvicorn
        print("✅ Uvicorn importable")
    except ImportError as e:
        print(f"❌ Uvicorn no disponible: {e}")
        return False

    # Verificar config
    try:
        from config import Config
        Config.validate()
        print("✅ Configuración válida")
    except Exception as e:
        print(f"❌ Error de configuración: {e}")
        return False

    print("✅ Health check básico PASSED")
    return True

if __name__ == "__main__":
    success = simple_health()
    print("\nSi este script funciona pero Railway falla,")
    print("el problema está en la inicialización de FastAPI.")
    sys.exit(0 if success else 1)
