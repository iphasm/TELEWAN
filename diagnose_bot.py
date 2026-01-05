#!/usr/bin/env python3
"""
Script de diagnóstico para TELEWAN Bot
Ayuda a identificar por qué el bot no responde
"""
import os
import sys
import asyncio
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def diagnose_bot():
    """Diagnóstico completo del bot"""
    print("🔍 DIAGNÓSTICO DEL BOT TELEWAN")
    print("=" * 50)

    issues = []
    warnings = []

    # 1. Verificar variables de entorno críticas
    print("\n📋 1. Variables de Entorno:")
    required_vars = ['TELEGRAM_BOT_TOKEN', 'WAVESPEED_API_KEY']
    for var in required_vars:
        value = os.getenv(var)
        if value:
            masked = value[:10] + "..." if len(value) > 10 else value
            print(f"   ✅ {var}: {masked}")
        else:
            print(f"   ❌ {var}: NO CONFIGURADA")
            issues.append(f"Variable {var} no configurada")

    # 2. Verificar modo de operación
    print("\n📋 2. Modo de Operación:")
    use_webhook = os.getenv('USE_WEBHOOK', 'false').lower() == 'true'
    webhook_url = os.getenv('WEBHOOK_URL')
    webhook_port = os.getenv('WEBHOOK_PORT', '8080')

    print(f"   📡 USE_WEBHOOK: {use_webhook}")
    print(f"   🌐 WEBHOOK_URL: {webhook_url or 'No configurada'}")
    print(f"   🔌 WEBHOOK_PORT: {webhook_port}")

    if use_webhook and not webhook_url:
        issues.append("USE_WEBHOOK=true pero WEBHOOK_URL no configurada")

    # 3. Verificar archivos
    print("\n📋 3. Archivos del Sistema:")
    required_files = [
        'fastapi_app.py',
        'bot.py',
        'config.py',
        'requirements.txt'
    ]

    for file in required_files:
        if Path(file).exists():
            print(f"   ✅ {file}: Existe")
        else:
            print(f"   ❌ {file}: NO ENCONTRADO")
            issues.append(f"Archivo {file} no encontrado")

    # 4. Verificar Procfile
    print("\n📋 4. Configuración de Railway:")
    procfile = Path('Procfile')
    if procfile.exists():
        content = procfile.read_text().strip()
        print(f"   📄 Procfile: {content}")
        if 'fastapi_app.py' in content:
            print("   ✅ Procfile apunta a FastAPI")
        else:
            print("   ⚠️  Procfile NO apunta a FastAPI")
            warnings.append("Procfile no apunta a fastapi_app.py")
    else:
        print("   ❌ Procfile: NO ENCONTRADO")
        issues.append("Procfile no encontrado")

    # 5. Verificar dependencias
    print("\n📋 5. Dependencias:")
    try:
        import fastapi
        import uvicorn
        import aiohttp
        import telegram
        print("   ✅ Dependencias críticas instaladas")
    except ImportError as e:
        print(f"   ❌ Dependencia faltante: {e}")
        issues.append(f"Dependencia faltante: {e}")

    # 6. Verificar conectividad con Telegram (si token disponible)
    print("\n📋 6. Conectividad:")
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if token:
        try:
            import telegram
            bot = telegram.Bot(token=token)
            # Intentar obtener info del bot (síncrono para diagnóstico)
            import requests
            response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot_username = data['result'].get('username', 'Unknown')
                    print(f"   ✅ Telegram API: Conectado (@{bot_username})")
                else:
                    print("   ❌ Telegram API: Token inválido")
                    issues.append("Token de Telegram inválido")
            else:
                print(f"   ❌ Telegram API: Error HTTP {response.status_code}")
                issues.append(f"Error conectando a Telegram API: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Telegram API: Error de conexión - {e}")
            issues.append(f"Error conectando a Telegram: {e}")
    else:
        print("   ⚠️  Telegram: No se puede verificar (sin token)")

    # 7. Verificar WaveSpeed API
    api_key = os.getenv('WAVESPEED_API_KEY')
    if api_key:
        try:
            import requests
            headers = {'Authorization': f'Bearer {api_key}'}
            response = requests.get('https://api.wavespeed.ai/api/v3/wavespeed-ai/models',
                                  headers=headers, timeout=5)
            if response.status_code == 200:
                print("   ✅ WaveSpeed API: Conectado")
            else:
                print(f"   ❌ WaveSpeed API: Error HTTP {response.status_code}")
                issues.append(f"Error conectando a WaveSpeed API: {response.status_code}")
        except Exception as e:
            print(f"   ❌ WaveSpeed API: Error de conexión - {e}")
            issues.append(f"Error conectando a WaveSpeed: {e}")
    else:
        print("   ⚠️  WaveSpeed: No se puede verificar (sin API key)")

    # 8. Verificar configuración de webhook actual
    print("\n📋 7. Estado del Webhook:")
    if token:
        try:
            import requests
            response = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    webhook_info = data.get('result', {})
                    webhook_url = webhook_info.get('url', '')
                    if webhook_url:
                        print(f"   📡 Webhook configurado: {webhook_url}")
                        if 'railway.app' in webhook_url:
                            print("   ✅ Webhook apunta a Railway")
                        else:
                            print("   ⚠️  Webhook NO apunta a Railway")
                            warnings.append("Webhook no apunta a Railway")
                    else:
                        print("   ❌ Webhook NO configurado")
                        issues.append("Webhook no configurado en Telegram")
                else:
                    print("   ❌ Error obteniendo info del webhook")
            else:
                print(f"   ❌ Error HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error verificando webhook: {e}")
    else:
        print("   ⚠️  Webhook: No se puede verificar (sin token)")

    # Resultados finales
    print("\n" + "=" * 50)
    print("📊 RESULTADOS DEL DIAGNÓSTICO")
    print("=" * 50)

    if issues:
        print(f"\n❌ PROBLEMAS CRÍTICOS ({len(issues)}):")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")

    if warnings:
        print(f"\n⚠️  ADVERTENCIAS ({len(warnings)}):")
        for i, warning in enumerate(warnings, 1):
            print(f"   {i}. {warning}")

    if not issues and not warnings:
        print("\n✅ DIAGNÓSTICO EXITOSO")
        print("   El bot debería funcionar correctamente")
        return True

    # Recomendaciones
    print("\n🔧 RECOMENDACIONES:")
    if 'fastapi_app.py' not in str(Path('Procfile').read_text()) if Path('Procfile').exists() else True:
        print("   1. Cambiar Procfile: web: python fastapi_app.py")
    if not os.getenv('TELEGRAM_BOT_TOKEN'):
        print("   2. Configurar TELEGRAM_BOT_TOKEN en Railway")
    if not os.getenv('WAVESPEED_API_KEY'):
        print("   3. Configurar WAVESPEED_API_KEY en Railway")
    if use_webhook and not webhook_url:
        print("   4. Configurar WEBHOOK_URL en Railway (la URL de tu app)")

    print("   5. Redeploy: git push origin feature/event-driven")

    return len(issues) == 0

def main():
    """Función principal"""
    try:
        success = asyncio.run(diagnose_bot())
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n🛑 Diagnóstico cancelado")
        return 1
    except Exception as e:
        print(f"\n💥 Error durante diagnóstico: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
