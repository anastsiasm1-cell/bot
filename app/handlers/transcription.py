"""
Хендлер автоматической расшифровки голосовых/аудио/видео сообщений
"""
from html import escape
from pathlib import Path

from aiogram import Router, F
from aiogram.types import BufferedInputFile, Document, Message
from loguru import logger

from app.database import db
from app.services import transcription_service, TranscriptionError
from app.utils import build_transcript_docx, split_text

router = Router()

# Расширения файлов, которые пытаемся расшифровать даже без корректного MIME-типа.
# ".null" — Telegram ставит это расширение для голосовых/аудио файлов без метаданных.
_MEDIA_EXTENSIONS = frozenset({
    ".mp3", ".ogg", ".oga", ".opus", ".wav", ".flac", ".aac", ".m4a", ".wma", ".aiff",
    ".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".m4v", ".3gp", ".webm",
    ".null",
})


def _is_media_document(doc: Document | None) -> bool:
    if not doc:
        return False
    if doc.mime_type and (doc.mime_type.startswith("audio/") or doc.mime_type.startswith("video/")):
        return True
    if doc.file_name:
        return Path(doc.file_name).suffix.lower() in _MEDIA_EXTENSIONS
    return False


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
    if _is_media_document(message.document):
        return message.document.file_id, "document"
    return None, None


@router.message(
    F.voice | F.audio | F.video | F.video_note
    | F.document.func(_is_media_document)
)
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
        if "file_too_big" in str(exc):
            await status_message.edit_text(
                "❌ Файл слишком большой. Telegram позволяет расшифровывать файлы до 20 МБ. "
                "Попробуйте отправить более короткое видео или сжать файл."
            )
        else:
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

    docx_buffer = build_transcript_docx(text)
    await message.answer_document(
        BufferedInputFile(docx_buffer.read(), filename="Расшифровка.docx")
    )

    await db.log_transcription(message.from_user.id, media_type, text_length=len(text), status="success")
