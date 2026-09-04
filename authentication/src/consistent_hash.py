import hashlib
import bisect
from typing import Optional


class ConsistentHashRing:
    """
    Consistent Hash Ring with optional virtual nodes.

    Without virtual nodes:
        Each server gets 1 point on the ring.
        Problem: uneven distribution, and removing a server dumps ALL
        its traffic onto a single neighbour (cascade risk).

    With virtual nodes:
        Each server gets `num_vnodes` points spread across the ring.
        Traffic redistributes evenly when a server is removed.
    """

    def __init__(self, num_vnodes: int = 0):
        self.num_vnodes = num_vnodes        # 0 = no virtual nodes
        self.ring: list[int] = []           # sorted list of hash positions
        self.ring_map: dict[int, str] = {}  # hash position -> server url
        self.servers: set[str] = set()

    def _hash(self, key: str) -> int:
        """MD5 hash -> 32-bit integer for ring position."""
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    def add_server(self, server_url: str):
        """Place a server (and its virtual nodes) onto the ring."""
        if server_url in self.servers:
            return
        self.servers.add(server_url)

        points = self._get_points(server_url)
        for h in points:
            self.ring_map[h] = server_url
            bisect.insort(self.ring, h)

    def remove_server(self, server_url: str):
        """Remove a server and all its virtual nodes from the ring."""
        if server_url not in self.servers:
            return
        self.servers.discard(server_url)

        points = self._get_points(server_url)
        for h in points:
            self.ring_map.pop(h, None)
            idx = bisect.bisect_left(self.ring, h)
            if idx < len(self.ring) and self.ring[idx] == h:
                self.ring.pop(idx)

    def get_server(self, key: str) -> Optional[str]:
        """Given a request key, walk clockwise to the first server."""
        if not self.ring:
            return None

        h = self._hash(key)
        idx = bisect.bisect_right(self.ring, h)
        # Wrap around the ring
        if idx == len(self.ring):
            idx = 0
        return self.ring_map[self.ring[idx]]

    def _get_points(self, server_url: str) -> list[int]:
        """Return all hash positions for a server (1 real + N virtual)."""
        if self.num_vnodes == 0:
            return [self._hash(server_url)]
        return [self._hash(f"{server_url}#vn{i}") for i in range(self.num_vnodes)]

    def get_distribution(self, sample_keys: list[str]) -> dict[str, int]:
        """For benchmarking: count how many keys map to each server."""
        dist: dict[str, int] = {}
        for key in sample_keys:
            server = self.get_server(key)
            if server:
                dist[server] = dist.get(server, 0) + 1
        return dist