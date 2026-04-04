from abc import ABC, abstractmethod
from typing import Optional
from consistent_hash import ConsistentHashRing


class LoadBalancer(ABC):
    """Base class for all load-balancing strategies."""

    def __init__(self, backends: list[str]):
        self.all_backends = list(backends)
        self.healthy: set[str] = set(backends)

    def mark_down(self, backend: str):
        self.healthy.discard(backend)

    def mark_up(self, backend: str):
        if backend in self.all_backends:
            self.healthy.add(backend)

    @abstractmethod
    def pick(self, request_key: str = "") -> Optional[str]:
        """Choose a backend for the incoming request."""
        pass

    @abstractmethod
    def on_request_start(self, backend: str):
        """Called when a proxied request begins."""
        pass

    @abstractmethod
    def on_request_end(self, backend: str):
        """Called when a proxied request completes."""
        pass

class RoundRobin(LoadBalancer):
    """Simple round robin."""

    def __init__(self, backends: list[str]):
        super().__init__(backends)
        self._idx = 0

    def pick(self, request_key: str = "") -> Optional[str]:
        alive = [b for b in self.all_backends if b in self.healthy]
        if not alive:
            return None
        choice = alive[self._idx % len(alive)]
        self._idx += 1
        return choice

    def on_request_start(self, backend: str):
        pass

    def on_request_end(self, backend: str):
        pass

class LeastConnections(LoadBalancer):
    """
    Routes each request to the backend with the fewest
    in-flight connections. Ties are broken by order.

    Why this matters:
        Round Robin doesn't care if one server is handling a
        slow 5s query while another is idle. Least-Connections
        naturally adapts to heterogeneous response times.
    """

    def __init__(self, backends: list[str]):
        super().__init__(backends)
        self._active: dict[str, int] = {b: 0 for b in backends}

    def pick(self, request_key: str = "") -> Optional[str]:
        alive = [b for b in self.all_backends if b in self.healthy]
        if not alive:
            return None
        return min(alive, key=lambda b: self._active.get(b, 0))

    def on_request_start(self, backend: str):
        self._active[backend] = self._active.get(backend, 0) + 1

    def on_request_end(self, backend: str):
        self._active[backend] = max(0, self._active.get(backend, 0) - 1)

    def get_connections(self) -> dict[str, int]:
        """Snapshot of active connections (useful for demos)."""
        return dict(self._active)

class ConsistentHashLB(LoadBalancer):
    """
    Uses a Consistent Hash Ring to assign requests.

    request_key determines placement on the ring, so the same
    key always hits the same server (sticky routing) unless
    that server goes down then traffic shifts to its
    clockwise neighbour.

    Set num_vnodes=0 for a raw ring (poor distribution),
    or num_vnodes=150 for production-grade evenness.
    """

    def __init__(self, backends: list[str], num_vnodes: int = 150):
        super().__init__(backends)
        self.ring = ConsistentHashRing(num_vnodes=num_vnodes)
        for b in backends:
            self.ring.add_server(b)

    def mark_down(self, backend: str):
        super().mark_down(backend)
        self.ring.remove_server(backend)

    def mark_up(self, backend: str):
        super().mark_up(backend)
        self.ring.add_server(backend)

    def pick(self, request_key: str = "") -> Optional[str]:
        if not self.healthy:
            return None
        server = self.ring.get_server(request_key or "default")
        return server

    def on_request_start(self, backend: str):
        pass

    def on_request_end(self, backend: str):
        pass