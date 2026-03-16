"""Text chunking helpers."""

from __future__ import annotations

from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter


@dataclass(slots=True, frozen=True)
class ChunkingConfig:
    """Paragraph-first chunking settings."""

    paragraph_separator: str = "\n\n"
    max_chunk_chars: int = 1400


def split_text_into_chunks(text: str, config: ChunkingConfig) -> list[str]:
    """Split text into paragraph-based chunks.

    The first pass separates paragraphs. If a paragraph is still too long for the
    configured limit, it is further split with a character-based recursive splitter.
    """

    normalized = text.replace("\r\n", "\n").strip()
    if not normalized:
        return []

    paragraphs = [
        paragraph.strip()
        for paragraph in normalized.split(config.paragraph_separator)
        if paragraph.strip()
    ]
    if not paragraphs:
        return []

    overflow_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""],
        chunk_size=config.max_chunk_chars,
        chunk_overlap=0,
        keep_separator=True,
        strip_whitespace=True,
    )

    chunks: list[str] = []
    for paragraph in paragraphs:
        if len(paragraph) <= config.max_chunk_chars:
            chunks.append(paragraph)
            continue

        sub_chunks = overflow_splitter.split_text(paragraph)
        chunks.extend(
            piece.strip()
            for piece in sub_chunks
            if piece.strip()
        )

    return chunks
