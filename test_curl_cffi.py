#!/usr/bin/env python3
"""
Script de prueba para curl_cffi con TikTok
"""
import re

try:
    from curl_cffi import requests as curl_requests
    CURL_CFFI_AVAILABLE = True
    print("✅ curl_cffi importado correctamente")
except ImportError as e:
    CURL_CFFI_AVAILABLE = False
    print(f"❌ curl_cffi no disponible: {e}")
    exit(1)

def test_tiktok_curl_cffi():
    """Prueba curl_cffi con un video de TikTok"""

    # URL de prueba (debe ser un video público real)
    test_url = "https://www.tiktok.com/@tiktok/video/7106594312295894278"

    print(f"🧪 Probando curl_cffi con TikTok")
    print(f"📥 URL: {test_url}")
    print()

    try:
        # Headers para impersonar Safari iOS (bueno para TikTok)
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        print("🌐 Realizando petición con impersonación safari18_ios...")

        # Primera petición para obtener la página
        response = curl_requests.get(
            test_url,
            impersonate="safari18_ios",
            headers=headers,
            timeout=30,
            allow_redirects=True
        )

        print(f"📊 Status code: {response.status_code}")
        print(f"📏 Content length: {len(response.text)} caracteres")

        if response.status_code == 200:
            print("✅ Petición exitosa")

            # Buscar URLs de video en el contenido
            content = response.text

            # Patrones para encontrar URLs de video
            video_patterns = [
                r'"playAddr":"([^"]+)"',
                r'"downloadAddr":"([^"]+)"',
                r'playAddr["\s]*:[\s]*"([^"]+)"',
                r'https://v\d+\.ttcdn\.cn[^"\s]+',
                r'https://v\d+\.bytecdn\.cn[^"\s]+'
            ]

            video_urls = []
            for pattern in video_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    url = match.replace('\\u0026', '&').replace('\\', '')
                    if url.startswith('http') and url not in video_urls:
                        video_urls.append(url)

            print(f"🎥 URLs de video encontradas: {len(video_urls)}")

            for i, url in enumerate(video_urls[:3]):  # Mostrar máximo 3
                print(f"  {i+1}. {url[:80]}...")

            # Buscar título
            title_patterns = [
                r'"desc":"([^"]+)"',
                r'"text":"([^"]+)"',
                r'title["\s]*:[\s]*"([^"]+)"'
            ]

            title = "Sin título"
            for pattern in title_patterns:
                match = re.search(pattern, content)
                if match:
                    title = match.group(1).replace('\\n', ' ').strip()
                    break

            print(f"📝 Título encontrado: {title[:50]}...")

        else:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"📝 Respuesta: {response.text[:200]}...")

    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_tiktok_curl_cffi()
