import os

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse

from scan import scan

FRONTEND = os.getenv("FRONTEND", "")

app = FastAPI(title="DockNav", version="1.0.0")
_cache = {"data": None}


@app.get("/api/health")
async def health():
    return {"ok": True}


@app.get("/api/services")
async def services(refresh: bool = False):
    if refresh or _cache["data"] is None:
        try:
            _cache["data"] = await scan()
        except FileNotFoundError:
            return JSONResponse(
                {"detail": "docker socket not found - mount /var/run/docker.sock"}, 503)
        except Exception as e:
            return JSONResponse({"detail": f"docker scan failed: {e}"}, 502)
    return _cache["data"]


if FRONTEND and os.path.isdir(FRONTEND):
    ROOT = os.path.realpath(FRONTEND)

    @app.get("/{full_path:path}")
    async def spa(full_path: str):
        target = os.path.realpath(os.path.join(ROOT, full_path))
        inside = target == ROOT or target.startswith(ROOT + os.sep)
        if full_path and inside and os.path.isfile(target):
            return FileResponse(target)
        return FileResponse(os.path.join(ROOT, "index.html"))
