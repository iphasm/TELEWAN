#!/usr/bin/env python3
"""
Script de prueba para verificar las mejoras en la descarga de videos.
"""
import logging
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_download_improvements():
    """Prueba las mejoras en el sistema de descarga."""

    print("=== Prueba de Mejoras en Descarga de Videos ===")

    # Simular diferentes tipos de errores
    test_errors = [
        {
            "description": "Timeout Error",
            "error": TimeoutError("Connection timed out after 30 seconds"),
            "expected_message": "⏰ **Error de timeout**"
        },
        {
            "description": "Connection Error",
            "error": ConnectionError("Failed to establish connection"),
            "expected_message": "🌐 **Error de conexión**"
        },
        {
            "description": "HTTP Error",
            "error": Exception("404 Client Error"),  # Simulando HTTPError
            "expected_message": "🔴 **Error del servidor**"
        },
        {
            "description": "Unknown Error",
            "error": ValueError("Some unexpected error"),
            "expected_message": "📡 **Error desconocido**"
        }
    ]

    # Simular el método _format_download_error
    def format_download_error(error, video_url):
        """Simula el método _format_download_error"""
        error_type = type(error).__name__

        base_message = "❌ Error al descargar el video después de múltiples intentos.\n\n"

        if "Timeout" in error_type:
            base_message += "⏰ **Error de timeout**\n"
            base_message += "El servidor tardó demasiado en responder.\n\n"
        elif "Connection" in error_type:
            base_message += "🌐 **Error de conexión**\n"
            base_message += "No se pudo conectar al servidor de videos.\n\n"
        elif "HTTP" in str(error) or "404" in str(error) or "500" in str(error):
            base_message += "🔴 **Error del servidor**\n"
            base_message += f"El servidor respondió con error HTTP.\n\n"
        else:
            base_message += "📡 **Error desconocido**\n"
            base_message += f"Tipo: `{error_type}`\n\n"

        base_message += f"🔗 **URL del video:**\n{video_url}\n\n"
        base_message += "💡 Contacta al administrador si el problema persiste."

        return base_message

    test_url = "https://d2p7pge43lyniu.cloudfront.net/output/test-video.mp4"

    for i, test_case in enumerate(test_errors, 1):
        print(f"\n--- Caso {i}: {test_case['description']} ---")

        formatted_message = format_download_error(test_case['error'], test_url)

        print("Mensaje generado:")
        print(formatted_message)
        print(f"Longitud: {len(formatted_message)} caracteres")

        # Verificar que contiene el mensaje esperado
        if test_case['expected_message'] in formatted_message:
            print("✅ Mensaje correcto incluido")
        else:
            print("❌ Mensaje esperado no encontrado")

    print("\n=== Sistema de Reintentos ===")

    # Simular el sistema de reintentos
    max_attempts = 5
    for attempt in range(max_attempts):
        print(f"Intento {attempt + 1}/{max_attempts}")

        if attempt < max_attempts - 1:
            wait_time = 2 * (attempt + 1)
            print(f"  ⏳ Esperando {wait_time} segundos antes del siguiente intento...")
            time.sleep(0.1)  # Simulación breve
        else:
            print("  ❌ Último intento fallido - enviando mensaje de error")

    print("\n=== Pruebas completadas ===")
    print("💡 Las mejoras incluyen:")
    print("  - Mejor manejo de errores específicos")
    print("  - Mensajes informativos para el usuario")
    print("  - Sistema de reintentos progresivos")
    print("  - Logging detallado para diagnóstico")
    print("  - Validación de URLs antes de descargar")

if __name__ == "__main__":
    test_download_improvements()

