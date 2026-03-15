"""Application service orchestration for OpenClaw Voice."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

from openclaw_voice.audio import concatenate_segments, encode_mp3
from openclaw_voice.chunking import ChunkingConfig, split_text_into_chunks
from openclaw_voice.config import ConfigError, load_config, read_reference_text, resolve_tts_bot
from openclaw_voice.messaging import AudioAttachment, create_provider
from openclaw_voice.tts import VoiceCloningEngine


@dataclass(slots=True, frozen=True)
class SynthesisDeliveryResult:
    """Result metadata for a synthesized delivery."""

    bot_name: str
    attachment_filename: str
    chunk_count: int


def synthesize_and_send(
    input_text_path: Path,
    bot_name: str,
    config_path: Path | None = None,
) -> SynthesisDeliveryResult:
    """Run synthesis and send the final MP3 through the selected provider."""

    config = load_config(config_path)
    bot_config = resolve_tts_bot(config, bot_name)
    source_text = input_text_path.read_text(encoding="utf-8").strip()
    if not source_text:
        raise ConfigError("The input text file is empty.")

    chunking_config = ChunkingConfig(max_chunk_chars=config.max_chunk_chars)
    chunks = split_text_into_chunks(source_text, chunking_config)
    if not chunks:
        raise ConfigError("No usable text chunks were produced from the input file.")

    reference_text = read_reference_text(config)
    engine = VoiceCloningEngine(config)
    segments, sample_rate = engine.synthesize_chunks(chunks, reference_text)
    waveform = concatenate_segments(
        segments,
        sample_rate=sample_rate,
        inter_chunk_silence_ms=config.inter_chunk_silence_ms,
    )
    mp3_bytes = encode_mp3(waveform, sample_rate)

    attachment = AudioAttachment(
        filename=_build_attachment_name(input_text_path),
        content=mp3_bytes,
        content_type="audio/mpeg",
    )
    provider = create_provider(bot_config)
    asyncio.run(provider.send_audio(attachment))

    return SynthesisDeliveryResult(
        bot_name=bot_config.name,
        attachment_filename=attachment.filename,
        chunk_count=len(chunks),
    )


def _build_attachment_name(input_text_path: Path) -> str:
    stem = input_text_path.stem.strip()
    if not stem:
        return "openclaw-voice.mp3"
    return f"{stem}.mp3"