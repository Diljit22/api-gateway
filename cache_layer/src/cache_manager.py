import time
from typing import Optional, Tuple, Dict

class CacheItem:
    def __init__(self, content: bytes, status_code: int, headers: dict, ttl_seconds: float):
        self.content = content
        self.status_code = status_code
        self.headers = headers
        self.expiry = time.time() + ttl_seconds

    def is_expired(self) -> bool:
        return time.time() > self.expiry

class CacheLayer:
    """An in-memory TTL cache with automated pruning."""
    def __init__(self, default_ttl: float = 10.0):
        self.default_ttl = default_ttl
        self.store: Dict[str, CacheItem] = {}

    def get(self, key: str) -> Optional[Tuple[bytes, int, dict]]:
        item = self.store.get(key)
        if not item:
            return None
        if item.is_expired():
            self.store.pop(key, None)
            return None
        return item.content, item.status_code, item.headers

    def set(self, key: str, content: bytes, status_code: int, headers: dict, ttl: Optional[float] = None):
        # Cache only successful GET responses
        if status_code != 200:
            return
        ttl_val = ttl if ttl is not None else self.default_ttl
        self.store[key] = CacheItem(content, status_code, headers, ttl_val)

    def prune(self):
        """Evicts expired cache entries."""
        now = time.time()
        expired_keys = [k for k, item in self.store.items() if item.expiry < now]
        for k in expired_keys:
            self.store.pop(k, None)