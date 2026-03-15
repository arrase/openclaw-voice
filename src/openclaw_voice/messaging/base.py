"""Common messaging abstractions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class DeliveryError(RuntimeError):
    """Raised when audio delivery fails."""


@dataclass(slots=True, frozen=True)
class AudioAttachment:
    """Binary audio attachment ready to be sent."""

    filename: str
    content: bytes
    content_type: str


class MessagingProvider(Protocol):
    """Protocol implemented by messaging providers."""

    async def send_audio(self, attachment: AudioAttachment) -> None:
        """Send the synthesized audio through the provider."""