from app.handlers.admin import admin_router
from app.handlers.ai_generator import ai_router
from app.handlers.feedback import feedback_router
from app.handlers.user import user_router

__all__ = ["admin_router", "ai_router", "feedback_router", "user_router"]
