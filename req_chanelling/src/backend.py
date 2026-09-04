import sys
import asyncio
import random
from fastapi import FastAPI

port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
name = sys.argv[2] if len(sys.argv) > 2 else "generic"

app = FastAPI(title=f"{name} backend :{port}")

@app.get("/health")
async def health():
    return {"status": "ok", "port": port, "service": name}

@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def catch_all(full_path: str = ""):
    # Deliberate simulated latency to capture the request lifecycle
    await asyncio.sleep(1.0)
    return {
        "service": name,
        "handled_by": f"localhost:{port}",
        "path_received": "/" + full_path if full_path else "/",
        # Helpful to verify coalescing (same random_id = served by same backend request)
        "random_id": random.randint(1000, 9999) 
    }

if __name__ == "__main__":
    import uvicorn
    print(f"Backend [{name}] starting on http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")