from fastapi import FastAPI

app = FastAPI(title="Users Backend")

@app.api_route("/{full_path:path}")
async def all_paths(full_path: str = ""):
    return {
        "service": "Users Backend",
        "message": "Hello from users service!",
        "path_received": "/" + full_path if full_path else "/"
    }

if __name__ == "__main__":
    import uvicorn
    print("Users Backend starting on http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")