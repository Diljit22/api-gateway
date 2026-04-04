import subprocess
import asyncio
import sys
import random
import time
import statistics
import json
import httpx

"""
Chaos Demo: Live load-balancer stress test.

Spins up 6 backends + the gateway, sends a burst of requests,
randomly kills servers mid-flight, and prints distribution stats.
"""

# Config

BACKENDS = [
    (8001, "users"), (8003, "users"), (8005, "users"),
    (8002, "orders"), (8004, "orders"), (8006, "orders"),
]
GATEWAY_PORT = 8080
REQUEST_COUNT = 200
PATHS = [
    "/users/profile/1", "/users/profile/2", "/users/search?q=alice",
    "/orders/checkout", "/orders/status/99", "/orders/cancel/5",
]

processes: list[subprocess.Popen] = []


def start_backend(port: int, name: str) -> subprocess.Popen:
    proc = subprocess.Popen(
        [sys.executable, "backend.py", str(port), name],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return proc


def start_gateway() -> subprocess.Popen:
    proc = subprocess.Popen(
        [sys.executable, "api_gateway.py"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return proc


def cleanup():
    for p in processes:
        try:
            p.terminate()
            p.wait(timeout=3)
        except Exception:
            p.kill()


def section(title: str):
    print(f"\n{'─'*55}")
    print(f"  {title}")
    print(f"{'─'*55}")


async def send_requests(client: httpx.AsyncClient, n: int) -> dict:
    """Fire n requests at the gateway, return distribution stats."""
    results: dict[str, int] = {}
    errors = 0
    latencies = []

    async def fire(path: str):
        nonlocal errors
        start = time.perf_counter()
        try:
            resp = await client.get(f"http://localhost:{GATEWAY_PORT}{path}")
            elapsed = time.perf_counter() - start
            latencies.append(elapsed)
            if resp.status_code == 200:
                data = resp.json()
                handler = data.get("handled_by", "unknown")
                results[handler] = results.get(handler, 0) + 1
            else:
                errors += 1
        except Exception:
            errors += 1

    tasks = [fire(random.choice(PATHS)) for _ in range(n)]
    await asyncio.gather(*tasks)

    return {
        "distribution": results,
        "errors": errors,
        "total": n,
        "avg_latency_ms": statistics.mean(latencies) * 1000 if latencies else 0,
        "p99_latency_ms": (sorted(latencies)[int(len(latencies) * 0.99)] * 1000) if latencies else 0,
    }


def print_stats(stats: dict, label: str):
    print(f"\n  [{label}]")
    dist = stats["distribution"]
    total_ok = sum(dist.values())
    if dist:
        counts = list(dist.values())
        cv = statistics.stdev(counts) / statistics.mean(counts) if statistics.mean(counts) > 0 else 0
        for handler in sorted(dist):
            bar = "█" * int(40 * dist[handler] / max(counts)) if max(counts) > 0 else ""
            print(f"    {handler:<25} {dist[handler]:>4} reqs  {bar}")
        print(f"    CV (evenness): {cv:.3f}  |  errors: {stats['errors']}  |  avg latency: {stats['avg_latency_ms']:.1f}ms")
    else:
        print(f"    No successful responses (errors: {stats['errors']})")


async def run_demo():
    section("Starting 6 backends + gateway")
    for port, name in BACKENDS:
        p = start_backend(port, name)
        processes.append(p)
        print(f"    backend [{name}] on :{port} (pid {p.pid})")

    gw = start_gateway()
    processes.append(gw)
    print(f"    gateway on :{GATEWAY_PORT} (pid {gw.pid})")

    # Wait for everything to come up
    print("\n  Waiting for services to be ready...")
    await asyncio.sleep(3)

    async with httpx.AsyncClient(timeout=10.0) as client:

        # Normal traffic
        section("Phase 1: Normal Traffic")
        print(f"  Sending {REQUEST_COUNT} requests across all backends...\n")
        stats = await send_requests(client, REQUEST_COUNT)
        print_stats(stats, "All backends healthy")

        # Kill a server
        section("Phase 2: Kill a Backend")
        victim_port = 8003
        print(f"  Marking :{victim_port} as DOWN via admin API...")
        await client.post(f"http://localhost:{GATEWAY_PORT}/_admin/down/{victim_port}")
        await asyncio.sleep(0.5)

        stats = await send_requests(client, REQUEST_COUNT)
        print_stats(stats, f"After killing :{victim_port}")

        # Kill another
        section("Phase 3: Kill Another Backend")
        victim_port2 = 8005
        print(f"  Marking :{victim_port2} as DOWN...")
        await client.post(f"http://localhost:{GATEWAY_PORT}/_admin/down/{victim_port2}")
        await asyncio.sleep(0.5)

        stats = await send_requests(client, REQUEST_COUNT)
        print_stats(stats, f"After killing :{victim_port} and :{victim_port2}")

        # Bring them back
        section("Phase 4: Recovery")
        print(f"  Bringing :{victim_port} and :{victim_port2} back UP...")
        await client.post(f"http://localhost:{GATEWAY_PORT}/_admin/up/{victim_port}")
        await client.post(f"http://localhost:{GATEWAY_PORT}/_admin/up/{victim_port2}")
        await asyncio.sleep(0.5)

        stats = await send_requests(client, REQUEST_COUNT)
        print_stats(stats, "All backends restored")

        # Show admin status
        section("Final Admin Status")
        resp = await client.get(f"http://localhost:{GATEWAY_PORT}/_admin/status")
        print(f"  {json.dumps(resp.json(), indent=2)}")

    section("Done — Cleaning Up")


if __name__ == "__main__":
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\n  Interrupted.")
    finally:
        cleanup()
        print("  All processes terminated.\n")