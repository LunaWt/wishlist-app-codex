from fastapi import APIRouter

from app.api.routes import auth, items, public, system, wishlists, ws

api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(auth.router)
api_router.include_router(wishlists.router)
api_router.include_router(public.router)
api_router.include_router(items.router)
api_router.include_router(ws.router)
