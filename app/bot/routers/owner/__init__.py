from aiogram import Router

from app.bot.routers.owner.setup_wizard import router as wizard_router
from app.bot.routers.owner.settings import router as settings_router

router = Router()
router.include_router(wizard_router)
router.include_router(settings_router)
