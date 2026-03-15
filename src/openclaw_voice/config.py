"""Configuration loading for OpenClaw Voice."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_PATH = Path.home() / ".openclaw-voice" / "config.yaml"


class ConfigError(RuntimeError):
    """Raised when configuration cannot be loaded or validated."""


@dataclass(slots=True, frozen=True)
class AppConfig:
    """Validated runtime settings."""

    config_path: Path
    model_name: str
    language: str
    ref_audio_path: Path
    ref_text_path: Path
    device_map: str
    dtype: str
    inter_chunk_silence_ms: int
    max_chunk_chars: int


def load_config(config_path: Path | None = None) -> AppConfig:
    """Load and validate the application configuration."""

    resolved_config_path = (config_path or DEFAULT_CONFIG_PATH).expanduser().resolve()
    if not resolved_config_path.exists():
        raise ConfigError(
            f"Configuration file not found: {resolved_config_path}. "
            "Create it from config/config.example.yaml."
        )

    try:
        raw_config = yaml.safe_load(resolved_config_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in {resolved_config_path}: {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"Unable to read {resolved_config_path}: {exc}") from exc

    if not isinstance(raw_config, dict):
        raise ConfigError("Configuration root must be a YAML mapping.")

    ref_audio_path = _resolve_path(raw_config, "ref_audio_path", resolved_config_path)
    ref_text_path = _resolve_path(raw_config, "ref_text_path", resolved_config_path)
    inter_chunk_silence_ms = _read_int(raw_config, "inter_chunk_silence_ms", default=150)
    max_chunk_chars = _read_int(raw_config, "max_chunk_chars", default=1400)

    if inter_chunk_silence_ms < 0:
        raise ConfigError("inter_chunk_silence_ms must be greater than or equal to 0.")
    if max_chunk_chars <= 0:
        raise ConfigError("max_chunk_chars must be greater than 0.")

    return AppConfig(
        config_path=resolved_config_path,
        model_name=_read_str(raw_config, "model_name", default="Qwen/Qwen3-TTS-12Hz-1.7B-Base"),
        language=_read_str(raw_config, "language"),
        ref_audio_path=ref_audio_path,
        ref_text_path=ref_text_path,
        device_map=_read_str(raw_config, "device_map", default="cuda:0"),
        dtype=_read_str(raw_config, "dtype", default="bfloat16"),
        inter_chunk_silence_ms=inter_chunk_silence_ms,
        max_chunk_chars=max_chunk_chars,
    )


def read_reference_text(config: AppConfig) -> str:
    """Read the reference transcription from disk."""

    try:
        text = config.ref_text_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise ConfigError(f"Unable to read reference transcription: {exc}") from exc

    if not text:
        raise ConfigError("The reference transcription file is empty.")
    return text


def _resolve_path(raw_config: dict[str, Any], key: str, config_path: Path) -> Path:
    value = _read_str(raw_config, key)
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = (config_path.parent / candidate).resolve()
    else:
        candidate = candidate.resolve()

    if not candidate.exists():
        raise ConfigError(f"Configured path for {key} does not exist: {candidate}")
    if not candidate.is_file():
        raise ConfigError(f"Configured path for {key} is not a file: {candidate}")
    return candidate


def _read_str(raw_config: dict[str, Any], key: str, default: str | None = None) -> str:
    value = raw_config.get(key, default)
    if value is None:
        raise ConfigError(f"Missing required configuration field: {key}")
    if not isinstance(value, str):
        raise ConfigError(f"Configuration field {key} must be a string.")

    cleaned = value.strip()
    if not cleaned:
        raise ConfigError(f"Configuration field {key} cannot be empty.")
    return cleaned


def _read_int(raw_config: dict[str, Any], key: str, default: int) -> int:
    value = raw_config.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"Configuration field {key} must be an integer.")
    return value
