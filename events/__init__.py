"""
Events Module for Event-Driven Architecture
Provides event types, event bus, and event handlers
"""

from .types import (
    BaseEvent, TelegramUpdateReceived, ImageProcessingStarted,
    ImageProcessingCompleted, VideoGenerationStarted, VideoGenerationProgress,
    VideoGenerationCompleted, VideoGenerationFailed, VideoDownloadStarted,
    VideoDownloadCompleted, VideoSentToUser, PromptOptimizationStarted,
    PromptOptimizationCompleted, ProcessingError, HealthCheckEvent,
    EVENT_TYPES, create_event
)

from .bus import EventBus, event_bus, init_event_bus, shutdown_event_bus
from .handlers import (
    EventHandlers, event_handlers, init_event_handlers, shutdown_event_handlers,
    publish_telegram_update, publish_image_processing_started,
    publish_video_generation_started, publish_video_generation_completed,
    publish_processing_error, publish_health_check
)

__all__ = [
    # Event Types
    "BaseEvent", "TelegramUpdateReceived", "ImageProcessingStarted",
    "ImageProcessingCompleted", "VideoGenerationStarted", "VideoGenerationProgress",
    "VideoGenerationCompleted", "VideoGenerationFailed", "VideoDownloadStarted",
    "VideoDownloadCompleted", "VideoSentToUser", "PromptOptimizationStarted",
    "PromptOptimizationCompleted", "ProcessingError", "HealthCheckEvent",
    "EVENT_TYPES", "create_event",

    # Event Bus
    "EventBus", "event_bus", "init_event_bus", "shutdown_event_bus",

    # Event Handlers
    "EventHandlers", "event_handlers", "init_event_handlers", "shutdown_event_handlers",
    "publish_telegram_update", "publish_image_processing_started",
    "publish_video_generation_started", "publish_video_generation_completed",
    "publish_processing_error", "publish_health_check"
]
