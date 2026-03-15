---
name: openclaw-voice
description: "Use when generating speech with Qwen TTS for OpenClaw, preparing config files, chunking long text into paragraphs, or producing a final WAV output."
---

# OpenClaw Voice Skill

## Goal

Generate a single WAV file from text using the OpenClaw Voice CLI and the runtime configuration stored in `~/.openclaw-voice/config.yaml`.

## Workflow

1. Confirm that `~/.openclaw-voice/config.yaml` exists and points to a valid reference WAV plus a matching transcription file.
2. Read the input text file as UTF-8.
3. Split the text by paragraphs first. If a paragraph is too long, split it into smaller chunks before synthesis.
4. Use the configured language, reference audio, and reference text for every generated chunk.
5. Concatenate the generated waveforms into a single output WAV and keep the configured silence between chunks.

## Command

```bash
openclaw-voice input.txt output.wav
```

## Notes

- The default config location is `~/.openclaw-voice/config.yaml`.
- The CLI accepts an alternate config path with `--config`.
- `flash_attn` is optional and enabled automatically only when installed.
- The first release is paragraph-first, not full semantic chunking.
