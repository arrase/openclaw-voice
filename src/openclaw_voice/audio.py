"""Audio assembly helpers."""

from __future__ import annotations

from typing import Sequence

import lameenc
import numpy as np


def concatenate_segments(
    segments: Sequence[np.ndarray],
    sample_rate: int,
    inter_chunk_silence_ms: int = 0,
) -> np.ndarray:
    """Concatenate mono waveforms and optional silence into a single waveform."""

    if sample_rate <= 0:
        raise ValueError("sample_rate must be greater than 0.")
    if not segments:
        raise ValueError("At least one audio segment is required.")

    silence = _build_silence(sample_rate, inter_chunk_silence_ms)
    merged: list[np.ndarray] = []
    for index, segment in enumerate(segments):
        merged.append(_ensure_mono(segment))
        if silence is not None and index < len(segments) - 1:
            merged.append(silence)

    return np.concatenate(merged).astype(np.float32, copy=False)


def encode_mp3(
    waveform: np.ndarray,
    sample_rate: int,
    bit_rate_kbps: int = 128,
) -> bytes:
    """Encode a mono waveform into MP3 bytes."""

    if sample_rate <= 0:
        raise ValueError("sample_rate must be greater than 0.")
    if bit_rate_kbps <= 0:
        raise ValueError("bit_rate_kbps must be greater than 0.")

    mono_waveform = np.clip(_ensure_mono(waveform), -1.0, 1.0)
    pcm_int16 = np.rint(mono_waveform * np.iinfo(np.int16).max).astype(np.int16)

    encoder = lameenc.Encoder()
    encoder.set_bit_rate(bit_rate_kbps)
    encoder.set_in_sample_rate(sample_rate)
    encoder.set_channels(1)
    encoder.set_quality(2)

    encoded = encoder.encode(pcm_int16.tobytes())
    encoded += encoder.flush()
    if not encoded:
        raise RuntimeError("The MP3 encoder returned no audio data.")
    return encoded


def _build_silence(sample_rate: int, inter_chunk_silence_ms: int) -> np.ndarray | None:
    if inter_chunk_silence_ms <= 0:
        return None

    samples = int(sample_rate * (inter_chunk_silence_ms / 1000))
    if samples <= 0:
        return None
    return np.zeros(samples, dtype=np.float32)


def _ensure_mono(waveform: np.ndarray) -> np.ndarray:
    array = np.asarray(waveform, dtype=np.float32)
    if array.ndim == 1:
        return array
    if array.ndim != 2:
        raise ValueError("Waveform must be one-dimensional or a single-channel matrix.")
    if 1 in array.shape:
        return array.reshape(-1)
    raise ValueError("Waveform must contain a single audio channel.")
