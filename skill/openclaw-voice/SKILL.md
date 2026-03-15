---
name: voice-message
description: Use this skill when the user asks you to send an audio or voice message. The application converts text to audio and sends it automatically to the user without blocking.
---

# voice-message

Use this skill when the user asks you to send an audio or voice message.

## Instructions

1. Write the text you want to convert to audio into a temporary file using the `write` tool. For example, use `/tmp/voice_message.txt`.
2. Execute the `openclaw-voice` command using the `exec` tool. Set `background: true` since the application handles sending the audio automatically and you do not need to wait for it to finish.
3. Replace `<YourName>` with your actual agent name (e.g., Tars, etc.).

## Example Command

`openclaw-voice --input-text /tmp/voice_message.txt --bot-name <YourName>`