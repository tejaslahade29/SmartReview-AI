from fastapi import APIRouter

from app.api.v1.endpoints import documents, health, reviews

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(reviews.router, tags=["reviews"])
