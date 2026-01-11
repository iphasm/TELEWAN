#!/usr/bin/env python3
"""
Script de prueba para verificar la optimización de prompts
"""

import asyncio
import os
from async_wavespeed import AsyncWavespeedAPI

async def test_prompt_optimization():
    """Prueba la optimización de prompts"""

    # Verificar API key
    api_key = os.getenv('WAVESPEED_API_KEY')
    if not api_key:
        print("❌ WAVESPEED_API_KEY no configurada")
        return

    client = AsyncWavespeedAPI(api_key)

    test_prompt = "A woman walking in the city"

    print("🧪 PRUEBA DE OPTIMIZACIÓN DE PROMPTS")
    print("=" * 50)
    print(f"Prompt original: '{test_prompt}'")
    print()

    try:
        # Prueba optimización de texto solo
        print("🤖 Probando optimización de texto solo...")
        result = await client.optimize_prompt_text_only(
            text=test_prompt,
            mode="video",
            style="default"
        )

        print(f"📋 Respuesta completa: {result}")
        print()

        # Verificar estructura esperada
        if "optimized_prompt" in result:
            optimized = result["optimized_prompt"]
            print(f"✅ Encontrado optimized_prompt: '{optimized}'")
            print(f"📏 Longitud: original={len(test_prompt)}, optimizado={len(optimized)}")
        elif "result" in result:
            optimized = result["result"]
            print(f"✅ Encontrado result: '{optimized}'")
            print(f"📏 Longitud: original={len(test_prompt)}, optimizado={len(optimized)}")
        else:
            print(f"❌ No se encontró optimized_prompt ni result en: {list(result.keys())}")

        print()

        # Prueba optimización con imagen
        print("🖼️  Probando optimización con imagen...")
        test_image_url = "https://example.com/test.jpg"  # URL de prueba

        result_image = await client.optimize_prompt_v3(
            image_url=test_image_url,
            text=test_prompt,
            mode="video",
            style="default"
        )

        print(f"📋 Respuesta de optimización con imagen: {result_image}")

        if "id" in result_image:
            task_id = result_image["id"]
            print(f"📝 Task ID: {task_id}")

            # Intentar obtener resultado
            try:
                status = await client.get_prompt_optimizer_result(task_id)
                print(f"📋 Estado de optimización: {status}")
            except Exception as e:
                print(f"❌ Error obteniendo resultado: {e}")

    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_prompt_optimization())