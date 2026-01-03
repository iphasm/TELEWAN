#!/usr/bin/env python3
"""
Script de diagnóstico rápido para healthcheck
Ejecutar en Railway: railway run python debug_healthcheck.py
"""

import os
import requests
import subprocess
import sys

def check_environment():
    """Verificar variables de entorno"""
    print("🔧 Verificando configuración...")

    vars_to_check = [
        'USE_WEBHOOK',
        'WEBHOOK_URL',
        'WEBHOOK_PORT',
        'WEBHOOK_PATH',
        'TELEGRAM_BOT_TOKEN'
    ]

    for var in vars_to_check:
        value = os.getenv(var)
        if value:
            if 'TOKEN' in var:
                print(f"✅ {var}: {value[:10]}...{value[-5:]}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: No configurado")

def test_flask_basic():
    """Probar que Flask puede importarse y ejecutarse"""
    print("\n🏥 Probando Flask básico...")

    try:
        from flask import Flask, jsonify
        from datetime import datetime

        app = Flask(__name__)

        @app.route('/', methods=['GET'])
        def healthcheck():
            return jsonify({
                "status": "healthy",
                "service": "TELEWAN Bot",
                "timestamp": datetime.now().isoformat()
            }), 200

        print("✅ Flask importado correctamente")
        print("✅ Endpoint de healthcheck creado")

        # Intentar bind al puerto
        port = int(os.getenv('WEBHOOK_PORT', '8443'))
        try:
            # Solo probar que puede hacer bind, no ejecutar
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('0.0.0.0', port))
            sock.close()
            print(f"✅ Puerto {port} disponible")
        except OSError as e:
            print(f"❌ Error con puerto {port}: {e}")

        return True

    except ImportError as e:
        print(f"❌ Error importando Flask: {e}")
        return False

def test_network():
    """Probar conectividad de red"""
    print("\n🌐 Probando conectividad...")

    try:
        # Probar conexión a Telegram API
        response = requests.get("https://api.telegram.org/bot123/test", timeout=5)
        print("✅ Conectividad a internet OK")
    except:
        print("❌ Problemas de conectividad")

def check_processes():
    """Verificar procesos corriendo"""
    print("\n🔍 Verificando procesos...")

    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=10)
        python_processes = [line for line in result.stdout.split('\n') if 'python' in line.lower()]

        if python_processes:
            print(f"✅ Procesos Python encontrados: {len(python_processes)}")
            for proc in python_processes[:3]:  # Mostrar primeros 3
                print(f"   {proc.strip()[:80]}...")
        else:
            print("❌ No hay procesos Python corriendo")

    except Exception as e:
        print(f"❌ Error verificando procesos: {e}")

def main():
    print("🔍 Diagnóstico de Healthcheck - TELEWAN")
    print("=" * 50)

    check_environment()
    flask_ok = test_flask_basic()
    test_network()
    check_processes()

    print("\n" + "=" * 50)

    if flask_ok:
        print("✅ Flask está configurado correctamente")
        print("💡 Si el healthcheck falla, verifica:")
        print("   - Que USE_WEBHOOK=true esté configurado")
        print("   - Que el puerto esté disponible")
        print("   - Los logs del contenedor: railway logs --follow")
    else:
        print("❌ Hay problemas con Flask")
        print("💡 Verifica que flask esté en requirements.txt")

    print("\n📋 Comandos útiles:")
    print("  railway logs --tail 20          # Ver logs recientes")
    print("  railway run python test_flask.py # Probar Flask solo")
    print("  railway variables list          # Ver configuración")

if __name__ == "__main__":
    main()
