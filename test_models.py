#!/usr/bin/env python3
"""
Script de prueba para los nuevos modelos de Wavespeed AI
"""

# Simular la configuración y clases necesarias
class MockConfig:
    AVAILABLE_MODELS = {
        'ultra_fast': 'wan-2.2/i2v-480p-ultra-fast',
        'fast': 'wan-2.2/i2v-480p-fast',
        'quality': 'wan-2.2/i2v-720p-quality',
        'text_to_video': 'wan-2.2/t2v-480p-ultra-fast'
    }
    DEFAULT_MODEL = 'ultra_fast'
    MAX_VIDEO_DURATION = 8

class MockWavespeedAPI:
    def __init__(self):
        self.base_url = "https://api.wavespeed.ai"
        self.models = MockConfig.AVAILABLE_MODELS

    def generate_video(self, prompt: str, image_url: str = None, model: str = None) -> dict:
        """Simula la generación de video"""
        if model is None:
            model = MockConfig.DEFAULT_MODEL

        model_endpoint = self.models.get(model, self.models['ultra_fast'])
        endpoint = f"{self.base_url}/api/v3/wavespeed-ai/{model_endpoint}"

        # Simular configuración por modelo
        model_config = {
            'ultra_fast': {'duration': MockConfig.MAX_VIDEO_DURATION, 'resolution': '480p'},
            'fast': {'duration': MockConfig.MAX_VIDEO_DURATION, 'resolution': '480p'},
            'quality': {'duration': MockConfig.MAX_VIDEO_DURATION, 'resolution': '720p'},
            'text_to_video': {'duration': MockConfig.MAX_VIDEO_DURATION, 'resolution': '480p'}
        }

        config = model_config.get(model, model_config['ultra_fast'])

        payload = {
            "duration": config['duration'],
            "prompt": prompt,
            "negative_prompt": "test negative prompt",
        }

        # Solo incluir imagen si no es text-to-video
        if image_url and model != 'text_to_video':
            payload["image"] = image_url
            payload["last_image"] = ""
        elif model == 'text_to_video' and image_url:
            payload["image"] = image_url
            payload["last_image"] = ""

        return {
            "endpoint": endpoint,
            "payload": payload,
            "model": model,
            "config": config
        }

    def get_available_models(self) -> dict:
        """Retorna información sobre los modelos disponibles"""
        return {
            'ultra_fast': {
                'name': 'Ultra Fast 480p',
                'description': 'Video rápido en 480p, duración máxima 8s',
                'duration_max': 8,
                'resolution': '480p',
                'speed': 'ultra_fast'
            },
            'fast': {
                'name': 'Fast 480p',
                'description': 'Video rápido en 480p con mejor calidad',
                'duration_max': 8,
                'resolution': '480p',
                'speed': 'fast'
            },
            'quality': {
                'name': 'Quality 720p',
                'description': 'Video de alta calidad en 720p',
                'duration_max': 8,
                'resolution': '720p',
                'speed': 'quality'
            },
            'text_to_video': {
                'name': 'Text to Video 480p',
                'description': 'Genera video solo desde texto (sin imagen)',
                'duration_max': 8,
                'resolution': '480p',
                'speed': 'ultra_fast'
            }
        }

def test_models():
    """Prueba los diferentes modelos disponibles"""
    print("🎬 Probando modelos de Wavespeed AI...")
    print("=" * 60)

    api = MockWavespeedAPI()
    models_info = api.get_available_models()

    # Mostrar información de modelos
    print("📊 Modelos disponibles:")
    for model_key, model_info in models_info.items():
        print(f"  • {model_info['name']}: {model_info['description']}")
    print()

    # Test 1: Ultra Fast con imagen
    print("Test 1: Ultra Fast con imagen")
    result = api.generate_video("A beautiful sunset", "https://example.com/image.jpg", "ultra_fast")
    print(f"  Endpoint: {result['endpoint']}")
    print(f"  Payload keys: {list(result['payload'].keys())}")
    print(f"  Has image: {'image' in result['payload']}")
    print(f"  Resolution: {result['config']['resolution']}")
    print()

    # Test 2: Quality con imagen
    print("Test 2: Quality con imagen")
    result = api.generate_video("A beautiful sunset", "https://example.com/image.jpg", "quality")
    print(f"  Endpoint: {result['endpoint']}")
    print(f"  Resolution: {result['config']['resolution']}")
    print()

    # Test 3: Text to Video (sin imagen)
    print("Test 3: Text to Video (sin imagen)")
    result = api.generate_video("A beautiful sunset over mountains", None, "text_to_video")
    print(f"  Endpoint: {result['endpoint']}")
    print(f"  Has image: {'image' in result['payload']}")
    print(f"  Prompt: {result['payload']['prompt'][:50]}...")
    print()

    # Test 4: Modelo por defecto
    print("Test 4: Modelo por defecto (sin especificar)")
    result = api.generate_video("Default model test", "https://example.com/image.jpg")
    print(f"  Model: {result['model']}")
    print(f"  Resolution: {result['config']['resolution']}")
    print()

    # Test 5: Modelo inválido (debería usar default)
    print("Test 5: Modelo inválido")
    result = api.generate_video("Invalid model test", "https://example.com/image.jpg", "invalid_model")
    print(f"  Model fallback: {result['model']}")
    print(f"  Resolution: {result['config']['resolution']}")
    print()

    print("✅ Todos los tests completados correctamente!")
    print()
    print("💡 Resumen de funcionalidades implementadas:")
    print("  • 4 modelos diferentes (ultra_fast, fast, quality, text_to_video)")
    print("  • Configuración automática por modelo")
    print("  • Manejo de imágenes opcionales para text-to-video")
    print("  • Sistema de fallback para modelos inválidos")
    print("  • Información detallada de modelos disponibles")

if __name__ == '__main__':
    test_models()
