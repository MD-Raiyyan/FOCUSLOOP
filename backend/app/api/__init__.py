"""API routing package."""
from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.users import router as users_router
from app.api.tasks import router as tasks_router
from app.api.checkins import router as checkins_router
from app.api.procrastination import router as procrastination_router
from app.api.screen_usage import router as screen_usage_router
from app.api.behavior import router as behavior_router
from app.api.experiments import router as experiments_router
from app.api.chat import router as chat_router
from app.api.profile import router as profile_router
from app.api.social import router as social_router
from app.api.auth import router as auth_router
from app.api.onboarding import router as onboarding_router

api_router = APIRouter()

# Register sub-routers
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(onboarding_router)
api_router.include_router(users_router)
api_router.include_router(tasks_router)
api_router.include_router(checkins_router)
api_router.include_router(procrastination_router)
api_router.include_router(screen_usage_router)
api_router.include_router(behavior_router)
api_router.include_router(experiments_router)
api_router.include_router(chat_router)
api_router.include_router(profile_router)
api_router.include_router(social_router)

__all__ = ["api_router"]
