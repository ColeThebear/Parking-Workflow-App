from fastapi import APIRouter

from . import sessions, search, import_, historic, analytics

router = APIRouter(prefix="/operator", tags=["operator"])

router.include_router(sessions.router)
router.include_router(search.router)
router.include_router(import_.router)
router.include_router(historic.router)
router.include_router(analytics.router)
