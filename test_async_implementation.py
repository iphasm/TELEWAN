#!/usr/bin/env python3
"""
Test script for async implementation (Fase 1)
Verifica que las nuevas funciones async funcionan correctamente
"""
import asyncio
import logging
import sys

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def test_async_wavespeed_api():
    """Prueba la nueva AsyncWavespeedAPI"""
    print("🧪 Probando AsyncWavespeedAPI...")

    try:
        from async_wavespeed import AsyncWavespeedAPI

        api = AsyncWavespeedAPI()
        print("✅ AsyncWavespeedAPI instanciada correctamente")

        # Verificar que los métodos existen
        methods = ['generate_video', 'get_video_status', 'download_video',
                  'optimize_prompt_v3', 'get_prompt_optimizer_result']

        for method in methods:
            if hasattr(api, method):
                print(f"✅ Método {method} existe")
            else:
                print(f"❌ Método {method} no encontrado")
                return False

        print("✅ Todos los métodos de AsyncWavespeedAPI están presentes")
        return True

    except ImportError as e:
        print(f"❌ Error importando AsyncWavespeedAPI: {e}")
        return False
    except Exception as e:
        print(f"❌ Error en AsyncWavespeedAPI: {e}")
        return False

async def test_async_handlers():
    """Prueba las funciones async de handlers"""
    print("\n🧪 Probando async handlers...")

    try:
        from async_handlers import (
            generate_serial_filename,
            optimize_user_prompt_async
        )

        # Probar generate_serial_filename
        filename = generate_serial_filename("test", "mp4")
        if filename.startswith("test_") and filename.endswith(".mp4"):
            print("✅ generate_serial_filename funciona correctamente")
        else:
            print(f"❌ generate_serial_filename falló: {filename}")
            return False

        # Probar optimize_user_prompt_async (sin API key debería retornar el texto original)
        if not hasattr(asyncio, 'run'):
            # Ya estamos en un loop async
            result = await optimize_user_prompt_async(
                image_url="https://example.com/test.jpg",
                text="Test prompt"
            )
        else:
            result = await optimize_user_prompt_async(
                image_url="https://example.com/test.jpg",
                text="Test prompt"
            )

        if result == "Test prompt":
            print("✅ optimize_user_prompt_async maneja errores correctamente")
        else:
            print(f"❌ optimize_user_prompt_async falló: {result}")
            return False

        print("✅ Async handlers funcionan correctamente")
        return True

    except ImportError as e:
        print(f"❌ Error importando async handlers: {e}")
        return False
    except Exception as e:
        print(f"❌ Error en async handlers: {e}")
        return False

async def test_imports():
    """Prueba que todas las importaciones funcionan"""
    print("\n🧪 Probando importaciones...")

    try:
        import aiohttp
        import aiofiles
        print("✅ aiohttp y aiofiles importados correctamente")

        import asyncio
        print("✅ asyncio disponible")

        return True
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        return False

async def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas de implementación async (Fase 1)")
    print("=" * 60)

    tests = [
        test_imports,
        test_async_wavespeed_api,
        test_async_handlers
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            result = await test()
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ Error ejecutando test {test.__name__}: {e}")

    print("\n" + "=" * 60)
    print(f"📊 RESULTADOS: {passed}/{total} tests pasaron")

    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron exitosamente!")
        print("✅ Fase 1 (Async I/O) implementada correctamente")
        return True
    else:
        print("❌ Algunas pruebas fallaron")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    if not success:
        sys.exit(1)
