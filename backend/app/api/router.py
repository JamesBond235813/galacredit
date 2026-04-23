from fastapi import APIRouter
from app.api.endpoints import auth, user, loan, admin

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(user.router, prefix="/user", tags=["user"])
router.include_router(loan.router, prefix="/loan", tags=["loan"])
router.include_router(admin.router, prefix="/admin", tags=["admin"])
