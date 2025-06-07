from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description="FastAPI Microservices Project",
)


@app.get("/")
async def root():
    return {"message": "FastAPI server is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
