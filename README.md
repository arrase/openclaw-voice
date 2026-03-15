# OpenClaw Voice

OpenClaw Voice is a Python CLI that turns a UTF-8 text file into cloned speech with Qwen TTS and delivers the result as an MP3 attachment through a configured Discord bot.

Speech synthesis runs locally on your own machine, so the tool does not depend on a hosted inference API or incur per-request API costs. It is designed to be installed as a regular shell command and called from OpenClaw or any other automation that can execute a standard program.

## Requirements

- Python 3.11 or newer
- A CUDA-capable GPU with a working PyTorch CUDA runtime
- A reference speaker WAV file and its matching transcript text file
- A Discord bot token for each bot you want to use
- A Discord user ID that will receive the direct message

OpenClaw Voice currently requires CUDA. Set `device_map` to a CUDA target such as `cuda:0` and run it on a machine with a compatible GPU.

If your GPU has limited VRAM, switch to the smaller `Qwen/Qwen3-TTS-12Hz-0.6B-Base` model instead of `Qwen/Qwen3-TTS-12Hz-1.7B-Base`.

The configured Discord bot must be able to reach the target user. In practice, that usually means the bot and the user share at least one server, and the user allows direct messages from server members.

## Quick start

Install the package:

```bash
pipx install git+https://github.com/arrase/openclaw-voice.git
```

Create the runtime directory and copy the bundled template assets:

```bash
mkdir -p ~/.openclaw-voice
cp config/config.yaml ~/.openclaw-voice/config.yaml
cp assets/reference/spanish_male.wav ~/.openclaw-voice/spanish_male.wav
cp assets/reference/spanish_male.txt ~/.openclaw-voice/spanish_male.txt
```

Edit `~/.openclaw-voice/config.yaml` and then run:

```bash
openclaw-voice --input-text input.txt --bot-name narrator
```

The repository already includes a Spanish reference voice. The default template expects `spanish_male.wav` and `spanish_male.txt` to live next to `config.yaml` inside `~/.openclaw-voice/`.

For other languages, generate your own reference WAV and matching plain-text transcription, copy both files into `~/.openclaw-voice/`, and update `ref_audio_path`, `ref_text_path`, and `language` accordingly.

## Example configuration:

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

- `model_name`: Hugging Face model identifier loaded by `Qwen3TTSModel.from_pretrained`
- `language`: Language label passed to the model for generation
- `device_map`: CUDA execution target such as `cuda:0`
- `dtype`: One of `float16`, `bfloat16`, or `float32`
- `ref_audio_path`: Reference speaker WAV file. Relative paths are resolved from the directory that contains `config.yaml`
- `ref_text_path`: Plain-text transcription that matches the reference speaker audio. Relative paths are resolved from the directory that contains `config.yaml`
- `inter_chunk_silence_ms`: Silence inserted between generated chunks
- `max_chunk_chars`: Maximum size for a chunk before recursive splitting is used
- `tts`: Non-empty list of delivery bot definitions
- `tts[].name`: Human-readable bot identifier selected with `--bot-name`
- `tts[].provider`: Messaging provider name. The current implementation supports `discord`
- `tts[].token`: Discord bot token
- `tts[].user_id`: Discord user ID that will receive the MP3 attachment

The bundled Spanish voice can be copied directly into the runtime config directory and used with relative paths. For any other language, create your own WAV and matching transcription before updating the config.

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

During normal execution, OpenClaw Voice does not write a local output file. The generated waveform is compressed to MP3 in memory and sent directly through the selected provider.

## OpenClaw integration

The repository includes an OpenClaw skill at [skill/openclaw-voice/SKILL.md](skill/openclaw-voice/SKILL.md). It tells OpenClaw how to use the service, which configuration file it depends on, and the expected command shape for turning a text file into a Discord DM with an MP3 attachment.

## Repository assets

- Example long-form Spanish input: [examples/long_text_es.txt](examples/long_text_es.txt)
- Example config template: [config/config.yaml](config/config.yaml)
- Bundled Spanish reference audio: [assets/reference/spanish_male.wav](assets/reference/spanish_male.wav)
- Bundled Spanish reference transcript: [assets/reference/spanish_male.txt](assets/reference/spanish_male.txt)