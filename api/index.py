from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="FastAPI on Vercel")

@app.get("/api")
def root():
    return {"ok": True, "msg": "FastAPI running on Vercel"}

@app.get("/api/health")
def health():
    return JSONResponse({"status": "healthy"})

@app.get("/")
def main():
    return JSONResponse({"status": "healthy"})
    