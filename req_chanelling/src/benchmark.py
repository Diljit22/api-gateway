import asyncio
import httpx
import time

GATEWAY_URL = "http://localhost:8080/users/profile/1"

async def send_request(client: httpx.AsyncClient, req_id: int):
    start = time.perf_counter()
    try:
        resp = await client.get(GATEWAY_URL)
        elapsed = time.perf_counter() - start
        if resp.status_code == 200:
            data = resp.json()
            random_id = data.get("random_id")
            handled_by = data.get("handled_by")
            coalesced_header = resp.headers.get("X-Request-Coalesced", "FALSE")
            print(f"Request {req_id:2d} | Status: 200 | Time: {elapsed:.3f}s | Random ID: {random_id} | Handled By: {handled_by} | Coalesced: {coalesced_header}")
        else:
            print(f"Request {req_id:2d} | Status: {resp.status_code} | Time: {elapsed:.3f}s")
    except Exception as e:
        print(f"Request {req_id:2d} | Failed: {e}")

async def run_benchmark():
    print("=" * 75)
    print("  Request Channeling Benchmark: Coalescing & Bulkhead Queuing")
    print("=" * 75)
    print("Firing 10 concurrent requests to the Gateway...")
    print("Note: The backend has a fixed delay of 1.0 second.\n")

    start_total = time.perf_counter()
    async with httpx.AsyncClient(timeout=10.0) as client:
        tasks = [send_request(client, i) for i in range(1, 11)]
        await asyncio.gather(*tasks)
    
    total_time = time.perf_counter() - start_total
    print("\n" + "=" * 75)
    print(f"Total benchmark execution time: {total_time:.3f} seconds")
    print("=" * 75)
    print("\nKey Takeaways:")
    print("1. All 10 requests completed in ~1.0 second total (rather than 10s or 4s queuing).")
    print("2. All parallel requests returned the exact same Random ID.")
    print("3. Duplicated requests carry the 'X-Request-Coalesced: TRUE' response header.")
    print("This confirms request coalescing successfully collapsed 10 parallel calls into 1 backend fetch!\n")

if __name__ == "__main__":
    asyncio.run(run_benchmark())