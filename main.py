from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from config import settings

app = FastAPI(title="量化足球系统")

@app.get("/api/health")
def health():
    return {"status": "ok"}

app.mount("/", StaticFiles(directory="web", html=True), name="web")
