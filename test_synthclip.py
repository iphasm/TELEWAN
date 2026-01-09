#!/usr/bin/env python3
"""
Test script for SynthClip web application
Run this to test the application locally with detailed logging
"""
import os
import sys
import asyncio
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up environment for testing
os.environ.setdefault('WAVESPEED_API_KEY', 'test_key')
os.environ.setdefault('BASE_URL', 'http://localhost:8000')
os.environ.setdefault('VOLUME_PATH', './test_storage')

async def test_imports():
    """Test that all imports work correctly"""
    try:
        from web_app import app
        from config import Config
        from async_wavespeed import AsyncWavespeedAPI
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_config():
    """Test configuration loading"""
    try:
        from config import Config
        print(f"📋 WAVESPEED_API_KEY: {'✓ Set' if Config.WAVESPEED_API_KEY else '✗ Missing'}")
        print(f"📋 WAVESPEED_BASE_URL: {Config.WAVESPEED_BASE_URL}")
        print(f"📋 VOLUME_PATH: {Config.VOLUME_PATH}")
        return True
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 SynthClip Test Suite")
    print("=" * 50)

    # Test imports
    if not asyncio.run(test_imports()):
        return False

    # Test config
    if not test_config():
        return False

    print("\n🚀 Starting SynthClip server...")
    print("📝 Visit http://localhost:8000 to test the web interface")
    print("🔍 Check console output for detailed logs during video generation")
    print("🛑 Press Ctrl+C to stop the server")

    try:
        import uvicorn
        uvicorn.run(
            "web_app:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")
        return False

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)