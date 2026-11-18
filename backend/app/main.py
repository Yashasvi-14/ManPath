
from fastapi import FastAPI

from app.api.predictions import router as prediction_router
from app.api.assessments import router as assessments_router
from app.api.auth import router as auth_router

app = FastAPI(
    title="ManPath API",
    description="An explainable student well-being companion.",
    version="0.1.0",
)

app.include_router(prediction_router)

app.include_router(assessments_router)

app.include_router(auth_router)

@app.get("/")
def root():
    return {
        "message": "Welcome to ManPath API",
        "status": "running",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
