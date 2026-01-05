#!/usr/bin/env python3
"""
Script de prueba para verificar la detección automática de URLs
"""
import re
from urllib.parse import urlparse

# Copiar la lógica del VideoDownloader para testing
SUPPORTED_PLATFORMS = {
    'facebook.com': 'Facebook',
    'fb.com': 'Facebook',
    'instagram.com': 'Instagram',
    'instagr.am': 'Instagram',
    'twitter.com': 'X (Twitter)',
    'x.com': 'X (Twitter)',
    'reddit.com': 'Reddit',
    'tiktok.com': 'TikTok',
    'vm.tiktok.com': 'TikTok'
}

def detect_platform(url: str) -> str:
    """Detecta la plataforma de redes sociales desde la URL"""
    try:
        domain = urlparse(url).netloc.lower()
        for platform_domain, platform_name in SUPPORTED_PLATFORMS.items():
            if platform_domain in domain:
                return platform_name
        return None
    except Exception as e:
        print(f"Error detectando plataforma para URL {url}: {e}")
        return None

def is_valid_social_url(url: str) -> bool:
    """Verifica si la URL es de una red social soportada"""
    platform = detect_platform(url)
    return platform is not None

def extract_urls_from_text(text: str) -> list:
    """Extrae todas las URLs de un texto"""
    url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?'
    return re.findall(url_pattern, text)

def test_url_extraction():
    """Prueba la extracción de URLs de texto"""
    test_messages = [
        "Mira este video: https://www.instagram.com/p/ABC123/",
        "Check this out https://twitter.com/user/status/123456 #cool",
        "Aquí está: https://www.facebook.com/watch?v=789 y también https://reddit.com/r/videos/comments/xyz/",
        "Sin URLs aquí, solo texto normal",
        "Múltiples: https://instagram.com/p/DEF456/ y https://x.com/user/status/789",
    ]

    print("🧪 Probando extracción de URLs:")
    for message in test_messages:
        urls = extract_urls_from_text(message)
        print(f"  Texto: {message[:50]}...")
        print(f"  URLs encontradas: {urls}")

        for url in urls:
            platform = detect_platform(url)
            valid = is_valid_social_url(url)
            status = "✅" if valid else "❌"
            print(f"    {status} {url} -> {platform}")
        print()

def test_detection():
    """Prueba la detección de plataformas"""
    test_urls = [
        "https://www.instagram.com/p/ABC123/",
        "https://twitter.com/user/status/123",
        "https://www.facebook.com/watch?v=456",
        "https://reddit.com/r/videos/comments/789/video/",
        "https://tiktok.com/@user/video/123",
        "https://vm.tiktok.com/abc123/",
        "https://youtube.com/watch?v=abc",  # No soportado
    ]

    print("🧪 Probando detección de plataformas:")
    for url in test_urls:
        platform = detect_platform(url)
        valid = is_valid_social_url(url)
        status = "✅" if valid else "❌"
        print(f"  {status} {url} -> {platform}")

if __name__ == "__main__":
    print("🚀 Probando Detección Automática de URLs\n")
    test_url_extraction()
    print("\n" + "="*50 + "\n")
    test_detection()
    print("\n✅ Pruebas completadas")
