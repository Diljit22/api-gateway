import time
import statistics
from radix_trie import RadixRouter

"""
Benchmark: Dict prefix scan vs Radix Trie lookup.

NB: Isolates the routing algorithm - no network, no HTTP.
"""
def bench(fn, runs: int, warmup: int = 50) -> list[float]:
    """Run fn with warmup, return list of elapsed times."""
    for _ in range(warmup):
        fn()
    times = []
    for _ in range(runs):
        start = time.perf_counter()
        fn()
        times.append(time.perf_counter() - start)
    return times


def report(label: str, times: list[float]):
    avg = statistics.mean(times)
    sd = statistics.stdev(times) if len(times) > 1 else 0.0
    p50 = sorted(times)[len(times) // 2]
    p99 = sorted(times)[int(len(times) * 0.99)]
    print(f"   {label}")
    print(f"     mean: {avg*1_000_000:.1f} µs   std: {sd*1_000_000:.1f} µs   p50: {p50*1_000_000:.1f} µs   p99: {p99*1_000_000:.1f} µs")


# Setup

ROUTE_COUNTS = [100, 10_000, 1_000_000]
RUNS = 500
TARGET_PATH = "/users/profile/123"

print(f"Benchmark: Dict Scan vs Radix Trie")
print(f"Target path: {TARGET_PATH}")
print(f"Runs per test: {RUNS} (+ 50 warmup)\n")

for num_routes in ROUTE_COUNTS:
    print(f"{'='*60}")
    print(f"  {num_routes:,} routes registered")
    print(f"{'='*60}\n")

    # Build the dict and trie with identical routes
    dict_routes = {}
    trie_router = RadixRouter()

    for i in range(num_routes):
        path = f"/api/v1/svc_{i}/endpoint"
        backend = f"http://localhost:9000"
        dict_routes[path] = backend
        trie_router.insert(path, backend)

    # Insert the route we're searching for
    dict_routes["/users"] = "http://localhost:8001"
    trie_router.insert("/users", "http://localhost:8001")

    # Pre-sort the keys once
    sorted_prefixes = sorted(dict_routes.keys(), key=len, reverse=True)

    # Dict scan
    def dict_lookup():
        for prefix in sorted_prefixes:
            if TARGET_PATH.startswith(prefix):
                return dict_routes[prefix]
        return None

    # Trie lookup
    def trie_lookup():
        return trie_router.search(TARGET_PATH)

    dict_times = bench(dict_lookup, RUNS)
    trie_times = bench(trie_lookup, RUNS)

    report("Dict scan:", dict_times)
    report("Radix Trie:", trie_times)

    avg_dict = statistics.mean(dict_times)
    avg_trie = statistics.mean(trie_times)
    speedup = avg_dict / avg_trie if avg_trie > 0 else float('inf')
    print(f"\n   Trie is {speedup:,.0f}x faster at {num_routes:,} routes.\n")