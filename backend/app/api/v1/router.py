from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin_review,
    auth,
    certificates,
    chat,
    fields,
    quizzes,
    resources,
    roadmaps,
    specializations,
    tasks,
    users,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(fields.router)
api_router.include_router(specializations.router)
api_router.include_router(roadmaps.router)
api_router.include_router(resources.router)
api_router.include_router(quizzes.router)
api_router.include_router(tasks.router)
api_router.include_router(certificates.router)
api_router.include_router(chat.router)
api_router.include_router(admin_review.router)