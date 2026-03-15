"""Messaging provider factory."""

from __future__ import annotations

from openclaw_voice.config import TTSBotConfig
from openclaw_voice.messaging.base import DeliveryError, MessagingProvider
from openclaw_voice.messaging.discord_provider import DiscordMessagingProvider


def create_provider(bot_config: TTSBotConfig) -> MessagingProvider:
    """Instantiate the provider configured for the selected bot."""

    if bot_config.provider == "discord":
        return DiscordMessagingProvider(token=bot_config.token, user_id=bot_config.user_id)

    raise DeliveryError(f"Unsupported provider {bot_config.provider!r}.")