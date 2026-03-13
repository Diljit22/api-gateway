from fastapi import FastAPI, Request
from fastapi.responses import Response
from contextlib import asynccontextmanager
import httpx

# Global HTTP client for connection pooling
http_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    # Instantiate a single client to reuse TCP connections
    http_client = httpx.AsyncClient()
    yield
    await http_client.aclose()

app = FastAPI(title="Toy API Gateway - Simplest Version", lifespan=lifespan)

routes = {
    "/users":  "http://localhost:8001",
    "/orders": "http://localhost:8002",
}

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def gateway(request: Request, path: str):
    full_path = "/" + path if path else "/"

    # Find longest matching prefix
    matched_backend = None
    matched_prefix = ""
    for prefix in sorted(routes.keys(), key=len, reverse=True):
        if full_path.startswith(prefix):
            matched_backend = routes[prefix]
            matched_prefix = prefix
            break

    if matched_backend is None:
        return Response(content=b"404 - No route matched", status_code=404)

    # Build target URL for the backend
    remaining = full_path[len(matched_prefix):] or "/"
    target_url = matched_backend.rstrip("/") + remaining

    # Extract headers
    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in ("host", "content-length")
    }
    
    # read the body for a HTTP method (may be "")
    body = await request.body()

    # Proxy the request using the global connection pool
    resp = await http_client.request(
        method=request.method,
        url=target_url,
        headers=headers,
        content=body,
        params=request.query_params,
    )

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers={k: v for k, v in resp.headers.items()
                 if k.lower() not in ("content-length", "transfer-encoding")}
    )

if __name__ == "__main__":
    import uvicorn
    print("Toy API Gateway starting on http://0.0.0.0:8080")
    print("Registered routes:")
    for p, u in routes.items():
        print(f"  {p}  →  {u}")
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")