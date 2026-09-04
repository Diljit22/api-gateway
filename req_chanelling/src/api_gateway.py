from fastapi import FastAPI, Request
from fastapi.responses import Response, JSONResponse
from contextlib import asynccontextmanager
import httpx

from radix_trie import RadixRouter
from load_balancer import LeastConnections, ConsistentHashLB, RoundRobin, LoadBalancer
from request_channeler import RequestChanneler

ROUTE_BACKENDS = {
    "/users":  ["http://localhost:8001", "http://localhost:8003", "http://localhost:8005"],
    "/orders": ["http://localhost:8002", "http://localhost:8004", "http://localhost:8006"],
}

LB_STRATEGY = "least_conn"
VNODES = 150

http_client = None
router = RadixRouter()
balancers: dict[str, LoadBalancer] = {}

# Initialize RequestChanneler (Bulkhead limit = 3 per backend instance)
channeler = RequestChanneler(max_concurrent_per_backend=3)

def _make_balancer(backends: list[str]) -> LoadBalancer:
    if LB_STRATEGY == "round_robin":
        return RoundRobin(backends)
    elif LB_STRATEGY == "least_conn":
        return LeastConnections(backends)
    elif LB_STRATEGY == "consistent_hash":
        return ConsistentHashLB(backends, num_vnodes=VNODES)
    raise ValueError(f"Unknown strategy: {LB_STRATEGY}")

for prefix, backends in ROUTE_BACKENDS.items():
    router.insert(prefix, prefix)
    balancers[prefix] = _make_balancer(backends)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    http_client = httpx.AsyncClient(timeout=10.0)
    yield
    await http_client.aclose()

app = FastAPI(title="Toy API Gateway - Request Channeling", lifespan=lifespan)

@app.get("/_admin/status")
async def admin_status():
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

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def gateway(request: Request, path: str):
    full_path = "/" + path if path else "/"

    prefix_key, remaining_path = router.search(full_path)
    if not prefix_key or prefix_key not in balancers:
        return Response(content=b"404 - No route matched", status_code=404)

    lb = balancers[prefix_key]

    backend = lb.pick(request_key=full_path)
    if not backend:
        return Response(content=b"503 - No healthy backends", status_code=503)

    target_url = backend.rstrip("/") + (remaining_path if remaining_path != "/" else "")

    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in ("host", "content-length")
    }
    body = await request.body()

    # Define downstream request task
    async def perform_request():
        lb.on_request_start(backend)
        try:
            resp = await http_client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                params=request.query_params,
            )
            lb.on_request_end(backend)
            return resp.status_code, resp.content, dict(resp.headers)
        except httpx.ConnectError:
            lb.on_request_end(backend)
            lb.mark_down(backend)
            
            fallback = lb.pick(request_key=full_path)
            if not fallback:
                return 503, b"503 - All backends down", {}
            
            fb_url = fallback.rstrip("/") + (remaining_path if remaining_path != "/" else "")
            lb.on_request_start(fallback)
            try:
                resp = await http_client.request(
                    method=request.method,
                    url=fb_url,
                    headers=headers,
                    content=body,
                    params=request.query_params,
                )
                lb.on_request_end(fallback)
                return resp.status_code, resp.content, dict(resp.headers)
            except httpx.ConnectError:
                lb.on_request_end(fallback)
                lb.mark_down(fallback)
                return 503, b"503 - Backends unreachable", {}

    # Define coalescing key (only GET requests should be coalesced)
    coalesce_key = f"{request.method}:{full_path}:{request.query_params}"
    should_coalesce = request.method == "GET"

    # Route through the Request Channeler
    try:
        (status_code, content, resp_headers), was_coalesced = await channeler.execute(
            key=coalesce_key,
            backend=backend,
            request_func=perform_request,
            coalesce=should_coalesce
        )
    except Exception as e:
        return Response(content=f"500 - Internal Gateway Error: {str(e)}".encode(), status_code=500)

    headers_to_send = {
        k: v for k, v in resp_headers.items()
        if k.lower() not in ("content-length", "transfer-encoding")
    }
    
    if was_coalesced:
        headers_to_send["X-Request-Coalesced"] = "TRUE"

    return Response(
        content=content,
        status_code=status_code,
        headers=headers_to_send
    )

if __name__ == "__main__":
    import uvicorn
    print(f"Toy API Gateway with Request Channeling on http://0.0.0.0:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="warning")