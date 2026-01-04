#!/usr/bin/env python3
"""
Script de prueba para verificar la generación de captions en videos.
"""
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_video_caption_generation():
    """Prueba la generación de captions para videos."""

    print("=== Prueba de Generación de Captions para Videos ===")

    # Casos de prueba
    test_cases = [
        {
            "description": "Prompt original simple",
            "prompt": "una mujer hermosa caminando en la playa",
            "prompt_optimized": False
        },
        {
            "description": "Prompt optimizado largo",
            "prompt": "A stunning cinematic portrait of a beautiful woman with flowing hair, dramatic lighting, shallow depth of field, 4K resolution, film grain texture, atmospheric mood, hyper-realistic skin details, professional composition",
            "prompt_optimized": True
        },
        {
            "description": "DEFAULT_PROMPT (sin caption)",
            "prompt": "Absolutely fixed face and head position, zero head movement. No camera movement — a static, hyper-detailed cinematic shot. She swiftly reaches and removes her entire dress with decisive and strong motion...",
            "prompt_optimized": False
        },
        {
            "description": "Text-to-video prompt",
            "prompt": "Un amanecer espectacular sobre las montañas con nubes moviéndose suavemente",
            "prompt_optimized": False
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Caso {i}: {test_case['description']} ---")

        prompt = test_case['prompt']
        prompt_optimized = test_case['prompt_optimized']

        # Generar el caption como lo hace el bot
        video_caption = f"🎬 **Prompt utilizado:**\n{prompt}"
        if prompt_optimized:
            video_caption += "\n\n🎨 *Prompt optimizado automáticamente*"

        print(f"Prompt original: {prompt[:80]}...")
        print(f"Prompt optimizado: {prompt_optimized}")
        print(f"Caption generado:")
        print(video_caption)
        print(f"Longitud del caption: {len(video_caption)} caracteres")

        # Verificar límites de Telegram (4096 caracteres)
        if len(video_caption) > 4096:
            print("⚠️  ADVERTENCIA: Caption excede límite de 4096 caracteres de Telegram!")
        else:
            print("✅ Caption dentro de límites")

    print("\n=== Pruebas completadas ===")

if __name__ == "__main__":
    test_video_caption_generation()
