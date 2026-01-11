#!/usr/bin/env python3
"""
Debug script specifically for Text-to-Video functionality
"""
import asyncio
import os
from async_wavespeed import AsyncWavespeedAPI

async def test_text_to_video():
    """Test text-to-video generation"""
    print("🎬 Testing Text-to-Video generation...")

    api = AsyncWavespeedAPI()

    prompt = "A beautiful sunset over the ocean with waves gently crashing on the shore"

    try:
        print(f"📝 Prompt: {prompt}")
        print("🖼️  Image: None (Text-to-Video)")

        result = await api.generate_video(
            prompt=prompt,
            image_url=None,  # No image for text-to-video
            model="text_to_video"
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
        print(f"❌ Text-to-Video generation failed: {type(e).__name__}: {e}")
        return None

async def test_text_to_video_polling(request_id):
    """Test polling for text-to-video"""
    print(f"\n🔄 Testing Text-to-Video polling for request: {request_id}")

    api = AsyncWavespeedAPI()
    max_attempts = 60  # Shorter for testing

    for attempt in range(max_attempts):
        try:
            print(f"🔍 Attempt {attempt + 1}/{max_attempts}")
            status_result = await api.get_video_status(request_id)
            print(f"📋 Raw status: {status_result}")

            # Handle nested response
            if status_result.get('data'):
                task_data = status_result['data']
                status = task_data.get('status')
                print(f"📊 Nested status: {status}")

                if status == "completed":
                    if task_data.get('outputs') and len(task_data['outputs']) > 0:
                        video_url = task_data['outputs'][0]
                        print(f"🎬 SUCCESS! Video URL: {video_url}")
                        return video_url

                elif status == "failed":
                    error_msg = task_data.get("error", "Generation failed")
                    print(f"❌ Generation failed: {error_msg}")
                    return None

            else:
                status = status_result.get("status")
                print(f"📊 Direct status: {status}")

            print(f"⏳ Still processing... ({attempt + 1}/{max_attempts})")
            await asyncio.sleep(2)

        except Exception as e:
            print(f"❌ Polling error: {type(e).__name__}: {e}")
            await asyncio.sleep(2)

    print("⏰ Polling timeout")
    return None

async def main():
    """Main test function"""
    print("🎭 SynthClip Text-to-Video Debug Test")
    print("=" * 50)

    # Test generation
    request_id = await test_text_to_video()
    if not request_id:
        return

    # Test polling
    video_url = await test_text_to_video_polling(request_id)
    if video_url:
        print("
✅ Text-to-Video test completed successfully!"        print(f"📹 Video available at: {video_url}")
    else:
        print("\n❌ Text-to-Video test failed")

if __name__ == "__main__":
    asyncio.run(main())