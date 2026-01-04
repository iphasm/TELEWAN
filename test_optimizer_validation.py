#!/usr/bin/env python3
"""
Script de prueba para validar la función optimize_prompt con validación de parámetros.
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
from bot import WavespeedAPI

def test_optimizer_validation():
    """Prueba la validación de parámetros del optimizer."""

    if not Config.WAVESPEED_API_KEY:
        logger.error("WAVESPEED_API_KEY no está configurada")
        return

    wavespeed = WavespeedAPI()

    logger.info("=== Probando validación del Prompt Optimizer ===")

    # URLs de prueba
    test_image_url = "https://via.placeholder.com/512x512.jpg"
    test_caption = "una mujer hermosa caminando en la playa"

    # Prueba 1: Parámetros válidos
    logger.info("Prueba 1: Parámetros válidos")
    try:
        result = wavespeed.optimize_prompt(
            image_url=test_image_url,
            text=test_caption,
            mode="video",
            style="realistic"
        )
        logger.info("✅ Parámetros válidos aceptados")
    except Exception as e:
        logger.error(f"❌ Error con parámetros válidos: {e}")

    # Prueba 2: Mode inválido
    logger.info("Prueba 2: Mode inválido")
    try:
        result = wavespeed.optimize_prompt(
            image_url=test_image_url,
            text=test_caption,
            mode="invalid_mode",
            style="realistic"
        )
        logger.error("❌ Mode inválido debería haber fallado")
    except ValueError as e:
        logger.info(f"✅ Mode inválido correctamente rechazado: {e}")
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")

    # Prueba 3: Style inválido
    logger.info("Prueba 3: Style inválido")
    try:
        result = wavespeed.optimize_prompt(
            image_url=test_image_url,
            text=test_caption,
            mode="video",
            style="invalid_style"
        )
        logger.error("❌ Style inválido debería haber fallado")
    except ValueError as e:
        logger.info(f"✅ Style inválido correctamente rechazado: {e}")
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")

    # Prueba 4: Text vacío
    logger.info("Prueba 4: Text vacío")
    try:
        result = wavespeed.optimize_prompt(
            image_url=test_image_url,
            text="",
            mode="video",
            style="realistic"
        )
        logger.error("❌ Text vacío debería haber fallado")
    except ValueError as e:
        logger.info(f"✅ Text vacío correctamente rechazado: {e}")
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")

    # Prueba 5: URL de imagen vacía
    logger.info("Prueba 5: URL de imagen vacía")
    try:
        result = wavespeed.optimize_prompt(
            image_url="",
            text=test_caption,
            mode="video",
            style="realistic"
        )
        logger.error("❌ URL vacía debería haber fallado")
    except ValueError as e:
        logger.info(f"✅ URL vacía correctamente rechazada: {e}")
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")

    logger.info("=== Pruebas de validación completadas ===")

if __name__ == "__main__":
    test_optimizer_validation()
