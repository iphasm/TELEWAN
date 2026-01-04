#!/usr/bin/env python3
"""
Script de verificación rápida del bot TELEWAN
Ejecutar después de correcciones para verificar funcionamiento básico
"""

import os
import sys

def main():
    print("🔍 Verificación rápida del Bot TELEWAN")
    print("=" * 45)

    # Verificar imports básicos
    print("📦 Verificando imports básicos...")
    try:
        import telegram
        print("✅ python-telegram-bot")
    except ImportError as e:
        print(f"❌ python-telegram-bot: {e}")
        return False

    try:
        import requests
        print("✅ requests")
    except ImportError as e:
        print(f"❌ requests: {e}")
        return False

    try:
        from PIL import Image
        print("✅ PIL/Pillow")
    except ImportError as e:
        print(f"❌ PIL/Pillow: {e}")
        return False

    # Verificar sintaxis del bot.py
    print("\n🔧 Verificando sintaxis de bot.py...")
    try:
        with open('bot.py', 'r', encoding='utf-8') as f:
            code = f.read()
        compile(code, 'bot.py', 'exec')
        print("✅ Sintaxis correcta")
    except SyntaxError as e:
        print(f"❌ Error de sintaxis: {e}")
        return False
    except FileNotFoundError:
        print("❌ Archivo bot.py no encontrado")
        return False

    # Verificar variables de entorno
    print("\n🔐 Verificando configuración...")
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    api_key = os.getenv('WAVESPEED_API_KEY')

    if token:
        print("✅ TELEGRAM_BOT_TOKEN configurado")
    else:
        print("⚠️  TELEGRAM_BOT_TOKEN no configurado")

    if api_key:
        print("✅ WAVESPEED_API_KEY configurado")
    else:
        print("⚠️  WAVESPEED_API_KEY no configurado")

    # Verificar funciones principales existen
    print("\n🎯 Verificando funciones principales...")
    try:
        exec("from bot import generate_serial_filename, ensure_storage_directory")
        print("✅ Funciones de almacenamiento disponibles")
    except Exception as e:
        print(f"❌ Error en funciones: {e}")
        return False

    print("\n🎉 Verificación completada exitosamente!")
    print("El bot debería funcionar correctamente ahora.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)



