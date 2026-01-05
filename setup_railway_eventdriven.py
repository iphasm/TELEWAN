#!/usr/bin/env python3
"""
Setup script for Railway Event-Driven Bot
Configura las variables de entorno necesarias para el bot event-driven
"""
import os
import sys
from pathlib import Path

def setup_railway_env():
    """Configura las variables de entorno para Railway"""

    print("🚀 Configuración del Bot TELEWAN para Railway (Event-Driven)")
    print("=" * 60)

    # Verificar si ya existe .env
    env_file = Path('.env')
    if env_file.exists():
        print("⚠️  Archivo .env encontrado. Respaldando...")
        backup_file = Path('.env.backup')
        if backup_file.exists():
            backup_file.unlink()
        env_file.rename(backup_file)
        print("✅ Backup creado: .env.backup")

    # Variables requeridas
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'WAVESPEED_API_KEY'
    ]

    # Variables opcionales con valores por defecto
    optional_vars = {
        'USE_WEBHOOK': 'true',
        'WEBHOOK_PATH': '/webhook',
        'WEBHOOK_PORT': '8080',
        'ALLOWED_USER_ID': '',  # Vacío = permite a todos
        'DEFAULT_MODEL': 'ultra_fast',
        'VOLUME_PATH': './storage'
    }

    print("\n📝 Variables requeridas:")
    env_content = []

    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: Configurada")
            env_content.append(f"{var}={value}")
        else:
            print(f"❌ {var}: NO CONFIGURADA")
            print(f"   ℹ️  Configure esta variable en Railway Dashboard")
            env_content.append(f"{var}=tu_{var.lower()}_aqui")

    print("\n📋 Variables opcionales (con valores por defecto):")
    for var, default in optional_vars.items():
        value = os.getenv(var, default)
        print(f"✅ {var}: {value}")
        env_content.append(f"{var}={value}")

    # Variables adicionales para Railway
    railway_vars = {
        'REDIS_URL': 'redis://localhost:6379',  # Railway proporciona Redis
        'WEBHOOK_SECRET_TOKEN': '',  # Opcional para seguridad adicional
    }

    print("\n🔧 Variables específicas de Railway:")
    for var, default in railway_vars.items():
        value = os.getenv(var, default)
        if var == 'REDIS_URL' and not value.startswith('redis://'):
            print(f"⚠️  {var}: Railway debería proporcionar Redis automáticamente")
        else:
            print(f"✅ {var}: {'Configurada' if value != default else 'Usando default'}")
        env_content.append(f"{var}={value}")

    # Crear archivo .env
    print("\n💾 Creando archivo .env...")
    with open('.env', 'w', encoding='utf-8') as f:
        f.write("# Configuración para TELEWAN Bot (Event-Driven Architecture)\n")
        f.write("# Generado automáticamente por setup_railway_eventdriven.py\n\n")
        f.write("# Variables requeridas - CONFIGURAR EN RAILWAY DASHBOARD\n")
        for var in required_vars:
            f.write(f"{var}=tu_{var.lower()}_aqui\n")
        f.write("\n# Variables opcionales\n")
        for var, default in optional_vars.items():
            f.write(f"{var}={default}\n")
        f.write("\n# Variables específicas de Railway\n")
        for var, default in railway_vars.items():
            f.write(f"{var}={default}\n")

    print("✅ Archivo .env creado")

    # Verificar dependencias
    print("\n🔍 Verificando dependencias...")
    try:
        import fastapi
        import uvicorn
        import aiohttp
        import redis
        print("✅ Todas las dependencias instaladas")
    except ImportError as e:
        print(f"❌ Dependencia faltante: {e}")
        print("Ejecuta: pip install -r requirements.txt")
        return False

    # Verificar configuración
    print("\n⚙️  Verificando configuración...")
    try:
        from config import Config
        Config.validate()
        print("✅ Configuración válida")
    except ValueError as e:
        print(f"❌ Error de configuración: {e}")
        return False

    # Mostrar instrucciones finales
    print("\n" + "=" * 60)
    print("🎯 CONFIGURACIÓN COMPLETA")
    print("=" * 60)
    print()
    print("Para completar la configuración:")
    print()
    print("1. 🚀 Despliega en Railway:")
    print("   git push origin feature/event-driven")
    print()
    print("2. ⚙️  Configura variables en Railway Dashboard:")
    print("   - TELEGRAM_BOT_TOKEN: Tu token de @BotFather")
    print("   - WAVESPEED_API_KEY: Tu API key de WaveSpeed")
    print("   - WEBHOOK_URL: URL proporcionada por Railway")
    print()
    print("3. 🎮 El bot responderá automáticamente a:")
    print("   - /start, /help, /models")
    print("   - /optimize, /preview, /quality")
    print("   - Imágenes con captions")
    print()
    print("4. 📊 Monitoreo disponible en:")
    print("   - /health: Estado del sistema")
    print("   - /stats: Estadísticas de uso")
    print()
    print("✅ ¡Bot listo para usar!")
    print()

    return True

if __name__ == "__main__":
    success = setup_railway_env()
    if not success:
        sys.exit(1)
