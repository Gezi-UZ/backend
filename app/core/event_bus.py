"""
Event Bus — Sistema de pub/sub in-memory baseado em asyncio.Queue.

Permite que use cases (ex: ConfirmPaymentUseCase, ProcessAckUseCase)
publiquem eventos que sao consumidos por endpoints SSE em tempo real.
"""
import asyncio
import logging
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)


class EventBus:
    """
    Pub/sub in-memory por chave (ex: recharge_id).
    Cada subscriber recebe a sua propria asyncio.Queue.
    """

    def __init__(self):
        # chave -> lista de queues (um por subscriber SSE)
        self._subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)

    def subscribe(self, key: str) -> asyncio.Queue:
        """Cria uma queue para um subscriber e regista-a na chave."""
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers[key].append(queue)
        logger.info(f"EventBus: novo subscriber para '{key}' (total: {len(self._subscribers[key])})")
        return queue

    def unsubscribe(self, key: str, queue: asyncio.Queue):
        """Remove a queue do subscriber da chave."""
        if key in self._subscribers:
            try:
                self._subscribers[key].remove(queue)
            except ValueError:
                pass
            if not self._subscribers[key]:
                del self._subscribers[key]
            logger.info(f"EventBus: subscriber removido de '{key}'")

    async def publish(self, key: str, event: dict[str, Any]):
        """Publica um evento para todos os subscribers de uma chave."""
        if key not in self._subscribers:
            return
        for queue in self._subscribers[key]:
            await queue.put(event)
        logger.info(f"EventBus: evento publicado para '{key}' ({len(self._subscribers[key])} subscribers)")


# Instancia global (singleton)
event_bus = EventBus()
