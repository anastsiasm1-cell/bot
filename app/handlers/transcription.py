"""
Хендлер автоматической расшифровки голосовых/аудио/видео сообщений
"""
from html import escape

from aiogram import Router, F
from aiogram.types import Message
from loguru import logger

from app.database import db
from app.services import transcription_service, TranscriptionError
from app.utils import split_text

router = Router()


def _get_media_info(message: Message):
    """Определяет file_id и тип медиа для входящего сообщения"""
    if message.voice:
        return message.voice.file_id, "voice"
    if message.audio:
        return message.audio.file_id, "audio"
    if message.video:
        return message.video.file_id, "video"
    if message.video_note:
        return message.video_note.file_id, "video_note"
    return None, None


@router.message(F.voice | F.audio | F.video | F.video_note)
async def transcribe_media(message: Message):
    """Автоматически распознаёт речь в голосовых/аудио/видео сообщениях"""
    file_id, media_type = _get_media_info(message)
    if not file_id:
        return

    status_message = await message.reply("🎙 Распознаю текст...")

    try:
        text = await transcription_service.transcribe_telegram_file(message.bot, file_id)
    except TranscriptionError as exc:
        logger.error(f"Transcription failed for user {message.from_user.id}: {exc}")
        await status_message.edit_text(
            "❌ Не удалось распознать речь. Сервис расшифровки временно недоступен, попробуйте позже."
        )
        await db.log_transcription(message.from_user.id, media_type, status="error")
        return

    if not text.strip():
        await status_message.edit_text("🤷 Не удалось распознать речь в этом сообщении.")
        await db.log_transcription(message.from_user.id, media_type, status="empty")
        return

    chunks = split_text(text)
    await status_message.edit_text(f"📝 <b>Расшифровка:</b>\n\n{escape(chunks[0])}")
    for chunk in chunks[1:]:
        await message.answer(escape(chunk))

    await db.log_transcription(message.from_user.id, media_type, text_length=len(text), status="success")
