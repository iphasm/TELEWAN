#!/usr/bin/env python3
"""
Diagnóstico completo del bot de Telegram en Railway
Ejecutar este script en Railway para identificar exactamente qué está fallando
"""

import os
import sys
import requests
import json
import time
import asyncio
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BotDiagnoser:
    def __init__(self):
        self.results = {
            "environment": {},
            "telegram_api": {},
            "webhook": {},
            "application": {},
            "bot_functionality": {}
        }

    def log_section(self, title):
        print(f"\n{'='*60}")
        print(f"🔍 {title.upper()}")
        print('='*60)

    def diagnose_environment(self):
        """Diagnóstico del entorno Railway"""
        self.log_section("ENTORNO RAILWAY")

        env_vars = {
            'TELEGRAM_BOT_TOKEN': 'Token del bot de Telegram',
            'WAVESPEED_API_KEY': 'API key de WaveSpeed',
            'WEBHOOK_URL': 'URL del webhook',
            'USE_WEBHOOK': 'Modo webhook habilitado',
            'PORT': 'Puerto del servidor',
            'RAILWAY_ENVIRONMENT': 'Entorno Railway',
            'RAILWAY_PROJECT_ID': 'ID del proyecto Railway',
            'RAILWAY_STATIC_URL': 'URL estática de Railway'
        }

        self.results["environment"]["railway_detected"] = bool(os.getenv('RAILWAY_ENVIRONMENT'))
        self.results["environment"]["variables"] = {}

        for var, desc in env_vars.items():
            value = os.getenv(var)
            exists = bool(value)

            if var in ['TELEGRAM_BOT_TOKEN', 'WAVESPEED_API_KEY'] and value:
                masked = value[:10] + "***" if len(value) > 10 else value
                print(f"   ✅ {var}: {masked} ({desc})")
            elif var == 'WEBHOOK_URL' and value:
                print(f"   ✅ {var}: {value} ({desc})")
            elif exists:
                print(f"   ✅ {var}: {value} ({desc})")
            else:
                print(f"   ❌ {var}: NO CONFIGURADA ({desc})")

            self.results["environment"]["variables"][var] = exists

        # Verificar si estamos en Railway
        is_railway = os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RAILWAY_PROJECT_ID')
        print(f"\n🚂 ¿Ejecutándose en Railway?: {'✅ SÍ' if is_railway else '❌ NO'}")

        if not is_railway:
            print("⚠️  ADVERTENCIA: Este diagnóstico está diseñado para Railway")
            print("   Para diagnóstico local, algunos tests pueden fallar")

    def diagnose_telegram_api(self):
        """Diagnóstico de la API de Telegram"""
        self.log_section("API DE TELEGRAM")

        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            print("❌ No hay token de Telegram configurado")
            self.results["telegram_api"]["token_configured"] = False
            return

        self.results["telegram_api"]["token_configured"] = True

        try:
            # Test 1: getMe
            print("🔍 Probando conectividad básica (getMe)...")
            response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot_info = data['result']
                    username = bot_info.get('username', 'Unknown')
                    bot_id = bot_info.get('id', 'Unknown')
                    print(f"   ✅ Token válido - Bot: @{username} (ID: {bot_id})")

                    self.results["telegram_api"]["getMe_success"] = True
                    self.results["telegram_api"]["bot_username"] = username
                    self.results["telegram_api"]["bot_id"] = bot_id
                else:
                    print(f"   ❌ Token inválido: {data.get('description', 'Unknown error')}")
                    self.results["telegram_api"]["getMe_success"] = False
                    return
            else:
                print(f"   ❌ Error HTTP {response.status_code}")
                self.results["telegram_api"]["getMe_success"] = False
                return

            # Test 2: getWebhookInfo
            print("🔍 Verificando configuración del webhook...")
            response = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo", timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    webhook_info = data.get('result', {})
                    current_url = webhook_info.get('url', '')
                    pending_updates = webhook_info.get('pending_update_count', 0)
                    last_error_date = webhook_info.get('last_error_date')
                    last_error_message = webhook_info.get('last_error_message')

                    print(f"   URL del webhook actual: {current_url or 'Ninguna'}")
                    print(f"   Updates pendientes: {pending_updates}")

                    if last_error_date:
                        error_time = datetime.fromtimestamp(last_error_date).strftime('%Y-%m-%d %H:%M:%S')
                        print(f"   ❌ Último error: {last_error_message} (at {error_time})")

                    self.results["telegram_api"]["webhook_url"] = current_url
                    self.results["telegram_api"]["pending_updates"] = pending_updates
                    self.results["telegram_api"]["has_webhook"] = bool(current_url)
                    self.results["telegram_api"]["last_error"] = last_error_message if last_error_date else None

                    if current_url:
                        print("   ✅ Webhook configurado en Telegram")
                    else:
                        print("   ❌ NO HAY WEBHOOK CONFIGURADO")
                        print("   💡 El bot no puede recibir mensajes de Telegram")

                    if pending_updates > 0:
                        print(f"   ⚠️  HAY {pending_updates} MENSAJES PENDIENTES")
                        print("   💡 El bot no está procesando las actualizaciones")

                else:
                    print(f"   ❌ Error obteniendo webhook info: {data.get('description')}")
            else:
                print(f"   ❌ Error HTTP {response.status_code}")

        except Exception as e:
            print(f"   ❌ Error conectando a Telegram API: {e}")
            self.results["telegram_api"]["connection_error"] = str(e)

    def diagnose_webhook_endpoint(self):
        """Diagnóstico del endpoint del webhook"""
        self.log_section("ENDPOINT DEL WEBHOOK")

        webhook_url = os.getenv('WEBHOOK_URL')
        if not webhook_url:
            print("❌ WEBHOOK_URL no configurada")
            self.results["webhook"]["url_configured"] = False
            return

        self.results["webhook"]["url_configured"] = True

        # Asegurar HTTPS
        if not webhook_url.startswith('http'):
            webhook_url = f"https://{webhook_url}"

        webhook_endpoint = f"{webhook_url}/webhook"
        health_endpoint = f"{webhook_url}/health"

        print(f"URL del webhook: {webhook_url}")
        print(f"Endpoint del webhook: {webhook_endpoint}")

        # Test 1: Health endpoint
        try:
            print("🔍 Probando endpoint de health...")
            response = requests.get(health_endpoint, timeout=10)

            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                components = data.get('components', {})
                telegram_status = components.get('telegram_bot')

                print(f"   ✅ Health check: {status}")
                print(f"   🤖 Estado del bot: {telegram_status}")

                self.results["webhook"]["health_status"] = status
                self.results["webhook"]["telegram_bot_status"] = telegram_status

                if status == 'healthy' and telegram_status == 'operational':
                    print("   ✅ APLICACIÓN OPERATIVA Y BOT FUNCIONANDO")
                else:
                    print("   ❌ PROBLEMAS EN LA APLICACIÓN O BOT")
                    if status != 'healthy':
                        print(f"   💡 Estado de aplicación: {status}")
                    if telegram_status != 'operational':
                        print(f"   💡 Estado del bot: {telegram_status}")
            else:
                print(f"   ❌ Health check falló: HTTP {response.status_code}")
                print(f"   📄 Respuesta: {response.text[:200]}")
                self.results["webhook"]["health_status"] = f"HTTP {response.status_code}"

        except requests.exceptions.ConnectionError:
            print(f"   ❌ No se puede conectar al endpoint: {health_endpoint}")
            print("   💡 Verificar que la URL del webhook sea correcta")
            print("   💡 Verificar que la aplicación esté ejecutándose")
            self.results["webhook"]["connection_error"] = True

        except Exception as e:
            print(f"   ❌ Error probando endpoint: {e}")
            self.results["webhook"]["test_error"] = str(e)

    def diagnose_application_logs(self):
        """Revisar logs de la aplicación (simulado)"""
        self.log_section("LOGS DE LA APLICACIÓN")

        print("ℹ️  Información sobre logs:")
        print("   • Revisa los logs de Railway Dashboard")
        print("   • Busca mensajes de inicialización del bot")
        print("   • Busca errores de webhook")
        print("   • Verifica que no haya errores de importación")

        # Simular verificación de logs básicos
        try:
            # Intentar importar módulos críticos
            import fastapi
            import telegram
            import uvicorn
            print("   ✅ Módulos críticos importados correctamente")
            self.results["application"]["imports_ok"] = True
        except ImportError as e:
            print(f"   ❌ Error de importación: {e}")
            self.results["application"]["imports_ok"] = False

    def test_bot_functionality(self):
        """Probar funcionalidad básica del bot"""
        self.log_section("FUNCIONALIDAD DEL BOT")

        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            print("❌ No hay token para probar funcionalidad")
            return

        try:
            print("🔍 Probando envío de mensaje de prueba...")

            # Enviar un mensaje al bot mismo (si tenemos el chat ID)
            # Esto es limitado porque no tenemos un chat ID conocido
            print("   ℹ️  Para probar completamente, envía un mensaje al bot desde Telegram")
            print("   ℹ️  Y verifica si aparece en los logs de Railway")

            self.results["bot_functionality"]["test_possible"] = True

        except Exception as e:
            print(f"   ❌ Error en test de funcionalidad: {e}")

    def generate_report(self):
        """Generar reporte completo del diagnóstico"""
        self.log_section("REPORTE FINAL DE DIAGNÓSTICO")

        # Análisis de resultados
        issues = []
        recommendations = []

        # Verificar variables críticas
        if not self.results["environment"]["variables"].get("TELEGRAM_BOT_TOKEN"):
            issues.append("TELEGRAM_BOT_TOKEN no configurada")
            recommendations.append("Configurar TELEGRAM_BOT_TOKEN en Railway Dashboard")

        if not self.results["environment"]["variables"].get("WEBHOOK_URL"):
            issues.append("WEBHOOK_URL no configurada")
            recommendations.append("Configurar WEBHOOK_URL en Railway Dashboard con la URL completa")

        # Verificar Telegram API
        if not self.results["telegram_api"].get("getMe_success", False):
            issues.append("Token de Telegram inválido o problemas de conectividad")
            recommendations.append("Verificar que TELEGRAM_BOT_TOKEN sea correcto")

        if not self.results["telegram_api"].get("has_webhook", False):
            issues.append("No hay webhook configurado en Telegram")
            recommendations.append("El bot no puede recibir mensajes sin webhook")

        if self.results["telegram_api"].get("pending_updates", 0) > 0:
            issues.append(f"{self.results['telegram_api']['pending_updates']} mensajes pendientes")
            recommendations.append("El bot no está procesando actualizaciones")

        # Verificar webhook endpoint
        if self.results["webhook"].get("connection_error"):
            issues.append("No se puede conectar al endpoint del webhook")
            recommendations.append("Verificar que la aplicación esté ejecutándose y la URL sea correcta")

        if self.results["webhook"].get("health_status") != "healthy":
            issues.append("Aplicación no saludable")
            recommendations.append("Revisar logs de Railway para errores de inicialización")

        if self.results["webhook"].get("telegram_bot_status") != "operational":
            issues.append("Bot no inicializado correctamente")
            recommendations.append("Revisar configuración del bot en el código")

        # Reporte final
        if issues:
            print("❌ PROBLEMAS ENCONTRADOS:")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")

            print("\n🔧 RECOMENDACIONES:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        else:
            print("✅ NO SE ENCONTRARON PROBLEMAS CRÍTICOS")
            print("🎉 El bot debería estar funcionando correctamente")

        print(f"\n⏰ Diagnóstico completado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return len(issues) == 0

    async def run_full_diagnosis(self):
        """Ejecutar diagnóstico completo"""
        print("🚀 DIAGNÓSTICO COMPLETO DEL BOT DE TELEGRAM")
        print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🐍 Python: {sys.version.split()[0]}")
        print(f"📁 Directorio: {os.getcwd()}")
        print()

        # Ejecutar diagnósticos
        self.diagnose_environment()
        self.diagnose_telegram_api()
        self.diagnose_webhook_endpoint()
        self.diagnose_application_logs()
        self.test_bot_functionality()

        # Generar reporte
        success = self.generate_report()

        return success

def main():
    """Función principal"""
    diagnoser = BotDiagnoser()

    # Ejecutar diagnóstico asíncrono
    try:
        success = asyncio.run(diagnoser.run_full_diagnosis())
    except Exception as e:
        print(f"❌ Error ejecutando diagnóstico: {e}")
        return 1

    if success:
        print("\n✅ DIAGNÓSTICO COMPLETADO - SIN PROBLEMAS CRÍTICOS")
        return 0
    else:
        print(f"\n❌ DIAGNÓSTICO COMPLETADO - PROBLEMAS ENCONTRADOS")
        return 1

if __name__ == "__main__":
    sys.exit(main())