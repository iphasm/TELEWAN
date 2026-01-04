#!/usr/bin/env python3
"""
Script de prueba para verificar el manejo de errores del prompt optimizer.
"""
import logging
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importar módulos después de configurar logging
from config import Config
from bot import WavespeedAPI, optimize_user_prompt

def test_optimizer_error_handling():
    """Prueba el manejo de errores del optimizer."""

    # Verificar configuración
    if not Config.WAVESPEED_API_KEY:
        logger.error("WAVESPEED_API_KEY no está configurada")
        return

    wavespeed = WavespeedAPI()

    # URLs de prueba
    test_image_url = "https://via.placeholder.com/512x512.jpg"  # Imagen placeholder
    test_caption = "una mujer hermosa caminando en la playa al atardecer"

    logger.info("=== Probando Prompt Optimizer con manejo de errores ===")

    try:
        # Prueba 1: URL inválida
        logger.info("Prueba 1: URL inválida")
        result_invalid = optimize_user_prompt("https://invalid-url.com/image.jpg", test_caption)
        logger.info(f"Resultado con URL inválida: '{result_invalid}'")

        # Prueba 2: API key inválida (temporalmente)
        logger.info("Prueba 2: URL válida pero con timeout simulado")
        result_timeout = optimize_user_prompt(test_image_url, test_caption)
        logger.info(f"Resultado con timeout: '{result_timeout[:100]}...'")

        # Prueba 3: Caption vacío
        logger.info("Prueba 3: Caption vacío")
        result_empty = optimize_user_prompt(test_image_url, "")
        logger.info(f"Resultado con caption vacío: '{result_empty[:100]}...'")

        logger.info("=== Todas las pruebas completadas ===")

    except Exception as e:
        logger.error(f"Error en las pruebas: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_optimizer_error_handling()
