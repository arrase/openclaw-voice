# OpenClaw Voice

OpenClaw Voice is a small Python CLI that turns a UTF-8 text file into cloned speech using Qwen TTS and sends the final audio as an MP3 attachment through a configured Discord bot. Audio generation runs locally on your own machine, so it does not depend on a hosted inference API or incur per-request API costs. It is intended to be installed as a shell command and called from OpenClaw or any other automation that can invoke a regular executable.

## Features

- Installs a command named `openclaw-voice`
- Runs speech synthesis locally instead of calling a paid external API
- Sends the generated audio as a compressed MP3 attachment by Discord DM
- Selects the delivery bot from the `tts` section in `~/.openclaw-voice/config.yaml`
- Matches bot names case-insensitively so `Narrator` and `narrator` resolve to the same entry
- Accepts an optional `--config` override for alternate configuration files
- Splits long input text paragraph by paragraph, then recursively splits oversized paragraphs
- Synthesizes one chunk at a time and concatenates everything into a single waveform before compression
- Inserts configurable silence between chunks to smooth the joins
- Includes an OpenClaw skill so the agent knows how to invoke the service

## Requirements

- Python 3.11 or newer
- A CUDA-capable GPU with a working PyTorch CUDA runtime
- A reference speaker WAV file and its matching transcript text file
- A Discord bot token for each bot you want to use
- A Discord user ID that will receive the direct message

OpenClaw Voice currently requires CUDA. Set `device_map` to a CUDA target such as `cuda:0` and run it on a machine with a compatible GPU.

The configured Discord bot must be able to reach the target user. In practice, that usually means the bot and the user share at least one server, and the user allows direct messages from server members.

## Installation

### Install with pipx

```bash
pipx install git+https://github.com/arrase/openclaw-voice.git
```

### Install for local development

```bash
python -m pip install -e .
```

## Configuration

Copy the repository template to the default runtime location:

```bash
mkdir -p ~/.openclaw-voice
cp config/config.yaml ~/.openclaw-voice/config.yaml
```

Then edit `~/.openclaw-voice/config.yaml` so it points to your own reference audio, transcription, and one or more messaging bots.

Example:

```yaml
model_name: Qwen/Qwen3-TTS-12Hz-1.7B-Base
language: Spanish
device_map: cuda:0
dtype: bfloat16
ref_audio_path: /absolute/path/to/reference.wav
ref_text_path: /absolute/path/to/reference.txt
inter_chunk_silence_ms: 150
max_chunk_chars: 1400
tts:
  - name: narrator
    provider: discord
    token: YOUR_DISCORD_BOT_TOKEN
    user_id: 123456789012345678
```

### Configuration fields

- `model_name`: Hugging Face model identifier loaded by `Qwen3TTSModel.from_pretrained`.
- `language`: Language label passed to the model for generation.
- `device_map`: CUDA execution target such as `cuda:0`.
- `dtype`: One of `float16`, `bfloat16`, or `float32`.
- `ref_audio_path`: Reference speaker WAV file.
- `ref_text_path`: Plain-text transcription that matches the reference speaker audio.
- `inter_chunk_silence_ms`: Silence inserted between generated chunks.
- `max_chunk_chars`: Maximum size for a chunk before recursive splitting is used.
- `tts`: Non-empty list of delivery bot definitions.
- `tts[].name`: Human-readable bot identifier selected with `--bot-name`.
- `tts[].provider`: Messaging provider name. The current implementation supports `discord`.
- `tts[].token`: Discord bot token.
- `tts[].user_id`: Discord user ID that will receive the MP3 attachment.

Relative paths in the config file are resolved from the directory that contains `config.yaml`.

Bot names are normalized to lowercase before comparison. That means `Narrator`, `NARRATOR`, and `narrator` all resolve to the same configured entry. Two configured names that differ only by case are rejected as duplicates.

## Usage

Basic invocation:

```bash
openclaw-voice --input-text input.txt --bot-name narrator
```

Use a different configuration file:

```bash
openclaw-voice --input-text input.txt --bot-name narrator --config /path/to/config.yaml
```

Run through the module entry point instead of the installed script:

```bash
python -m openclaw_voice --input-text input.txt --bot-name narrator
```

The CLI exits with code `1` when configuration loading, file I/O, chunk generation, MP3 encoding, or Discord delivery fails.

OpenClaw Voice no longer writes a local output file during normal execution. The generated waveform is compressed to MP3 in memory and sent directly through the selected provider.

## OpenClaw integration

The repository includes an OpenClaw skill at [skill/openclaw-voice/SKILL.md](skill/openclaw-voice/SKILL.md). It tells OpenClaw how to use the service, which configuration file it depends on, and the expected command shape for turning a text file into a Discord DM with an MP3 attachment.

## How it works

1. The CLI loads and validates the YAML configuration.
2. It resolves the requested bot from the `tts` list using case-insensitive name matching.
3. It reads the input text file and rejects empty input.
4. It splits the text on paragraph boundaries.
5. Any paragraph longer than `max_chunk_chars` is split again with `RecursiveCharacterTextSplitter`.
6. The Qwen TTS model generates one waveform per chunk using the configured reference voice.
7. All waveforms are concatenated, optional silence is inserted between chunks, and the final waveform is compressed to MP3 in memory.
8. The selected messaging provider sends the MP3 attachment to the configured destination.

## Repository assets

- Example long-form Spanish input: [examples/long_text_es.txt](examples/long_text_es.txt)
- Example config template: [config/config.yaml](config/config.yaml)
- Reference audio used during development: [assets/reference/bodega.wav](assets/reference/bodega.wav)
- Matching reference transcript: [assets/reference/reference.txt](assets/reference/reference.txt)

Example end-to-end command:

```bash
openclaw-voice --input-text examples/long_text_es.txt --bot-name narrator
```

## Flash Attention

If `flash_attn` is importable in the environment, OpenClaw Voice requests `flash_attention_2` automatically when loading the model. This dependency is optional by design because it often fails to build from source on systems without a full CUDA toolchain.

## Development

The current repository does not include an automated test suite.

For a basic smoke check, use:

```bash
openclaw-voice --help
python -m openclaw_voice --help
```
