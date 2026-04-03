from fastapi import FastAPI

app = FastAPI(title="Orders Backend")

@app.api_route("/{full_path:path}")
async def all_paths(full_path: str = ""):
    return {
        "service": "Orders Backend",
        "message": "Hello from orders service!",
        "path_received": "/" + full_path if full_path else "/"
    }

if __name__ == "__main__":
    import uvicorn
    print("Orders Backend starting on http://localhost:8002")
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")