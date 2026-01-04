#!/usr/bin/env python3
"""
Script de prueba local para webhooks
Configura variables de entorno locales para testing
"""

import os
import sys

def setup_local_env():
    """Configura variables de entorno locales para testing"""

    print("🔧 Configuración de entorno local para testing de webhooks")
    print("=" * 60)

    # Solicitar valores al usuario
    print("\nIngresa tus configuraciones (presiona Enter para usar valores de ejemplo):")

    telegram_token = input("TELEGRAM_BOT_TOKEN: ").strip() or "TU_TOKEN_AQUI"
    webhook_url = input("WEBHOOK_URL (ej: https://tu-proyecto.railway.app): ").strip() or "https://example.railway.app"
    webhook_path = input("WEBHOOK_PATH (default: /webhook): ").strip() or "/webhook"
    secret_token = input("WEBHOOK_SECRET_TOKEN (opcional): ").strip() or ""

    # Crear archivo .env local para testing
    env_content = f"""# Configuración local para testing de webhooks
TELEGRAM_BOT_TOKEN={telegram_token}
WEBHOOK_URL={webhook_url}
WEBHOOK_PATH={webhook_path}
WEBHOOK_PORT=8443
USE_WEBHOOK=true
"""

    if secret_token:
        env_content += f"WEBHOOK_SECRET_TOKEN={secret_token}\n"

    # Agregar otras variables necesarias para testing
    env_content += """
# Otras configuraciones para testing
WAVESPEED_API_KEY=test_key
ALLOWED_USER_ID=
VOLUME_PATH=./storage
"""

    with open('.env.local', 'w') as f:
        f.write(env_content)

    print("
✅ Archivo .env.local creado con configuración de testing"    print("📄 Contenido del archivo:"    print("-" * 40)
    print(env_content)

    print("\n📋 Para usar en Railway, ejecuta estos comandos:")
    print("-" * 50)
    print(f"railway variables set TELEGRAM_BOT_TOKEN={telegram_token}")
    print(f"railway variables set WEBHOOK_URL={webhook_url}")
    print(f"railway variables set WEBHOOK_PATH={webhook_path}")
    print("railway variables set WEBHOOK_PORT=8443"
    print("railway variables set USE_WEBHOOK=true")
    if secret_token:
        print(f"railway variables set WEBHOOK_SECRET_TOKEN={secret_token}")
    print("
railway deploy"    print("
railway run python setup_webhook.py setup"

def test_webhook_locally():
    """Prueba la configuración local"""

    print("🧪 Probando configuración local...")

    # Cargar variables del archivo .env.local
    if os.path.exists('.env.local'):
        from dotenv import load_dotenv
        load_dotenv('.env.local')
        print("✅ Variables cargadas desde .env.local")
    else:
        print("❌ Archivo .env.local no encontrado. Ejecuta primero: python test_webhook_local.py setup")
        return

    # Importar y ejecutar el script de setup
    print("\n🚀 Ejecutando setup_webhook.py con configuración local...")
    os.system("python setup_webhook.py check")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        setup_local_env()
    else:
        print("🔧 Test de Webhooks Local para TELEWAN")
        print("=" * 45)
        print("Comandos:")
        print("  setup  - Configurar entorno local")
        print("  test   - Probar configuración")
        print()
        print("Ejemplos:")
        print("  python test_webhook_local.py setup")
        print("  python test_webhook_local.py test")

if __name__ == "__main__":
    main()


