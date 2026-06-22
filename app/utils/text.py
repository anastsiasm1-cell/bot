"""
Текстовые утилиты
"""
from typing import List


def split_text(text: str, max_length: int = 4000) -> List[str]:
    """
    Разбивает текст на части не длиннее max_length символов,
    стараясь резать по границам предложений/пробелов

    Args:
        text: исходный текст
        max_length: максимальная длина одной части (лимит Telegram - 4096)

    Returns:
        Список частей текста
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    remaining = text
    while len(remaining) > max_length:
        split_at = remaining.rfind(". ", 0, max_length)
        if split_at == -1:
            split_at = remaining.rfind(" ", 0, max_length)
        if split_at == -1:
            split_at = max_length

        chunks.append(remaining[:split_at + 1].strip())
        remaining = remaining[split_at + 1:].strip()

    if remaining:
        chunks.append(remaining)

    return chunks
