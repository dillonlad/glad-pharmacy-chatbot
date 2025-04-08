from fastapi import APIRouter
from routers.staff.clock.api_router import router as clock_router
from routers.staff.members.api_router import router as members_router

router = APIRouter(prefix="/staff")
router.include_router(clock_router)
router.include_router(members_router)