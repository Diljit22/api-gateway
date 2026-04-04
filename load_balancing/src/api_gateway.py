from fastapi import FastAPI, Request
from fastapi.responses import Response, JSONResponse
from contextlib import asynccontextmanager
import httpx

from radix_trie import RadixRouter
from load_balancer import LeastConnections, ConsistentHashLB, RoundRobin, LoadBalancer

# Each route prefix now maps to MULTIPLE backends
ROUTE_BACKENDS = {
    "/users":  ["http://localhost:8001", "http://localhost:8003", "http://localhost:8005"],
    "/orders": ["http://localhost:8002", "http://localhost:8004", "http://localhost:8006"],
}

# Choose your strategy: "round_robin", "least_conn", "consistent_hash"
LB_STRATEGY = "least_conn"
# For consistent hashing: virtual nodes per server (0 = no vnodes)
VNODES = 150

# Setup

http_client = None

# Radix Trie still handles prefix matching (route -> service group)
router = RadixRouter()

# One load balancer per service group
balancers: dict[str, LoadBalancer] = {}

def _make_balancer(backends: list[str]) -> LoadBalancer:
    if LB_STRATEGY == "round_robin":
        return RoundRobin(backends)
    elif LB_STRATEGY == "least_conn":
        return LeastConnections(backends)
    elif LB_STRATEGY == "consistent_hash":
        return ConsistentHashLB(backends, num_vnodes=VNODES)
    raise ValueError(f"Unknown strategy: {LB_STRATEGY}")

for prefix, backends in ROUTE_BACKENDS.items():
    # The trie stores the prefix key; we look up the balancer separately
    router.insert(prefix, prefix)
    balancers[prefix] = _make_balancer(backends)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    http_client = httpx.AsyncClient(timeout=5.0)
    yield
    await http_client.aclose()

app = FastAPI(title="Toy API Gateway - Load Balanced", lifespan=lifespan)


# Admin endpoints (for the demo + chaos tooling)

@app.get("/_admin/status")
async def admin_status():
    """Peek at which backends are healthy and active connections."""
    status = {}
    for prefix, lb in balancers.items():
        info = {
            "strategy": LB_STRATEGY,
            "healthy": sorted(lb.healthy),
            "down": sorted(set(lb.all_backends) - lb.healthy),
        }
        if isinstance(lb, LeastConnections):
            info["active_connections"] = lb.get_connections()
        status[prefix] = info
    return status

@app.post("/_admin/down/{backend_port:int}")
async def admin_mark_down(backend_port: int):
    """Simulate a backend going down."""
    target = f"http://localhost:{backend_port}"
    hit = False
    for lb in balancers.values():
        if target in lb.all_backends:
            lb.mark_down(target)
            hit = True
    if not hit:
        return JSONResponse({"error": f"port {backend_port} not found"}, status_code=404)
    return {"marked_down": target}

@app.post("/_admin/up/{backend_port:int}")
async def admin_mark_up(backend_port: int):
    """Bring a backend back up."""
    target = f"http://localhost:{backend_port}"
    for lb in balancers.values():
        if target in lb.all_backends:
            lb.mark_up(target)
    return {"marked_up": target}


# Main proxy route

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def gateway(request: Request, path: str):
    full_path = "/" + path if path else "/"

    # Trie lookup -> which service group?
    prefix_key, remaining_path = router.search(full_path)
    if not prefix_key or prefix_key not in balancers:
        return Response(content=b"404 - No route matched", status_code=404)

    lb = balancers[prefix_key]

    # Load balancer picks a specific backend
    # Use the full path as the hash key (for consistent hashing stickiness)
    backend = lb.pick(request_key=full_path)
    if not backend:
        return Response(content=b"503 - No healthy backends", status_code=503)

    # Proxy the request
    target_url = backend.rstrip("/") + (remaining_path if remaining_path != "/" else "")

    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in ("host", "content-length")
    }
    body = await request.body()

    lb.on_request_start(backend)
    try:
        resp = await http_client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
            params=request.query_params,
        )
    except httpx.ConnectError:
        # Backend is actually unreachable. mark it down and retry once
        lb.on_request_end(backend)
        lb.mark_down(backend)
        fallback = lb.pick(request_key=full_path)
        if not fallback:
            return Response(content=b"503 - All backends down", status_code=503)
        target_url = fallback.rstrip("/") + (remaining_path if remaining_path != "/" else "")
        lb.on_request_start(fallback)
        try:
            resp = await http_client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                params=request.query_params,
            )
        except httpx.ConnectError:
            lb.on_request_end(fallback)
            lb.mark_down(fallback)
            return Response(content=b"503 - Backends unreachable", status_code=503)
        lb.on_request_end(fallback)
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers={k: v for k, v in resp.headers.items()
                     if k.lower() not in ("content-length", "transfer-encoding")},
        )

    lb.on_request_end(backend)

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers={k: v for k, v in resp.headers.items()
                 if k.lower() not in ("content-length", "transfer-encoding")},
    )


if __name__ == "__main__":
    import uvicorn
    print(f"Toy API Gateway (Load Balanced — {LB_STRATEGY}) on http://0.0.0.0:8080")
    print(f"Virtual nodes: {VNODES}")
    print("Registered routes:")
    for prefix, backends in ROUTE_BACKENDS.items():
        print(f"  {prefix}  →  {backends}")
    print("\nAdmin endpoints:")
    print("  GET  /_admin/status")
    print("  POST /_admin/down/{port}")
    print("  POST /_admin/up/{port}")
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")