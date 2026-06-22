"""
Handlers package
"""
from aiogram import Dispatcher

from .start import router as start_router
from .help import router as help_router
from .admin import combined_router as admin_router
from .transcription import router as transcription_router


def setup_routers(dp: Dispatcher) -> None:
    """Настройка всех роутеров"""
    # admin_router подключается первым, чтобы FSM-сценарий рассылки
    # (приём голосовых/видео для broadcast) перехватывал такие сообщения
    # раньше, чем transcription_router
    dp.include_router(admin_router)
    dp.include_router(start_router)
    dp.include_router(help_router)
    dp.include_router(transcription_router)
