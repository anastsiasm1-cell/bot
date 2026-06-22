"""
Миграция для добавления таблицы transcription_logs
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection
from loguru import logger

from app.database.migrations.base import Migration


class AddTranscriptionLogsMigration(Migration):
    """Миграция для добавления таблицы логов расшифровки медиа"""

    def get_version(self) -> str:
        return "20260622_000004"

    def get_description(self) -> str:
        return "Add transcription_logs table"

    async def check_can_apply(self, connection: AsyncConnection) -> bool:
        """Проверяем, нужно ли создавать таблицу"""
        result = await connection.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'transcription_logs'
            );
        """))
        return not result.scalar()

    async def upgrade(self, connection: AsyncConnection) -> None:
        """Создание таблицы для логов расшифровки"""

        await connection.execute(text("""
            CREATE TABLE IF NOT EXISTS transcription_logs (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                media_type VARCHAR(20) NOT NULL,
                text_length INTEGER,
                status VARCHAR(20) DEFAULT 'success',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """))

        await connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_transcription_logs_user_id ON transcription_logs(user_id);
        """))
        await connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_transcription_logs_created_at ON transcription_logs(created_at);
        """))

        logger.info("✅ Created transcription_logs table")

    async def downgrade(self, connection: AsyncConnection) -> None:
        """Откат миграции - удаление таблицы"""
        await connection.execute(text("DROP TABLE IF EXISTS transcription_logs CASCADE;"))
        logger.info("✅ Dropped transcription_logs table")
