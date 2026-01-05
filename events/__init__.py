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

__all__ = [
    # Event Types
    "BaseEvent", "TelegramUpdateReceived", "ImageProcessingStarted",
    "ImageProcessingCompleted", "VideoGenerationStarted", "VideoGenerationProgress",
    "VideoGenerationCompleted", "VideoGenerationFailed", "VideoDownloadStarted",
    "VideoDownloadCompleted", "VideoSentToUser", "PromptOptimizationStarted",
    "PromptOptimizationCompleted", "ProcessingError", "HealthCheckEvent",
    "EVENT_TYPES", "create_event",

    # Event Bus
    "EventBus", "event_bus", "init_event_bus", "shutdown_event_bus"
]
