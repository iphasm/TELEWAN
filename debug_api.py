#!/usr/bin/env python3
"""
Debug script to test Wavespeed API calls directly
This helps isolate issues with the API integration
"""
import asyncio
import os
from async_wavespeed import AsyncWavespeedAPI

async def test_api_connection():
    """Test basic API connection"""
    print("🔍 Testing Wavespeed API connection...")

    api_key = os.getenv('WAVESPEED_API_KEY')
    if not api_key:
        print("❌ WAVESPEED_API_KEY not set")
        return False

    api = AsyncWavespeedAPI()
    print(f"✅ API client initialized with key: {api_key[:8]}...")

    return True

async def test_video_generation():
    """Test video generation with a simple prompt"""
    print("\n🎬 Testing video generation...")

    api = AsyncWavespeedAPI()

    try:
        # Simple test prompt without image
        result = await api.generate_video(
            prompt="A beautiful sunset over mountains",
            image_url=None,
            model="ultra_fast"
        )

        print(f"✅ Generation response: {result}")

        # Extract request ID
        request_id = result.get("id") or result.get("request_id")
        if not request_id:
            print("❌ No request ID in response")
            return None

        print(f"📋 Request ID: {request_id}")
        return request_id

    except Exception as e:
        print(f"❌ Generation failed: {type(e).__name__}: {e}")
        return None

async def test_status_polling(request_id):
    """Test status polling for a request"""
    print(f"\n🔄 Testing status polling for request: {request_id}")

    api = AsyncWavespeedAPI()
    max_attempts = 10  # Just a few attempts for testing

    for attempt in range(max_attempts):
        try:
            print(f"🔍 Attempt {attempt + 1}/{max_attempts}")
            status_result = await api.get_video_status(request_id)
            print(f"📋 Status response: {status_result}")

            # Check status
            if status_result.get('data'):
                task_data = status_result['data']
                status = task_data.get('status')
                print(f"📊 Nested status: {status}")

                if status == "completed" and task_data.get('outputs'):
                    video_url = task_data['outputs'][0]
                    print(f"🎬 Video completed! URL: {video_url}")
                    return True

            else:
                status = status_result.get("status")
                print(f"📊 Direct status: {status}")

            await asyncio.sleep(2)

        except Exception as e:
            print(f"❌ Status check failed: {type(e).__name__}: {e}")
            await asyncio.sleep(2)

    print("⏰ Polling test completed (may still be processing)")
    return False

async def main():
    """Main test function"""
    print("🧪 SynthClip API Debug Test")
    print("=" * 50)

    # Test 1: API connection
    if not await test_api_connection():
        return

    # Test 2: Video generation
    request_id = await test_video_generation()
    if not request_id:
        return

    # Test 3: Status polling
    await test_status_polling(request_id)

    print("\n✨ Debug test completed")
    print("💡 Check the output above for any issues")

if __name__ == "__main__":
    asyncio.run(main())