from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.upload import router as upload_router
from app.api.search import router as search_router
from app.api.teach import router as teach_router
from app.api.chat import router as chat_router
from app.api.quiz import router as quiz_router
from app.api.arc0 import router as arc0_router


app = FastAPI(
    title="ARC LEARNS API",
    description="AI Powered Learning Platform",
    version="1.0.0"
)


import os

# ============================================================
# CORS CONFIGURATION
# ============================================================

cors_env = os.getenv("CORS_ORIGINS", "")
allowed_origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "https://arc-learns.onrender.com",
    "https://arc-learns-api.onrender.com",
]
if cors_env:
    for origin in cors_env.split(","):
        if origin.strip() and origin.strip() not in allowed_origins:
            allowed_origins.append(origin.strip())

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.onrender\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROUTES
# ============================================================

app.include_router(upload_router)

app.include_router(search_router)

app.include_router(teach_router)

app.include_router(chat_router)

app.include_router(quiz_router)

app.include_router(arc0_router)


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "message": "Welcome to ARC LEARNS",
        "status": "Backend Running Successfully"
    }


@app.get("/status")
def status():
    from app.services.ai_manager import get_provider_status
    return {
        "status": "online",
        "platform": "ARC LEARN",
        "providers": get_provider_status()
    }