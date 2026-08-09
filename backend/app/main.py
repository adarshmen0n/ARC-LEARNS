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


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://arc-learns.onrender.com"
    ],

    allow_credentials=False,

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