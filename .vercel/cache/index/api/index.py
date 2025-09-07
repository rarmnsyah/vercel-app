from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="FastAPI on Vercel")

@app.get("/")
def main():
    return {"hello": "world", "docs": "/docs"}

@app.get("/api")
def root():
    return {"ok": True, "msg": "FastAPI running on Vercel"}

@app.get("/api/health")
def health():
    return {"status": "healthy"}
    