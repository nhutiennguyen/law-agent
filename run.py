# run.py — Entrypoint an toàn cho Render Cloud và Local
import os
import sys
import uvicorn

if __name__ == "__main__":
    port_env = os.getenv("PORT", "8000").strip()
    try:
        port = int(port_env)
    except ValueError:
        port = 8000

    host = os.getenv("HOST", "0.0.0.0")
    print(f"Starting Huynh Nguyen Khang Father on {host}:{port}...", flush=True)
    uvicorn.run("backend.main:app", host=host, port=port)
