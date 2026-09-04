import asyncio
import httpx
import time

GATEWAY_URL = "http://localhost:8080/users/profile/1"

async def run_benchmark():
    print("=" * 75)
    print("  Caching Layer Benchmark: Cache Miss vs Cache Hit Latency")
    print("=" * 75)
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        # 1. First Request: Cache Miss
        print("Firing Request 1 (Expect Cache MISS)...")
        start = time.perf_counter()
        resp1 = await client.get(GATEWAY_URL)
        elapsed1 = time.perf_counter() - start
        cache_header1 = resp1.headers.get("X-Cache", "NONE")
        print(f"  Result 1 | Status: {resp1.status_code} | Time: {elapsed1:.4f}s | X-Cache: {cache_header1}")

        # 2. Second Request: Cache Hit
        print("\nFiring Request 2 (Expect Cache HIT)...")
        start = time.perf_counter()
        resp2 = await client.get(GATEWAY_URL)
        elapsed2 = time.perf_counter() - start
        cache_header2 = resp2.headers.get("X-Cache", "NONE")
        print(f"  Result 2 | Status: {resp2.status_code} | Time: {elapsed2:.4f}s | X-Cache: {cache_header2}")

        # Calculate speedup ratio
        speedup = elapsed1 / elapsed2 if elapsed2 > 0 else float('inf')
        print("\n" + "=" * 75)
        print(f"Cache Hit is {speedup:.1f}x faster than Cache Miss!")
        print("=" * 75)

if __name__ == "__main__":
    asyncio.run(run_benchmark())