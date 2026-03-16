"""Qwen TTS model bootstrap and synthesis."""

from __future__ import annotations

from importlib.util import find_spec
from typing import TYPE_CHECKING, Sequence

import numpy as np

from openclaw_voice.config import AppConfig

if TYPE_CHECKING:
    from qwen_tts import Qwen3TTSModel


class VoiceCloningEngine:
    """Thin wrapper around Qwen3TTSModel for voice cloning."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._model = self._load_model(config)

    def synthesize_chunks(
        self,
        chunks: Sequence[str],
        ref_text: str,
    ) -> tuple[list[np.ndarray], int]:
        """Generate audio for each chunk and return the waveforms and sample rate."""

        if not chunks:
            raise ValueError("At least one chunk is required for synthesis.")

        sample_rate: int | None = None
        segments: list[np.ndarray] = []
        for chunk in chunks:
            wavs, current_sample_rate = self._model.generate_voice_clone(
                text=chunk,
                language=self._config.language,
                ref_audio=str(self._config.ref_audio_path),
                ref_text=ref_text,
            )
            if not wavs:
                raise RuntimeError("The model returned no audio for one of the chunks.")

            if sample_rate is None:
                sample_rate = current_sample_rate
            elif sample_rate != current_sample_rate:
                raise RuntimeError(
                    "The model returned inconsistent sample rates across chunks."
                )

            segments.append(np.asarray(wavs[0], dtype=np.float32))

        return segments, sample_rate or 0

    def _load_model(self, config: AppConfig) -> Qwen3TTSModel:
        import torch
        from qwen_tts import Qwen3TTSModel

        model_kwargs: dict[str, object] = {
            "device_map": config.device_map,
            "dtype": _resolve_dtype(config.dtype),
        }

        if "cuda" in config.device_map.lower() and not torch.cuda.is_available():
            raise RuntimeError(
                "The configuration requests CUDA, but no CUDA device is available. "
                "Update device_map in your config.yaml."
            )

        if find_spec("flash_attn") is not None:
            model_kwargs["attn_implementation"] = "flash_attention_2"

        return Qwen3TTSModel.from_pretrained(config.model_name, **model_kwargs)


def _resolve_dtype(dtype_name: str) -> object:
    import torch

    dtype_map = {
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
        "float32": torch.float32,
    }

    try:
        return dtype_map[dtype_name.lower()]
    except KeyError as exc:
        supported = ", ".join(sorted(dtype_map))
        raise RuntimeError(
            f"Unsupported dtype {dtype_name!r}. Choose one of: {supported}."
        ) from exc
