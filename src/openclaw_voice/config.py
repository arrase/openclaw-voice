"""Configuration loading for OpenClaw Voice."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_PATH = Path.home() / ".openclaw-voice" / "config.yaml"
SUPPORTED_TTS_PROVIDERS = {"discord"}


class ConfigError(RuntimeError):
    """Raised when configuration cannot be loaded or validated."""


@dataclass(slots=True, frozen=True)
class TTSBotConfig:
    """Validated messaging bot settings."""

    name: str
    provider: str
    token: str
    user_id: int
    normalized_name: str


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
    tts: tuple[TTSBotConfig, ...]


def load_config(config_path: Path | None = None) -> AppConfig:
    """Load and validate the application configuration."""

    resolved_config_path = (config_path or DEFAULT_CONFIG_PATH).expanduser().resolve()
    if not resolved_config_path.exists():
        raise ConfigError(
            f"Configuration file not found: {resolved_config_path}. "
            "Create it from config/config.yaml."
        )

    try:
        content = resolved_config_path.read_text(encoding="utf-8")
        raw_config = yaml.safe_load(content) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in {resolved_config_path}: {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"Unable to read {resolved_config_path}: {exc}") from exc

    if not isinstance(raw_config, dict):
        raise ConfigError("Configuration root must be a YAML mapping.")

    ref_audio_path = _resolve_path(raw_config, "ref_audio_path", resolved_config_path)
    ref_text_path = _resolve_path(raw_config, "ref_text_path", resolved_config_path)
    inter_chunk_silence_ms = _read_int(
        raw_config, "inter_chunk_silence_ms", default=150,
    )
    max_chunk_chars = _read_int(raw_config, "max_chunk_chars", default=1400)
    tts = _load_tts_configs(raw_config)

    if inter_chunk_silence_ms < 0:
        raise ConfigError("inter_chunk_silence_ms must be greater than or equal to 0.")
    if max_chunk_chars <= 0:
        raise ConfigError("max_chunk_chars must be greater than 0.")

    return AppConfig(
        config_path=resolved_config_path,
        model_name=_read_str(
            raw_config, "model_name",
            default="Qwen/Qwen3-TTS-12Hz-1.7B-Base",
        ),
        language=_read_str(raw_config, "language"),
        ref_audio_path=ref_audio_path,
        ref_text_path=ref_text_path,
        device_map=_read_str(raw_config, "device_map", default="cuda:0"),
        dtype=_read_str(raw_config, "dtype", default="bfloat16"),
        inter_chunk_silence_ms=inter_chunk_silence_ms,
        max_chunk_chars=max_chunk_chars,
        tts=tts,
    )


def resolve_tts_bot(config: AppConfig, bot_name: str) -> TTSBotConfig:
    """Resolve a configured bot by name using case-insensitive matching."""

    normalized_bot_name = _normalize_name(bot_name)
    for bot_config in config.tts:
        if bot_config.normalized_name == normalized_bot_name:
            return bot_config

    available = ", ".join(sorted(bot.name for bot in config.tts))
    raise ConfigError(
        f"No TTS bot named {bot_name!r} was found in the tts configuration. "
        f"Available bots: {available}."
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


def _load_tts_configs(raw_config: dict[str, Any]) -> tuple[TTSBotConfig, ...]:
    raw_tts = raw_config.get("tts")
    if not isinstance(raw_tts, list) or not raw_tts:
        raise ConfigError("Configuration field tts must be a non-empty list.")

    bots: list[TTSBotConfig] = []
    seen_names: dict[str, str] = {}
    for index, item in enumerate(raw_tts, start=1):
        context = f"tts[{index}]"
        if not isinstance(item, dict):
            raise ConfigError(f"Configuration entry {context} must be a mapping.")

        name = _read_str(item, "name", context=context)
        normalized_name = _normalize_name(name)
        if normalized_name in seen_names:
            original_name = seen_names[normalized_name]
            raise ConfigError(
                "Configuration contains duplicate bot names after lowercasing: "
                f"{original_name!r} and {name!r}."
            )

        provider = _read_str(item, "provider", context=context).lower()
        if provider not in SUPPORTED_TTS_PROVIDERS:
            supported = ", ".join(sorted(SUPPORTED_TTS_PROVIDERS))
            raise ConfigError(
                f"Unsupported provider {provider!r} in {context}. "
                f"Choose one of: {supported}."
            )

        bot = TTSBotConfig(
            name=name,
            provider=provider,
            token=_read_str(item, "token", context=context),
            user_id=_read_user_id(item, "user_id", context=context),
            normalized_name=normalized_name,
        )
        bots.append(bot)
        seen_names[normalized_name] = name

    return tuple(bots)


def _normalize_name(value: str) -> str:
    return value.strip().lower()


def _read_str(
    raw_config: dict[str, Any],
    key: str,
    default: str | None = None,
    *,
    context: str | None = None,
) -> str:
    value = raw_config.get(key, default)
    if value is None:
        msg = f"Missing required configuration field: {key}"
        raise ConfigError(_prefix_context(msg, context))
    if not isinstance(value, str):
        msg = f"Configuration field {key} must be a string."
        raise ConfigError(_prefix_context(msg, context))

    cleaned = value.strip()
    if not cleaned:
        msg = f"Configuration field {key} cannot be empty."
        raise ConfigError(_prefix_context(msg, context))
    return cleaned


def _read_int(raw_config: dict[str, Any], key: str, default: int) -> int:
    value = raw_config.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"Configuration field {key} must be an integer.")
    return value


def _read_user_id(
    raw_config: dict[str, Any],
    key: str,
    *,
    context: str | None = None,
) -> int:
    value = raw_config.get(key)
    if value is None:
        msg = f"Missing required configuration field: {key}"
        raise ConfigError(_prefix_context(msg, context))
    if isinstance(value, bool):
        msg = f"Configuration field {key} must be an integer."
        raise ConfigError(_prefix_context(msg, context))
    if isinstance(value, int):
        if value <= 0:
            msg = f"Configuration field {key} must be > 0."
            raise ConfigError(_prefix_context(msg, context))
        return value
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned.isdigit():
            parsed = int(cleaned)
            if parsed > 0:
                return parsed
    msg = f"Configuration field {key} must be a positive integer."
    raise ConfigError(_prefix_context(msg, context))


def _prefix_context(message: str, context: str | None) -> str:
    if context is None:
        return message
    return f"{context}: {message}"
