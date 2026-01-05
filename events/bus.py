"""
Event Bus implementation using Redis Pub/Sub
Provides async publish/subscribe functionality for event-driven architecture
"""
import json
import asyncio
import logging
from typing import Dict, Any, Callable, List, Optional
from contextlib import asynccontextmanager

import redis.asyncio as redis

from .types import BaseEvent, EVENT_TYPES

logger = logging.getLogger(__name__)


class EventBus:
    """
    Async Event Bus using Redis Pub/Sub
    Handles event publishing and subscription in an event-driven architecture
    """

    def __init__(self, redis_url: str = "redis://localhost:6379", max_connections: int = 10):
        self.redis_url = redis_url
        self.max_connections = max_connections
        self._connection_pool = None
        self._subscribers: Dict[str, List[Callable]] = {}
        self._running = False
        self._listener_task: Optional[asyncio.Task] = None

    async def connect(self):
        """Initialize Redis connection pool"""
        try:
            self._connection_pool = redis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=self.max_connections,
                decode_responses=True
            )
            logger.info("✅ EventBus connected to Redis")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise

    async def disconnect(self):
        """Close Redis connections"""
        if self._connection_pool:
            await self._connection_pool.disconnect()
            logger.info("✅ EventBus disconnected from Redis")

        if self._listener_task and not self._listener_task.done():
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass

    @asynccontextmanager
    async def connection(self):
        """Context manager for Redis connections"""
        if not self._connection_pool:
            await self.connect()

        client = redis.Redis(connection_pool=self._connection_pool)
        try:
            yield client
        finally:
            # Connection will be returned to pool automatically
            pass

    async def publish(self, event: BaseEvent) -> bool:
        """
        Publish an event to Redis Pub/Sub

        Args:
            event: The event to publish

        Returns:
            bool: True if published successfully
        """
        try:
            event_data = event.to_dict()

            async with self.connection() as client:
                # Publish to Redis channel
                channel = f"events:{event.event_type}"
                await client.publish(channel, json.dumps(event_data))

                # Also publish to wildcard channel for global listeners
                await client.publish("events:*", json.dumps(event_data))

                logger.debug(f"📤 Published event: {event.event_type} (ID: {event.event_id})")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to publish event {event.event_type}: {e}")
            return False

    async def subscribe(self, event_type: str, handler: Callable[[BaseEvent], None]):
        """
        Subscribe to events of a specific type

        Args:
            event_type: Type of events to listen for (e.g., "video.generation_completed")
            handler: Async function to handle the event
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        self._subscribers[event_type].append(handler)
        logger.info(f"✅ Subscribed to {event_type} events")

        # Start listener if not already running
        if not self._running:
            await self._start_listener()

    async def unsubscribe(self, event_type: str, handler: Callable[[BaseEvent], None]):
        """
        Unsubscribe from events

        Args:
            event_type: Type of events to stop listening for
            handler: Handler function to remove
        """
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
                logger.info(f"✅ Unsubscribed from {event_type} events")
            except ValueError:
                logger.warning(f"Handler not found for {event_type}")

    async def _start_listener(self):
        """Start the Redis listener task"""
        if self._running:
            return

        self._running = True
        self._listener_task = asyncio.create_task(self._listen_for_events())
        logger.info("🎧 Event listener started")

    async def _listen_for_events(self):
        """Listen for events from Redis and dispatch to handlers"""
        try:
            async with self.connection() as client:
                # Subscribe to all event channels
                channels = []
                for event_type in self._subscribers.keys():
                    channels.append(f"events:{event_type}")

                # Also listen to wildcard channel
                channels.append("events:*")

                if not channels:
                    logger.warning("No event subscriptions, listener exiting")
                    return

                pubsub = client.pubsub()
                await pubsub.subscribe(*channels)

                logger.info(f"🎧 Listening for events on channels: {channels}")

                async for message in pubsub.listen():
                    if message["type"] == "message":
                        await self._handle_message(message)

        except Exception as e:
            logger.error(f"❌ Event listener error: {e}")
        finally:
            self._running = False
            logger.info("🛑 Event listener stopped")

    async def _handle_message(self, message: Dict[str, Any]):
        """Handle incoming Redis message"""
        try:
            channel = message["channel"]
            data = json.loads(message["data"])

            # Extract event type from channel
            if channel.startswith("events:"):
                event_type = channel[7:]  # Remove "events:" prefix

                # Create event object
                event_class = EVENT_TYPES.get(event_type)
                if event_class:
                    event = event_class.from_dict(data)

                    # Dispatch to all subscribers of this event type
                    if event_type in self._subscribers:
                        for handler in self._subscribers[event_type]:
                            try:
                                await handler(event)
                            except Exception as e:
                                logger.error(f"❌ Error in event handler for {event_type}: {e}")

                    # Also dispatch wildcard handlers
                    if "*" in self._subscribers:
                        for handler in self._subscribers["*"]:
                            try:
                                await handler(event)
                            except Exception as e:
                                logger.error(f"❌ Error in wildcard event handler: {e}")

                else:
                    logger.warning(f"Unknown event type received: {event_type}")

        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in event message: {e}")
        except Exception as e:
            logger.error(f"❌ Error handling event message: {e}")

    async def publish_event(self, event_type: str, **kwargs) -> bool:
        """
        Convenience method to create and publish events

        Args:
            event_type: Type of event to create
            **kwargs: Event data

        Returns:
            bool: True if published successfully
        """
        try:
            event = EVENT_TYPES[event_type](**kwargs)
            return await self.publish(event)
        except KeyError:
            logger.error(f"Unknown event type: {event_type}")
            return False
        except Exception as e:
            logger.error(f"Error creating/publishing event {event_type}: {e}")
            return False

    def get_subscriber_count(self, event_type: str = None) -> int:
        """
        Get count of subscribers

        Args:
            event_type: Specific event type, or None for all

        Returns:
            int: Number of subscribers
        """
        if event_type:
            return len(self._subscribers.get(event_type, []))
        else:
            return sum(len(handlers) for handlers in self._subscribers.values())

    def get_event_types(self) -> List[str]:
        """Get list of subscribed event types"""
        return list(self._subscribers.keys())

    async def health_check(self) -> Dict[str, Any]:
        """Check health of EventBus"""
        try:
            async with self.connection() as client:
                await client.ping()
                return {
                    "status": "healthy",
                    "redis_connected": True,
                    "subscribers": self.get_subscriber_count(),
                    "event_types": self.get_event_types(),
                    "listener_running": self._running
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "redis_connected": False,
                "error": str(e),
                "subscribers": self.get_subscriber_count(),
                "event_types": self.get_event_types(),
                "listener_running": self._running
            }


# Global EventBus instance
event_bus = EventBus()


async def init_event_bus():
    """Initialize the global event bus"""
    await event_bus.connect()


async def shutdown_event_bus():
    """Shutdown the global event bus"""
    await event_bus.disconnect()
