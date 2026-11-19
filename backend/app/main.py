
from fastapi import FastAPI

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
