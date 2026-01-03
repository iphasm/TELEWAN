#!/usr/bin/env python3
"""
Script para probar el endpoint de healthcheck directamente
Ejecutar en Railway: railway run python test_health_endpoint.py
"""

import requests
import time
import os

def test_local_healthcheck():
    """Probar healthcheck desde dentro del contenedor"""
    print("🏥 Probando healthcheck local...")

    # Intentar acceder al localhost en el puerto del contenedor
    port = int(os.getenv('WEBHOOK_PORT', '8443'))
    url = f"http://localhost:{port}/"

    try:
        print(f"Intentando conectar a: {url}")
        response = requests.get(url, timeout=10)

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            print("✅ Healthcheck local funciona correctamente")
            return True
        else:
            print(f"❌ Healthcheck falló con código: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"❌ No se puede conectar a localhost:{port}")
        print("💡 El servidor Flask podría no estar corriendo")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_external_healthcheck():
    """Probar healthcheck desde fuera (usando la URL de Railway)"""
    print("\n🌐 Probando healthcheck externo...")

    webhook_url = os.getenv('WEBHOOK_URL')
    if not webhook_url:
        print("❌ WEBHOOK_URL no configurada")
        return False

    # Asegurar HTTPS
    if not webhook_url.startswith('http'):
        webhook_url = f"https://{webhook_url}"

    url = f"{webhook_url}/"

    try:
        print(f"Intentando conectar a: {url}")
        response = requests.get(url, timeout=10)

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            print("✅ Healthcheck externo funciona correctamente")
            return True
        else:
            print(f"❌ Healthcheck externo falló con código: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError as e:
        print(f"❌ No se puede conectar externamente: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def check_server_status():
    """Verificar si el servidor está corriendo"""
    print("\n🔍 Verificando estado del servidor...")

    try:
        import subprocess
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)

        flask_processes = [line for line in result.stdout.split('\n') if 'flask' in line.lower() or 'bot.py' in line]
        python_processes = [line for line in result.stdout.split('\n') if 'python' in line.lower()]

        print(f"Procesos Python encontrados: {len(python_processes)}")
        print(f"Procesos Flask encontrados: {len(flask_processes)}")

        if flask_processes:
            print("✅ Servidor Flask detectado")
            for proc in flask_processes[:2]:
                print(f"   {proc.strip()[:100]}...")
        else:
            print("❌ No se detecta servidor Flask corriendo")

    except Exception as e:
        print(f"❌ Error verificando procesos: {e}")

def test_manual_flask():
    """Probar crear y ejecutar Flask manualmente"""
    print("\n🧪 Probando Flask manualmente...")

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

        # Probar que la app se crea correctamente
        print("✅ Flask app creada correctamente")

        # Intentar bind al puerto
        import socket
        port = int(os.getenv('WEBHOOK_PORT', '8443'))

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('0.0.0.0', port))
            sock.close()
            print(f"✅ Puerto {port} disponible para bind")
        except OSError as e:
            print(f"❌ Puerto {port} no disponible: {e}")

        return True

    except ImportError as e:
        print(f"❌ Error importando Flask: {e}")
        return False
    except Exception as e:
        print(f"❌ Error creando Flask app: {e}")
        return False

def main():
    print("🔬 Diagnóstico de Healthcheck Endpoint")
    print("=" * 50)

    # Ejecutar todas las pruebas
    tests = [
        ("Estado del servidor", check_server_status),
        ("Flask manual", test_manual_flask),
        ("Healthcheck local", test_local_healthcheck),
        ("Healthcheck externo", test_external_healthcheck),
    ]

    all_passed = True
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}:")
        print("-" * (len(test_name) + 3))
        if not test_func():
            all_passed = False

    print("\n" + "=" * 50)

    if all_passed:
        print("🎉 ¡Todas las pruebas pasaron!")
        print("El healthcheck debería funcionar correctamente.")
    else:
        print("⚠️  Algunas pruebas fallaron.")
        print("💡 Posibles soluciones:")
        print("   1. Verificar que el puerto 8443 esté disponible")
        print("   2. Revisar logs del contenedor: railway logs --follow")
        print("   3. Verificar configuración en railway.json")
        print("   4. Probar redeploy: railway deploy")

    print("\n📋 Información útil:")
    print(f"   Puerto configurado: {os.getenv('WEBHOOK_PORT', '8443')}")
    print(f"   URL de webhook: {os.getenv('WEBHOOK_URL', 'No configurada')}")

if __name__ == "__main__":
    main()
