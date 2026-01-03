#!/usr/bin/env python3
"""
Script de diagnóstico para el bot TELEWAN
Ejecutar en Railway para verificar configuración
"""

import os
import sys
from dotenv import load_dotenv

def main():
    print("🔍 Diagnóstico del Bot TELEWAN")
    print("=" * 40)

    # Verificar Python version
    print(f"🐍 Python version: {sys.version}")
    print()

    # Verificar variables de entorno
    print("🔧 Variables de entorno:")
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    wavespeed_key = os.getenv("WAVESPEED_API_KEY")
    volume_path = os.getenv("VOLUME_PATH", "./storage")

    print(f"  TELEGRAM_BOT_TOKEN: {'✅ Configurado' if telegram_token else '❌ Faltante'}")
    print(f"  WAVESPEED_API_KEY: {'✅ Configurado' if wavespeed_key else '❌ Faltante'}")
    print(f"  VOLUME_PATH: {volume_path}")

    if telegram_token:
        # Mostrar primeros caracteres del token para verificar
        print(f"  Token preview: {telegram_token[:10]}...{telegram_token[-5:]}")

    print()

    # Verificar archivos
    print("📁 Archivos del proyecto:")
    required_files = ['bot.py', 'config.py', 'requirements.txt']
    for file in required_files:
        exists = os.path.exists(file)
        print(f"  {file}: {'✅ Existe' if exists else '❌ Faltante'}")

    print()

    # Verificar directorio de trabajo
    print(f"📍 Directorio actual: {os.getcwd()}")

    # Verificar volumen
    if os.path.exists(volume_path):
        print(f"💾 Volumen: ✅ Montado en {volume_path}")
        try:
            # Intentar escribir un archivo de prueba
            test_file = os.path.join(volume_path, "test_write.txt")
            with open(test_file, 'w') as f:
                f.write("Test write successful")
            os.remove(test_file)
            print("💾 Permisos de escritura: ✅ OK"        except Exception as e:
            print(f"💾 Permisos de escritura: ❌ Error - {e}")
    else:
        print(f"💾 Volumen: ❌ No encontrado en {volume_path}")

    print()

    # Verificar imports
    print("📦 Verificando imports:")
    try:
        import telegram
        print("  python-telegram-bot: ✅ OK")
    except ImportError:
        print("  python-telegram-bot: ❌ Faltante")

    try:
        import requests
        print("  requests: ✅ OK")
    except ImportError:
        print("  requests: ❌ Faltante")

    try:
        from PIL import Image
        print("  PIL/Pillow: ✅ OK")
    except ImportError:
        print("  PIL/Pillow: ❌ Faltante")

    try:
        from dotenv import load_dotenv
        print("  python-dotenv: ✅ OK")
    except ImportError:
        print("  python-dotenv: ❌ Faltante")

    print()
    print("🎯 Recomendaciones:")

    if not telegram_token:
        print("  - Configurar TELEGRAM_BOT_TOKEN en Railway")
    if not wavespeed_key:
        print("  - Configurar WAVESPEED_API_KEY en Railway")
    if not os.path.exists(volume_path):
        print("  - Verificar que el volumen esté montado correctamente")

    print()
    print("✅ Diagnóstico completado")

if __name__ == "__main__":
    main()


