#!/usr/bin/env python3
"""
Auditoría completa del bot TELEWAN
Identifica problemas de configuración, código y dependencias
"""
import os
import sys
import logging
import importlib.util
from typing import List, Dict

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class BotAuditor:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.info = []

    def add_issue(self, issue: str, severity: str = "ERROR"):
        """Agregar un problema encontrado"""
        if severity.upper() == "ERROR":
            self.issues.append(issue)
        elif severity.upper() == "WARNING":
            self.warnings.append(issue)
        else:
            self.info.append(issue)

    def audit_environment_variables(self):
        """Auditar variables de entorno requeridas"""
        logger.info("🔍 Auditando variables de entorno...")

        # Variables críticas
        critical_vars = ['TELEGRAM_BOT_TOKEN', 'WAVESPEED_API_KEY']
        for var in critical_vars:
            value = os.getenv(var)
            if not value:
                self.add_issue(f"Variable de entorno crítica faltante: {var}")
            else:
                self.info.append(f"✅ {var}: Configurada")

        # Variables opcionales
        optional_vars = ['ALLOWED_USER_ID', 'DEFAULT_MODEL', 'WEBHOOK_URL', 'WEBHOOK_SECRET_TOKEN']
        for var in optional_vars:
            value = os.getenv(var)
            if value:
                self.info.append(f"ℹ️  {var}: {value}")
            else:
                self.info.append(f"ℹ️  {var}: No configurada (opcional)")

    def audit_imports(self):
        """Auditar importaciones y dependencias"""
        logger.info("🔍 Auditando importaciones...")

        try:
            # Intentar importar módulos críticos
            import telegram
            self.info.append(f"✅ python-telegram-bot: {telegram.__version__}")
        except ImportError as e:
            self.add_issue(f"Dependencia faltante: python-telegram-bot - {e}")

        try:
            import requests
            self.info.append(f"✅ requests: OK")
        except ImportError as e:
            self.add_issue(f"Dependencia faltante: requests - {e}")

        try:
            import PIL
            self.info.append(f"✅ PIL/Pillow: OK")
        except ImportError as e:
            self.add_issue(f"Dependencia faltante: PIL/Pillow - {e}")

        try:
            import dotenv
            self.info.append(f"✅ python-dotenv: OK")
        except ImportError as e:
            self.add_issue(f"Dependencia faltante: python-dotenv - {e}")

        # Flask solo si se usa webhooks
        use_webhook = os.getenv('USE_WEBHOOK', 'false').lower() == 'true'
        if use_webhook:
            try:
                import flask
                self.info.append(f"✅ Flask: OK (requerido para webhooks)")
            except ImportError as e:
                self.add_issue(f"Dependencia faltante para webhooks: Flask - {e}")

    def audit_code_structure(self):
        """Auditar estructura del código"""
        logger.info("🔍 Auditando estructura del código...")

        try:
            # Importar config
            from config import Config
            self.info.append("✅ config.py: Importable")

            # Validar configuración
            try:
                Config.validate()
                self.info.append("✅ Configuración: Válida")
            except ValueError as e:
                self.add_issue(f"Configuración inválida: {e}")

        except ImportError as e:
            self.add_issue(f"No se puede importar config: {e}")

        # Verificar sintaxis del bot principal
        try:
            import py_compile
            py_compile.compile('bot.py', doraise=True)
            self.info.append("✅ bot.py: Sintaxis correcta")
        except py_compile.PyCompileError as e:
            self.add_issue(f"Error de sintaxis en bot.py: {e}")

        # Verificar funciones críticas
        try:
            from bot import main, handle_image_message, WavespeedAPI
            self.info.append("✅ Funciones críticas: Importables")
        except ImportError as e:
            self.add_issue(f"Función crítica no importable: {e}")

    def audit_filters(self):
        """Auditar filtros personalizados"""
        logger.info("🔍 Auditando filtros personalizados...")

        try:
            from bot import image_document_filter, static_sticker_filter
            self.info.append("✅ Filtros personalizados: Definidos correctamente")
        except ImportError as e:
            self.add_issue(f"Error en filtros personalizados: {e}")

    def audit_api_connectivity(self):
        """Auditar conectividad con APIs externas"""
        logger.info("🔍 Auditando conectividad con APIs...")

        # Solo si las claves están configuradas
        wavespeed_key = os.getenv('WAVESPEED_API_KEY')
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')

        if wavespeed_key:
            try:
                import requests
                # Intentar un request básico a Wavespeed
                headers = {'Authorization': f'Bearer {wavespeed_key}'}
                response = requests.get('https://api.wavespeed.ai/api/v3/wavespeed-ai/models',
                                      headers=headers, timeout=5)
                if response.status_code == 200:
                    self.info.append("✅ Wavespeed API: Conectividad OK")
                else:
                    self.add_issue(f"Wavespeed API: Error HTTP {response.status_code}")
            except Exception as e:
                self.add_issue(f"Wavespeed API: Error de conectividad - {e}")
        else:
            self.add_issue("Wavespeed API: No se puede probar (API_KEY faltante)")

        if telegram_token:
            try:
                import requests
                response = requests.get(f'https://api.telegram.org/bot{telegram_token}/getMe', timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('ok'):
                        bot_name = data.get('result', {}).get('username', 'Unknown')
                        self.info.append(f"✅ Telegram Bot API: Conectividad OK (@{bot_name})")
                    else:
                        self.add_issue("Telegram Bot API: Token inválido")
                else:
                    self.add_issue(f"Telegram Bot API: Error HTTP {response.status_code}")
            except Exception as e:
                self.add_issue(f"Telegram Bot API: Error de conectividad - {e}")
        else:
            self.add_issue("Telegram Bot API: No se puede probar (TOKEN faltante)")

    def audit_file_structure(self):
        """Auditar estructura de archivos"""
        logger.info("🔍 Auditando estructura de archivos...")

        required_files = ['bot.py', 'config.py', 'README.md', '.env.example']
        for file in required_files:
            if os.path.exists(file):
                self.info.append(f"✅ {file}: Existe")
            else:
                self.add_issue(f"Archivo requerido faltante: {file}")

        # Verificar directorios
        if os.path.exists('storage') or os.getenv('VOLUME_PATH'):
            self.info.append("✅ Directorio de almacenamiento: OK")
        else:
            self.warnings.append("Directorio de almacenamiento no encontrado (se creará automáticamente)")

    def run_full_audit(self):
        """Ejecutar auditoría completa"""
        logger.info("🚀 Iniciando auditoría completa del bot TELEWAN")
        logger.info("=" * 60)

        self.audit_environment_variables()
        print()
        self.audit_imports()
        print()
        self.audit_code_structure()
        print()
        self.audit_filters()
        print()
        self.audit_api_connectivity()
        print()
        self.audit_file_structure()
        print()

        # Mostrar resultados
        self.show_results()

    def show_results(self):
        """Mostrar resultados de la auditoría"""
        print("=" * 60)
        print("📊 RESULTADOS DE LA AUDITORÍA")
        print("=" * 60)

        if self.issues:
            print(f"\n❌ PROBLEMAS CRÍTICOS ({len(self.issues)}):")
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. {issue}")

        if self.warnings:
            print(f"\n⚠️  ADVERTENCIAS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")

        if self.info:
            print(f"\nℹ️  INFORMACIÓN ({len(self.info)}):")
            for i, info in enumerate(self.info, 1):
                print(f"  {i}. {info}")

        print("\n" + "=" * 60)

        # Resumen
        total_issues = len(self.issues) + len(self.warnings)
        if total_issues == 0:
            print("✅ AUDITORÍA EXITOSA: No se encontraron problemas críticos")
            print("🎉 El bot está listo para funcionar correctamente")
        else:
            print(f"⚠️  AUDITORÍA COMPLETADA: {len(self.issues)} problemas críticos, {len(self.warnings)} advertencias")
            if self.issues:
                print("🚫 Los problemas críticos deben resolverse antes de ejecutar el bot")

def main():
    auditor = BotAuditor()
    auditor.run_full_audit()

if __name__ == "__main__":
    main()
