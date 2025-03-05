from app.handlers.admin import admin_router
from app.handlers.feedback import feedback_router
from app.handlers.user import user_router

__all__ = ["admin_router", "feedback_router", "user_router"]
