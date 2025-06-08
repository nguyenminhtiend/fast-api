from fastapi import APIRouter
from app.features.auth.routes import router as auth_router

# Main API v1 router
api_router = APIRouter(prefix="/api/v1")

# Include feature routers
api_router.include_router(auth_router)

# You can add more feature routers here as you implement them:
# api_router.include_router(users_router)
# api_router.include_router(projects_router)
# api_router.include_router(tasks_router)
# api_router.include_router(comments_router)
# api_router.include_router(teams_router)
