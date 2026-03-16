"""Discord direct-message delivery provider."""

from __future__ import annotations

import io

import discord

from openclaw_voice.messaging.base import AudioAttachment, DeliveryError


class DiscordMessagingProvider:
    """Send audio attachments through a Discord bot DM."""

    def __init__(self, token: str, user_id: int) -> None:
        self._token = token
        self._user_id = user_id

    async def send_audio(self, attachment: AudioAttachment) -> None:
        client = _DiscordDMClient(user_id=self._user_id, attachment=attachment)
        try:
            await client.start(self._token)
        except discord.LoginFailure as exc:
            raise DeliveryError("Discord rejected the configured bot token.") from exc
        except discord.HTTPException as exc:
            raise DeliveryError(f"Discord connection failed: {exc}") from exc

        if client.delivery_error is not None:
            raise client.delivery_error
        if not client.sent:
            raise DeliveryError(
                "Discord closed the session before"
                " sending the MP3 attachment."
            )


class _DiscordDMClient(discord.Client):
    def __init__(self, user_id: int, attachment: AudioAttachment) -> None:
        super().__init__(intents=discord.Intents.default())
        self._user_id = user_id
        self._attachment = attachment
        self.delivery_error: DeliveryError | None = None
        self.sent = False

    async def on_ready(self) -> None:
        if self.sent or self.delivery_error is not None:
            await self.close()
            return

        try:
            user = await self.fetch_user(self._user_id)
            audio_file = discord.File(
                fp=io.BytesIO(self._attachment.content),
                filename=self._attachment.filename,
            )
            await user.send(file=audio_file)
            self.sent = True
        except discord.Forbidden as exc:
            self.delivery_error = DeliveryError(
                "Discord blocked the DM. The user may have"
                " direct messages disabled, no shared server,"
                " or the bot may be blocked."
            )
        except discord.NotFound as exc:
            self.delivery_error = DeliveryError(
                f"Discord could not find a user with ID {self._user_id}."
            )
        except discord.HTTPException as exc:
            self.delivery_error = DeliveryError(
                f"Discord could not send the MP3 attachment: {exc}"
            )
        except Exception as exc:
            self.delivery_error = DeliveryError(
                f"Unexpected Discord error: {type(exc).__name__}: {exc}"
            )
        finally:
            await self.close()
