from aiogram import Router

from app.routes.start import router as start_router

router = Router()

router.include_routers(
    start_router,
)