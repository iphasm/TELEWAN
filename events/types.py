"""
Event Types for Event-Driven Architecture
Define todos los tipos de eventos del sistema
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid


@dataclass
class BaseEvent:
    """Base event class with common fields"""
    event_type: str
    source: str
    data: Dict[str, Any]
    event_id: str = None
    timestamp: datetime = None

    def __post_init__(self):
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "data": self.data
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseEvent':
        """Create event from dictionary"""
        return cls(
            event_id=data.get("event_id", str(uuid.uuid4())),
            event_type=data["event_type"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            source=data["source"],
            data=data["data"]
        )


# Telegram Events
@dataclass
class TelegramUpdateReceived(BaseEvent):
    """Evento cuando se recibe una actualización de Telegram"""
    def __init__(self, update_data: Dict[str, Any], **kwargs):
        super().__init__(
            event_type="telegram.update_received",
            source="telegram_webhook",
            data={"update": update_data},
            **kwargs
        )


@dataclass
class ImageProcessingStarted(BaseEvent):
    """Evento cuando comienza el procesamiento de una imagen"""
    def __init__(self, chat_id: int, user_id: int, message_id: int, image_type: str, **kwargs):
        super().__init__(
            event_type="image.processing_started",
            source="image_handler",
            data={
                "chat_id": chat_id,
                "user_id": user_id,
                "message_id": message_id,
                "image_type": image_type
            },
            **kwargs
        )


@dataclass
class ImageProcessingCompleted(BaseEvent):
    """Evento cuando se completa el procesamiento de una imagen"""
    def __init__(self, chat_id: int, user_id: int, image_url: str, prompt: str, **kwargs):
        super().__init__(
            event_type="image.processing_completed",
            source="image_handler",
            data={
                "chat_id": chat_id,
                "user_id": user_id,
                "image_url": image_url,
                "prompt": prompt
            },
            **kwargs
        )


# Video Generation Events
@dataclass
class VideoGenerationStarted(BaseEvent):
    """Evento cuando comienza la generación de video"""
    def __init__(self, request_id: str, chat_id: int, prompt: str, model: str, **kwargs):
        super().__init__(
            event_type="video.generation_started",
            source="video_generator",
            data={
                "request_id": request_id,
                "chat_id": chat_id,
                "prompt": prompt,
                "model": model
            },
            **kwargs
        )


@dataclass
class VideoGenerationProgress(BaseEvent):
    """Evento de progreso en la generación de video"""
    def __init__(self, request_id: str, status: str, progress: Optional[float] = None, **kwargs):
        super().__init__(
            event_type="video.generation_progress",
            source="video_generator",
            data={
                "request_id": request_id,
                "status": status,
                "progress": progress
            },
            **kwargs
        )


@dataclass
class VideoGenerationCompleted(BaseEvent):
    """Evento cuando se completa la generación de video"""
    def __init__(self, request_id: str, video_url: str, **kwargs):
        super().__init__(
            event_type="video.generation_completed",
            source="video_generator",
            data={
                "request_id": request_id,
                "video_url": video_url
            },
            **kwargs
        )


@dataclass
class VideoGenerationFailed(BaseEvent):
    """Evento cuando falla la generación de video"""
    def __init__(self, request_id: str, error: str, **kwargs):
        super().__init__(
            event_type="video.generation_failed",
            source="video_generator",
            data={
                "request_id": request_id,
                "error": error
            },
            **kwargs
        )


# Video Delivery Events
@dataclass
class VideoDownloadStarted(BaseEvent):
    """Evento cuando comienza la descarga de video"""
    def __init__(self, request_id: str, video_url: str, **kwargs):
        super().__init__(
            event_type="video.download_started",
            source="video_downloader",
            data={
                "request_id": request_id,
                "video_url": video_url
            },
            **kwargs
        )


@dataclass
class VideoDownloadCompleted(BaseEvent):
    """Evento cuando se completa la descarga de video"""
    def __init__(self, request_id: str, file_path: str, file_size: int, **kwargs):
        super().__init__(
            event_type="video.download_completed",
            source="video_downloader",
            data={
                "request_id": request_id,
                "file_path": file_path,
                "file_size": file_size
            },
            **kwargs
        )


@dataclass
class VideoSentToUser(BaseEvent):
    """Evento cuando se envía el video al usuario"""
    def __init__(self, chat_id: int, message_id: int, video_url: str, prompt: str, **kwargs):
        super().__init__(
            event_type="video.sent_to_user",
            source="telegram_sender",
            data={
                "chat_id": chat_id,
                "message_id": message_id,
                "video_url": video_url,
                "prompt": prompt
            },
            **kwargs
        )


# Prompt Optimization Events
@dataclass
class PromptOptimizationStarted(BaseEvent):
    """Evento cuando comienza la optimización de prompt"""
    def __init__(self, chat_id: int, original_prompt: str, **kwargs):
        super().__init__(
            event_type="prompt.optimization_started",
            source="prompt_optimizer",
            data={
                "chat_id": chat_id,
                "original_prompt": original_prompt
            },
            **kwargs
        )


@dataclass
class PromptOptimizationCompleted(BaseEvent):
    """Evento cuando se completa la optimización de prompt"""
    def __init__(self, chat_id: int, original_prompt: str, optimized_prompt: str, **kwargs):
        super().__init__(
            event_type="prompt.optimization_completed",
            source="prompt_optimizer",
            data={
                "chat_id": chat_id,
                "original_prompt": original_prompt,
                "optimized_prompt": optimized_prompt
            },
            **kwargs
        )


# Error Events
@dataclass
class ProcessingError(BaseEvent):
    """Evento genérico de error en el procesamiento"""
    def __init__(self, component: str, error: str, context: Dict[str, Any], **kwargs):
        super().__init__(
            event_type="error.processing",
            source=component,
            data={
                "error": error,
                "context": context
            },
            **kwargs
        )


# Health Monitoring Events
@dataclass
class HealthCheckEvent(BaseEvent):
    """Evento de health check del sistema"""
    def __init__(self, component: str, status: str, metrics: Dict[str, Any], **kwargs):
        super().__init__(
            event_type="health.check",
            source="health_monitor",
            data={
                "component": component,
                "status": status,
                "metrics": metrics
            },
            **kwargs
        )


# Event type registry for easy lookup
EVENT_TYPES = {
    "telegram.update_received": TelegramUpdateReceived,
    "image.processing_started": ImageProcessingStarted,
    "image.processing_completed": ImageProcessingCompleted,
    "video.generation_started": VideoGenerationStarted,
    "video.generation_progress": VideoGenerationProgress,
    "video.generation_completed": VideoGenerationCompleted,
    "video.generation_failed": VideoGenerationFailed,
    "video.download_started": VideoDownloadStarted,
    "video.download_completed": VideoDownloadCompleted,
    "video.sent_to_user": VideoSentToUser,
    "prompt.optimization_started": PromptOptimizationStarted,
    "prompt.optimization_completed": PromptOptimizationCompleted,
    "error.processing": ProcessingError,
    "health.check": HealthCheckEvent,
}


def create_event(event_type: str, **kwargs) -> BaseEvent:
    """Factory function to create events by type"""
    event_class = EVENT_TYPES.get(event_type)
    if not event_class:
        raise ValueError(f"Unknown event type: {event_type}")
    return event_class(**kwargs)
