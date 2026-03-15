# OpenClaw Voice

OpenClaw Voice is a small Python CLI that turns a UTF-8 text file into a single WAV file using Qwen TTS voice cloning. Audio generation runs locally on your own machine, so it does not depend on a hosted inference API or incur per-request API costs. It is intended to be installed as a shell command and called from OpenClaw or any other automation that can invoke a regular executable.

## Features

- Installs a command named `openclaw-voice`
- Runs speech synthesis locally instead of calling a paid external API
- Loads runtime settings from `~/.openclaw-voice/config.yaml` by default
- Accepts an optional `--config` override for alternate configuration files
- Splits long input text paragraph by paragraph, then recursively splits oversized paragraphs
- Synthesizes one chunk at a time and concatenates everything into a single WAV file
- Inserts configurable silence between chunks to smooth the joins
- Creates the output directory automatically if it does not exist

## Requirements

- Python 3.11 or newer
- A CUDA-capable GPU with a working PyTorch CUDA runtime
- A reference speaker WAV file and its matching transcript text file

OpenClaw Voice currently requires CUDA. Set `device_map` to a CUDA target such as `cuda:0` and run it on a machine with a compatible GPU.

## Installation

### Install with pipx

```bash
# Install from GitHub
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

Then edit `~/.openclaw-voice/config.yaml` so it points to your own reference audio and transcription.

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

Relative paths in the config file are resolved from the directory that contains `config.yaml`.

## Usage

Basic invocation:

```bash
openclaw-voice input.txt output.wav
```

Use a different configuration file:

```bash
openclaw-voice input.txt output.wav --config /path/to/config.yaml
```

Run through the module entry point instead of the installed script:

```bash
python -m openclaw_voice input.txt output.wav
```

The CLI exits with code `1` when configuration loading, file I/O, chunk generation, or WAV assembly fails.

## How it works

1. The CLI loads and validates the YAML configuration.
2. It reads the input text file and rejects empty input.
3. It splits the text on paragraph boundaries.
4. Any paragraph longer than `max_chunk_chars` is split again with `RecursiveCharacterTextSplitter`.
5. The Qwen TTS model generates one waveform per chunk using the configured reference voice.
6. All waveforms are concatenated, optional silence is inserted between chunks, and the final WAV file is written to disk.

## Repository assets

- Example long-form Spanish input: [examples/long_text_es.txt](examples/long_text_es.txt)
- Example config template: [config/config.yaml](config/config.yaml)
- Reference audio used during development: [assets/reference/bodega.wav](assets/reference/bodega.wav)
- Matching reference transcript: [assets/reference/reference.txt](assets/reference/reference.txt)

Example end-to-end command:

```bash
openclaw-voice examples/long_text_es.txt output_long.wav
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
