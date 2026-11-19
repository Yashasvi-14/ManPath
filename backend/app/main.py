
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

from app.api.predictions import router as prediction_router
from app.api.assessments import router as assessments_router
from app.api.auth import router as auth_router
from app.api.analytics import router as analytics_router
from app.api import chat

app = FastAPI(
    title="ManPath API",
    description="An explainable student well-being companion.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(prediction_router)
app.include_router(assessments_router)
app.include_router(auth_router)
app.include_router(analytics_router)
app.include_router(chat.router)

@app.get("/")
def root():
    return {
        "message": "Welcome to ManPath API",
        "status": "running",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
