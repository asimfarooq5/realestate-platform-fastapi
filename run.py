import os
import uvicorn

if __name__ == "__main__":
    reload = os.environ.get("RELOAD", "false").lower() == "true"
    uvicorn.run(
        "app.main:app",
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "8000")),
        reload=reload,
        log_level=os.environ.get("LOG_LEVEL", "info"),
    )
