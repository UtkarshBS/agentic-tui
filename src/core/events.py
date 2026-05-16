"""Simple async event bus."""
from typing import Callable, Any
from collections import defaultdict
import asyncio


class EventBus:
    def __init__(self):
        self._handlers: dict[str, list[Callable]] = defaultdict(list)
        self._queue: asyncio.Queue = asyncio.Queue()

    def subscribe(self, event_type: str, handler: Callable[[Any], None]):
        self._handlers[event_type].append(handler)

    async def publish(self, event_type: str, payload: Any = None):
        await self._queue.put((event_type, payload))

    async def run(self):
        while True:
            try:
                event_type, payload = await asyncio.wait_for(self._queue.get(), timeout=0.1)
                for handler in self._handlers.get(event_type, []):
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            asyncio.create_task(handler(payload))
                        else:
                            handler(payload)
                    except Exception as e:
                        print(f"Event handler error: {e}")
            except asyncio.TimeoutError:
                await asyncio.sleep(0.01)