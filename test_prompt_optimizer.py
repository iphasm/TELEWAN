#!/usr/bin/env python3
"""
Script de prueba para la funcionalidad de optimización de prompts
"""

import os
import time
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Importar después de cargar .env
from wavespeed_api import WavespeedAPI

def test_prompt_optimizer():
    """Prueba la funcionalidad del prompt optimizer"""
    print("🧪 Probando Prompt Optimizer...")

    # Verificar API key
    api_key = os.getenv("WAVESPEED_API_KEY")
    if not api_key:
        print("❌ WAVESPEED_API_KEY no encontrada en .env")
        return

    print(f"✅ API Key encontrada: {api_key[:10]}...")

    # Crear instancia de la API
    wavespeed = WavespeedAPI()

    # URL de prueba (imagen de ejemplo)
    test_image_url = "https://d1q70pf5vjeyhc.cloudfront.net/media/4337ee19681340a888c8707fb49e026c/images/1767173780052146671_HRPY53c5.png"

    print(f"🖼️  Usando imagen de prueba: {test_image_url}")

    try:
        # Paso 1: Enviar imagen al optimizer
        print("\n📤 Enviando imagen al optimizer...")
        result = wavespeed.optimize_prompt(test_image_url, mode="image", style="default")

        if result.get('data') and result['data'].get('id'):
            request_id = result['data']['id']
            print(f"✅ Tarea enviada exitosamente. Request ID: {request_id}")

            # Paso 2: Esperar resultado
            print("\n⏳ Esperando resultado...")
            max_attempts = 60  # 30 segundos máximo
            attempt = 0

            while attempt < max_attempts:
                status_result = wavespeed.get_prompt_optimizer_status(request_id)

                if status_result.get('data'):
                    task_data = status_result['data']
                    status = task_data.get('status')

                    if status == 'completed':
                        if task_data.get('outputs') and len(task_data['outputs']) > 0:
                            optimized_prompt = task_data['outputs'][0]
                            print("✅ Optimización completada!"                            print(f"📝 Prompt optimizado: {optimized_prompt}")
                            return True
                        else:
                            print("❌ Optimización completada pero sin outputs")
                            return False

                    elif status == 'failed':
                        error_msg = task_data.get('error', 'Error desconocido')
                        print(f"❌ Optimización falló: {error_msg}")
                        return False

                    else:
                        print(f"⏳ Estado: {status} (intento {attempt + 1}/{max_attempts})")

                attempt += 1
                time.sleep(0.5)

            print("⏰ Timeout: La optimización tomó demasiado tiempo")
            return False

        else:
            print(f"❌ Error al enviar tarea: {result}")
            return False

    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        return False

def test_should_optimize():
    """Prueba la función de detección de captions que necesitan optimización"""
    from bot import should_optimize_prompt

    print("\n🧪 Probando detección de captions que necesitan optimización...")

    test_cases = [
        ("foto", True, "Caption muy corto"),
        ("una imagen bonita", True, "Caption genérico"),
        ("hola mundo", True, "Palabras genéricas"),
        ("hermosa mujer con vestido rojo caminando en la playa al atardecer", False, "Caption detallado"),
        ("A cinematic shot of a beautiful woman with flowing hair, dramatic lighting, shallow depth of field", False, "Ya es un prompt técnico"),
        ("", True, "Caption vacío"),
        ("test", True, "Palabra genérica"),
        ("A beautiful landscape with mountains and a lake, cinematic lighting, 4k resolution", False, "Ya tiene elementos técnicos")
    ]

    for caption, expected, description in test_cases:
        result = should_optimize_prompt(caption)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{caption[:30]}{'...' if len(caption) > 30 else ''}' -> {result} ({description})")

    return True

if __name__ == "__main__":
    print("🚀 Iniciando pruebas del Prompt Optimizer\n")

    # Prueba 1: Detección de captions
    test_should_optimize()

    # Prueba 2: API completa
    print("\n" + "="*50)
    success = test_prompt_optimizer()

    if success:
        print("\n🎉 Todas las pruebas pasaron exitosamente!")
    else:
        print("\n💥 Algunas pruebas fallaron.")
