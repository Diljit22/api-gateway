import time
from typing import Dict, Tuple

class TokenBucket:
    def __init__(self, capacity: float, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_update = time.time()
        self.last_access = time.time()

    def consume(self, amount: float = 1.0) -> bool:
        now = time.time()
        self.last_access = now
        elapsed = now - self.last_update
        self.last_update = now

        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)

        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False

class RateLimiter:
    """Token Bucket rate limiter supporting dynamic key-based limits and tiers."""
    def __init__(self):
        # Define limits for different tiers: (capacity, refill_rate_per_sec)
        self.tiers = {
            "anonymous": (5.0, 1.0),
            "basic": (10.0, 2.0),
            "premium": (30.0, 5.0)
        }
        self.buckets: Dict[str, TokenBucket] = {}

    def is_allowed(self, key: str, tier: str = "anonymous") -> Tuple[bool, int, float]:
        """
        Checks if a request is allowed for a given key and tier.
        Returns: (is_allowed, remaining_tokens, retry_after_seconds)
        """
        capacity, refill_rate = self.tiers.get(tier, self.tiers["anonymous"])
        
        if key not in self.buckets:
            self.buckets[key] = TokenBucket(capacity, refill_rate)
            
        bucket = self.buckets[key]
        
        # Dynamically adjust limits in case of configuration or tier updates
        bucket.capacity = capacity
        bucket.refill_rate = refill_rate

        allowed = bucket.consume(1.0)
        remaining = int(bucket.tokens)
        
        retry_after = 0.0
        if not allowed:
            needed = 1.0 - bucket.tokens
            retry_after = needed / bucket.refill_rate

        return allowed, remaining, retry_after

    def prune(self, max_idle_seconds: float = 3600.0):
        """Evicts inactive rate-limiting buckets from memory to prevent memory leaks."""
        now = time.time()
        stale_keys = [
            key for key, b in self.buckets.items()
            if now - b.last_access > max_idle_seconds
        ]
        for key in stale_keys:
            self.buckets.pop(key, None)