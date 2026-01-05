"""
Event Handlers for Event-Driven Architecture
Contains handlers for different types of events in the system
"""
import logging
import asyncio
from typing import Dict, Any

from .types import (
    BaseEvent, TelegramUpdateReceived, ImageProcessingStarted,
    VideoGenerationStarted, VideoGenerationCompleted, VideoGenerationFailed,
    ProcessingError, HealthCheckEvent
)
from .bus import event_bus

logger = logging.getLogger(__name__)


class EventHandlers:
    """Collection of event handlers for the event-driven system"""

    def __init__(self):
        self._registered_handlers = []
        self._stats = {
            "events_processed": 0,
            "errors_handled": 0,
            "videos_generated": 0,
            "videos_failed": 0
        }

    async def register_all_handlers(self):
        """Register all event handlers with the event bus"""
        logger.info("🔧 Registering event handlers...")

        # Telegram events
        await event_bus.subscribe("telegram.update_received", self.handle_telegram_update)

        # Image processing events
        await event_bus.subscribe("image.processing_started", self.handle_image_processing_started)
        await event_bus.subscribe("image.processing_completed", self.handle_image_processing_completed)

        # Video generation events
        await event_bus.subscribe("video.generation_started", self.handle_video_generation_started)
        await event_bus.subscribe("video.generation_completed", self.handle_video_generation_completed)
        await event_bus.subscribe("video.generation_failed", self.handle_video_generation_failed)

        # Error events
        await event_bus.subscribe("error.processing", self.handle_processing_error)

        # Health events
        await event_bus.subscribe("health.check", self.handle_health_check)

        logger.info("✅ All event handlers registered")

    async def unregister_all_handlers(self):
        """Unregister all event handlers"""
        logger.info("🔧 Unregistering event handlers...")
        # Note: In a real implementation, you'd want to keep track of registered handlers
        # and unsubscribe them individually. For now, we'll rely on the event bus cleanup.
        logger.info("✅ Event handlers unregistered")

    # Event Handlers

    async def handle_telegram_update(self, event: TelegramUpdateReceived):
        """Handle incoming Telegram updates"""
        self._stats["events_processed"] += 1

        update_data = event.data.get("update", {})
        update_id = update_data.get("update_id", "unknown")

        logger.info(f"📨 Processed Telegram update {update_id} from {event.source}")

        # Could trigger further processing based on update type
        # For now, just log and update stats

    async def handle_image_processing_started(self, event: ImageProcessingStarted):
        """Handle when image processing starts"""
        chat_id = event.data["chat_id"]
        user_id = event.data["user_id"]
        image_type = event.data["image_type"]

        logger.info(f"🖼️ Started processing {image_type} for user {user_id} in chat {chat_id}")

        # Could update user status, send progress messages, etc.

    async def handle_image_processing_completed(self, event: ImageProcessingCompleted):
        """Handle when image processing completes"""
        chat_id = event.data["chat_id"]
        user_id = event.data["user_id"]
        prompt = event.data["prompt"]

        logger.info(f"✅ Completed image processing for user {user_id}, prompt length: {len(prompt)}")

        # This would typically trigger video generation
        # await trigger_video_generation(chat_id, user_id, image_url, prompt)

    async def handle_video_generation_started(self, event: VideoGenerationStarted):
        """Handle when video generation starts"""
        request_id = event.data["request_id"]
        chat_id = event.data["chat_id"]
        model = event.data["model"]

        logger.info(f"🎬 Started video generation for chat {chat_id}, model: {model}, request: {request_id}")

        # Could update progress indicators, notify user, etc.

    async def handle_video_generation_completed(self, event: VideoGenerationCompleted):
        """Handle when video generation completes"""
        request_id = event.data["request_id"]
        video_url = event.data["video_url"]

        self._stats["videos_generated"] += 1

        logger.info(f"✅ Video generation completed: {request_id}, URL: {video_url[:50]}...")

        # This would trigger video download and delivery
        # await trigger_video_download_and_delivery(request_id, video_url)

    async def handle_video_generation_failed(self, event: VideoGenerationFailed):
        """Handle when video generation fails"""
        request_id = event.data["request_id"]
        error = event.data["error"]

        self._stats["videos_failed"] += 1

        logger.error(f"❌ Video generation failed: {request_id}, error: {error}")

        # Could notify user, retry, or log for analysis

    async def handle_processing_error(self, event: ProcessingError):
        """Handle processing errors"""
        component = event.source
        error = event.data["error"]
        context = event.data["context"]

        self._stats["errors_handled"] += 1

        logger.error(f"💥 Error in {component}: {error}")
        logger.error(f"   Context: {context}")

        # Could trigger alerts, retries, or error recovery

    async def handle_health_check(self, event: HealthCheckEvent):
        """Handle health check events"""
        component = event.data["component"]
        status = event.data["status"]
        metrics = event.data["metrics"]

        if status == "healthy":
            logger.debug(f"💚 Health check OK for {component}: {metrics}")
        else:
            logger.warning(f"❤️ Health check FAILED for {component}: {metrics}")

    # Utility methods

    def get_stats(self) -> Dict[str, Any]:
        """Get handler statistics"""
        return self._stats.copy()

    async def reset_stats(self):
        """Reset statistics counters"""
        self._stats = {
            "events_processed": 0,
            "errors_handled": 0,
            "videos_generated": 0,
            "videos_failed": 0
        }
        logger.info("📊 Handler statistics reset")


# Global handlers instance
event_handlers = EventHandlers()


async def init_event_handlers():
    """Initialize event handlers"""
    await event_handlers.register_all_handlers()


async def shutdown_event_handlers():
    """Shutdown event handlers"""
    await event_handlers.unregister_all_handlers()


# Convenience functions for publishing common events

async def publish_telegram_update(update_data: Dict[str, Any]) -> bool:
    """Publish a Telegram update received event"""
    return await event_bus.publish_event(
        "telegram.update_received",
        update_data=update_data
    )


async def publish_image_processing_started(chat_id: int, user_id: int, message_id: int, image_type: str) -> bool:
    """Publish image processing started event"""
    return await event_bus.publish_event(
        "image.processing_started",
        chat_id=chat_id,
        user_id=user_id,
        message_id=message_id,
        image_type=image_type
    )


async def publish_video_generation_started(request_id: str, chat_id: int, prompt: str, model: str) -> bool:
    """Publish video generation started event"""
    return await event_bus.publish_event(
        "video.generation_started",
        request_id=request_id,
        chat_id=chat_id,
        prompt=prompt,
        model=model
    )


async def publish_video_generation_completed(request_id: str, video_url: str) -> bool:
    """Publish video generation completed event"""
    return await event_bus.publish_event(
        "video.generation_completed",
        request_id=request_id,
        video_url=video_url
    )


async def publish_processing_error(component: str, error: str, context: Dict[str, Any]) -> bool:
    """Publish processing error event"""
    return await event_bus.publish_event(
        "error.processing",
        component=component,
        error=error,
        context=context
    )


async def publish_health_check(component: str, status: str, metrics: Dict[str, Any]) -> bool:
    """Publish health check event"""
    return await event_bus.publish_event(
        "health.check",
        component=component,
        status=status,
        metrics=metrics
    )
