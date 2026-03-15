"""Audio assembly helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np
import soundfile as sf


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


def write_wav(output_path: Path, waveform: np.ndarray, sample_rate: int) -> None:
    """Write a waveform to disk as a WAV file."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(output_path, _ensure_mono(waveform), sample_rate)


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
