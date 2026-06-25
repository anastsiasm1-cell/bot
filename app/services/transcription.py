"""
Сервис расшифровки голосовых/аудио/видео сообщений через локальный STT-сервис
"""
import aiohttp
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from loguru import logger

from app.config import settings


class TranscriptionError(Exception):
    """Ошибка при обращении к сервису распознавания речи"""


class TranscriptionService:
    """Сервис для расшифровки медиафайлов в текст"""

    async def transcribe_telegram_file(self, bot: Bot, file_id: str) -> str:
        """
        Скачивает файл из Telegram и отправляет его на распознавание
        в локальный сервис transcriber

        Args:
            bot: Экземпляр бота
            file_id: file_id голосового/аудио/видео сообщения

        Returns:
            Распознанный текст

        Raises:
            TranscriptionError: если сервис распознавания недоступен или вернул ошибку
        """
        try:
            file_bytes = await bot.download(file_id)
        except TelegramBadRequest as exc:
            if "file is too big" in str(exc):
                raise TranscriptionError("file_too_big") from exc
            raise TranscriptionError(str(exc)) from exc

        timeout = aiohttp.ClientTimeout(total=settings.transcriber_timeout)
        form = aiohttp.FormData()
        form.add_field(
            "file",
            file_bytes,
            filename="audio.bin",
            content_type="application/octet-stream",
        )

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{settings.transcriber_url}/transcribe", data=form
                ) as response:
                    if response.status != 200:
                        body = await response.text()
                        logger.error(f"Transcriber service error {response.status}: {body}")
                        raise TranscriptionError(f"Transcriber service returned {response.status}")
                    data = await response.json()
                    return data.get("text", "")
        except aiohttp.ClientError as exc:
            logger.error(f"Failed to reach transcriber service: {exc}")
            raise TranscriptionError("Transcriber service unreachable") from exc
        except TimeoutError as exc:
            logger.error("Transcriber service timed out")
            raise TranscriptionError("Transcriber service timed out") from exc


transcription_service = TranscriptionService()
