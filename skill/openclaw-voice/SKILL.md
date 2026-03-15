---
name: openclaw-voice
description: "Use when generating speech with Qwen TTS for OpenClaw, preparing config files, chunking long text into paragraphs, or sending a final MP3 attachment through a configured messaging bot."
---

# OpenClaw Voice Skill

## Goal

Generate cloned speech from text using the OpenClaw Voice CLI and send the final MP3 attachment through the bot selected from `~/.openclaw-voice/config.yaml`.

## Workflow

1. Confirm that `~/.openclaw-voice/config.yaml` exists, points to a valid reference WAV plus matching transcription file, and contains a `tts` entry for the requested bot.
2. Invoke the CLI with named parameters, always including `--input-text` and `--bot-name`.
3. Bot names are matched case-insensitively, so normalize expectations accordingly and avoid duplicate config names that differ only by case.
4. Read the input text file as UTF-8.
5. Split the text by paragraphs first. If a paragraph is too long, split it into smaller chunks before synthesis.
6. Use the configured language, reference audio, and reference text for every generated chunk.
7. Concatenate the generated waveforms, preserve the configured silence between chunks, compress the result to MP3, and send it through the selected provider.

## Command

```bash
openclaw-voice --input-text input.txt --bot-name narrator
```

## Notes

- The default config location is `~/.openclaw-voice/config.yaml`.
- The CLI accepts an alternate config path with `--config`.
- The current provider implementation is `discord` and sends the audio as a DM attachment without message text.
- The final audio is compressed to MP3 in memory before delivery.
- `flash_attn` is optional and enabled automatically only when installed.
- The first release is paragraph-first, not full semantic chunking.
