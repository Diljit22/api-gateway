from fastapi import FastAPI, Request
from fastapi.responses import Response, JSONResponse
from contextlib import asynccontextmanager
import asyncio
import httpx

from radix_trie import RadixRouter
from load_balancer import LeastConnections, ConsistentHashLB, RoundRobin, LoadBalancer
from request_channeler import RequestChanneler
from cache_manager import CacheLayer
from auth_manager import AuthManager, JWTTokenHelper
from rate_limiter import RateLimiter

ROUTE_BACKENDS = {
    "/users":  ["http://localhost:8001", "http://localhost:8003", "http://localhost:8005"],
    "/orders": ["http://localhost:8002", "http://localhost:8004", "http://localhost:8006"],
}

LB_STRATEGY = "least_conn"
VNODES = 150

http_client = None
router = RadixRouter()
balancers: dict[str, LoadBalancer] = {}

# Initialize gateway components
channeler = RequestChanneler(max_concurrent_per_backend=3)
cache = CacheLayer(default_ttl=10.0)
auth_manager = AuthManager()
rate_limiter = RateLimiter()

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

async def periodic_cleanup():
    try:
        while True:
            await asyncio.sleep(5)
            cache.prune()
            # Prune inactive buckets untouched for more than 60 seconds
            rate_limiter.prune(max_idle_seconds=60.0)
    except asyncio.CancelledError:
        pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    http_client = httpx.AsyncClient(timeout=10.0)
    cleanup_task = asyncio.create_task(periodic_cleanup())
    yield
    cleanup_task.cancel()
    try:
        await cleanup_task
    except Exception:
        pass
    await http_client.aclose()

app = FastAPI(title="Toy API Gateway - Tiered Rate Limiting", lifespan=lifespan)

# Middleware: Authentication, Rate Limiting, & Authorization checks
@app.middleware("http")
async def gateway_middleware(request: Request, call_next):
    # 1. Edge Authentication (Verifies JWT)
    auth_header = request.headers.get("Authorization")
    user_info = auth_manager.authenticate(auth_header)
    request.state.user = user_info
    
    # Extract identity metadata to assign the rate-limiting key & tier
    if user_info:
        rate_key = user_info["user_id"]
        roles = user_info.get("roles", [])
        tier = "premium" if "admin" in roles else "basic"
    else:
        # Fallback to Client IP for anonymous endpoints
        rate_key = request.client.host if request.client else "unknown"
        tier = "anonymous"

    # 2. Enforce Tier-Based Rate Limiting
    allowed, remaining, retry_after = rate_limiter.is_allowed(rate_key, tier=tier)
    if not allowed:
        return Response(
            content=b"429 - Too Many Requests (Rate limit exceeded)",
            status_code=429,
            headers={
                "Retry-After": f"{retry_after:.2f}",
                "X-RateLimit-Limit": f"{rate_limiter.tiers[tier][0]}",
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Tier": tier
            }
        )

    # 3. Enforce Prefix-Based RBAC
    if not auth_manager.is_authorized(user_info, request.url.path):
        return Response(
            content=b"403 - Forbidden (Insufficient permissions or unauthorized)",
            status_code=403
        )

    response = await call_next(request)
    
    # Inject compliance headers to the final response
    response.headers["X-RateLimit-Limit"] = f"{rate_limiter.tiers[tier][0]}"
    response.headers["X-RateLimit-Remaining"] = f"{remaining}"
    response.headers["X-RateLimit-Tier"] = tier
    return response

@app.get("/_admin/status")
async def admin_status():
    status = {}
    for prefix, lb in balancers.items():
        info = {
            "strategy": LB_STRATEGY,
            "healthy": sorted(lb.healthy),
            "down": sorted(set(lb.all_backends) - lb.healthy),
            "cached_items_count": len(cache.store)
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

    # Cache Lookup (GET requests only)
    cache_key = f"{request.method}:{full_path}:{request.query_params}"
    if request.method == "GET":
        cached = cache.get(cache_key)
        if cached is not None:
            content, status_code, resp_headers = cached
            headers_to_send = dict(resp_headers)
            headers_to_send["X-Cache"] = "HIT"
            return Response(content=content, status_code=status_code, headers=headers_to_send)

    backend = lb.pick(request_key=full_path)
    if not backend:
        return Response(content=b"503 - No healthy backends", status_code=503)

    target_url = backend.rstrip("/") + (remaining_path if remaining_path != "/" else "")

    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in ("host", "content-length")
    }
    body = await request.body()

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

    coalesce_key = f"{request.method}:{full_path}:{request.query_params}"
    should_coalesce = request.method == "GET"

    try:
        (status_code, content, resp_headers), was_coalesced = await channeler.execute(
            key=coalesce_key,
            backend=backend,
            request_func=perform_request,
            coalesce=should_coalesce
        )
    except Exception as e:
        return Response(content=f"500 - Internal Gateway Error: {str(e)}".encode(), status_code=500)

    if request.method == "GET" and status_code == 200:
        cache.set(cache_key, content, status_code, resp_headers)

    headers_to_send = {
        k: v for k, v in resp_headers.items()
        if k.lower() not in ("content-length", "transfer-encoding")
    }
    
    headers_to_send["X-Cache"] = "MISS"
    if was_coalesced:
        headers_to_send["X-Request-Coalesced"] = "TRUE"

    return Response(
        content=content,
        status_code=status_code,
        headers=headers_to_send
    )

if __name__ == "__main__":
    import uvicorn
    # Generate live operational JWT tokens on start for copying
    helper = JWTTokenHelper()
    user_token = helper.create_token({"user_id": "alice", "roles": ["user"]})
    admin_token = helper.create_token({"user_id": "bob", "roles": ["user", "admin"]})
    
    print("\n" + "=" * 80)
    print("  Toy API Gateway with JWT & Tiered Rate Limiting")
    print("=" * 80)
    print("  Copy-paste these live tokens into rate_limiting/demo.http for testing:")
    print(f"\n  Valid User Token (Tier: basic):\n  Bearer {user_token}")
    print(f"\n  Valid Admin Token (Tier: premium):\n  Bearer {admin_token}")
    print("=" * 80 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="warning")