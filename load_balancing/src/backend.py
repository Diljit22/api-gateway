import sys
import asyncio
import random
from fastapi import FastAPI

"""
Generic backend that identifies itself by port.

Usage:
    python backend.py <port> <service_name>
    python backend.py 8001 users
    python backend.py 8004 orders

The response includes which port handled it, so you can see
the load balancer distributing traffic.
"""

port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
name = sys.argv[2] if len(sys.argv) > 2 else "generic"

app = FastAPI(title=f"{name} backend :{port}")


@app.get("/health")
async def health():
    return {"status": "ok", "port": port, "service": name}


@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def catch_all(full_path: str = ""):
    # Simulate some variable latency so least-connections has something to work with
    await asyncio.sleep(random.uniform(0.01, 0.05))
    return {
        "service": name,
        "handled_by": f"localhost:{port}",
        "path_received": "/" + full_path if full_path else "/",
    }


if __name__ == "__main__":
    import uvicorn
    print(f"Backend [{name}] starting on http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")