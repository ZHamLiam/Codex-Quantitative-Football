from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from config import settings

app = FastAPI(title="量化足球系统")

@app.get("/api/health")
def health():
    return {"status": "ok"}

from api import factors, profiles, matches, analysis, llm
app.include_router(factors.router)
app.include_router(profiles.router)
app.include_router(matches.router)
app.include_router(analysis.router)
app.include_router(llm.router)

app.mount("/", StaticFiles(directory="web", html=True), name="web")

