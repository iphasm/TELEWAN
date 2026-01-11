#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad de descarga de videos
"""
import os
import sys
sys.path.append('.')

from bot import VideoDownloader

def test_platform_detection():
    """Prueba la detección de plataformas"""
    downloader = VideoDownloader()

    test_urls = [
        ("https://www.facebook.com/watch?v=123456789", "Facebook"),
        ("https://www.instagram.com/p/ABC123/", "Instagram"),
        ("https://twitter.com/user/status/123456", "X (Twitter)"),
        ("https://x.com/user/status/123456", "X (Twitter)"),
        ("https://reddit.com/r/videos/comments/123/video/", "Reddit"),
        ("https://youtube.com/watch?v=abc123", None),  # No soportado
    ]

    print("🧪 Probando detección de plataformas:")
    for url, expected in test_urls:
        result = downloader.detect_platform(url)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {url[:40]}... -> {result} (esperado: {expected})")

def test_url_validation():
    """Prueba la validación de URLs"""
    downloader = VideoDownloader()

    test_urls = [
        ("https://www.instagram.com/p/ABC123/", True),
        ("https://twitter.com/user/status/123", True),
        ("https://youtube.com/watch?v=abc", False),
        ("not-a-url", False),
    ]

    print("\n🧪 Probando validación de URLs:")
    for url, expected in test_urls:
        result = downloader.is_valid_social_url(url)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {url[:30]}... -> {result} (esperado: {expected})")

if __name__ == "__main__":
    print("🚀 Probando VideoDownloader")
    test_platform_detection()
    test_url_validation()
    print("\n✅ Pruebas completadas")
