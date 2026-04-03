from fastapi import FastAPI, Request
from fastapi.responses import Response
from contextlib import asynccontextmanager
import httpx
from radix_trie import RadixRouter

# Global HTTP client
http_client = None

# Initialize our new Radix Trie Router
router = RadixRouter()
router.insert("/users", "http://localhost:8001")
router.insert("/orders", "http://localhost:8002")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    http_client = httpx.AsyncClient()
    yield
    await http_client.aclose()

app = FastAPI(title="Toy API Gateway - Radix Trie Router", lifespan=lifespan)

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def gateway(request: Request, path: str):
    full_path = "/" + path if path else "/"

    # Radix Trie look up
    matched_backend, remaining_path = router.search(full_path)

    if not matched_backend:
        return Response(content=b"404 - No route matched", status_code=404)

    # Build target URL
    target_url = matched_backend.rstrip("/") + (remaining_path if remaining_path != "/" else "")

    # Proxy Request (Same as pass_through)
    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in ("host", "content-length")
    }
    body = await request.body()

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
    print("Toy API Gateway (Trie Routing) starting on http://0.0.0.0:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")