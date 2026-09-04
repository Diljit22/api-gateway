import asyncio
from typing import Callable, Any, Dict, Tuple, Awaitable

class RequestChanneler:
    """
    Manages outbound request concurrency to backend instances.
    - Bulkhead: Enforces a maximum concurrent request limit per backend instance.
    - Request Coalescing (Singleflight): Deduplicates identical concurrent GET 
      requests, serving multiple clients with a single backend invocation.
    """
    def __init__(self, max_concurrent_per_backend: int = 3):
        self.max_concurrent = max_concurrent_per_backend
        self.semaphores: Dict[str, asyncio.Semaphore] = {}
        self.in_flight: Dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()

    def _get_semaphore(self, backend: str) -> asyncio.Semaphore:
        if backend not in self.semaphores:
            self.semaphores[backend] = asyncio.Semaphore(self.max_concurrent)
        return self.semaphores[backend]

    async def _execute_with_bulkhead(self, backend: str, request_func: Callable[[], Awaitable[Any]]) -> Any:
        sem = self._get_semaphore(backend)
        async with sem:
            return await request_func()

    async def execute(
        self, 
        key: str, 
        backend: str, 
        request_func: Callable[[], Awaitable[Any]],
        coalesce: bool = True
    ) -> Tuple[Any, bool]:
        """
        Executes a request with concurrency limits and optional coalescing.
        Returns: (result, was_coalesced)
        """
        if coalesce:
            async with self._lock:
                if key in self.in_flight:
                    task = self.in_flight[key]
                    result = await task
                    return result, True
                
                # Wrap execution in an asyncio.Task to allow safe exception propagation
                task = asyncio.create_task(self._execute_with_bulkhead(backend, request_func))
                self.in_flight[key] = task

            try:
                result = await task
                return result, False
            finally:
                async with self._lock:
                    if self.in_flight.get(key) == task:
                        self.in_flight.pop(key, None)
        else:
            result = await self._execute_with_bulkhead(backend, request_func)
            return result, False