#!/usr/bin/env python3
"""
Script para probar diferentes modelos de Wavespeed AI y verificar cuáles funcionan
"""
import asyncio
import aiohttp
import json
from config import Config

async def test_model_availability():
    """Prueba la disponibilidad de diferentes modelos"""
    headers = {
        'Authorization': f'Bearer {Config.WAVESPEED_API_KEY}',
        'Content-Type': 'application/json'
    }

    # Lista de modelos a probar
    models_to_test = [
        'wan-2.2/i2v-480p-ultra-fast',
        'wan-2.2/i2v-480p-fast',
        'wan-2.2/i2v-720p-quality',
        'wan-2.2/t2v-480p-ultra-fast'
    ]

    base_url = "https://api.wavespeed.ai/api/v3/wavespeed-ai"

    for model in models_to_test:
        endpoint = f"{base_url}/{model}"
        print(f"\n🧪 Probando modelo: {model}")
        print(f"📍 Endpoint: {endpoint}")

        # Payload básico
        payload = {
            "duration": 5,  # Usar 5 segundos para prueba
            "prompt": "A beautiful sunset over mountains",
            "negative_prompt": "blurry, low quality",
            "seed": -1
        }

        # Solo agregar imagen para modelos i2v
        if 'i2v' in model:
            payload["image"] = "https://synthclip.up.railway.app/images/test.jpg"
            payload["last_image"] = ""

        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.post(endpoint, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    print(f"📊 Status: {response.status}")

                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Modelo {model} funciona correctamente")
                        print(f"🔍 Response: {result}")
                    elif response.status == 400:
                        error_text = await response.text()
                        print(f"❌ Bad Request: {error_text}")
                    else:
                        error_text = await response.text()
                        print(f"⚠️ Status {response.status}: {error_text}")

        except Exception as e:
            print(f"💥 Error: {e}")

if __name__ == "__main__":
    print("🚀 Probando disponibilidad de modelos Wavespeed AI...")
    asyncio.run(test_model_availability())