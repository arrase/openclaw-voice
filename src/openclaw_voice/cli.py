"""CLI entry point for OpenClaw Voice."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from openclaw_voice import __version__
from openclaw_voice.audio import concatenate_segments, write_wav
from openclaw_voice.chunking import ChunkingConfig, split_text_into_chunks
from openclaw_voice.config import ConfigError, load_config, read_reference_text
from openclaw_voice.tts import VoiceCloningEngine

app = typer.Typer(
    add_completion=False,
    help="Generate a cloned voice WAV from a text file using Qwen TTS.",
    no_args_is_help=True,
)


def main() -> None:
    """Run the CLI application."""

    app()


def _show_version(value: bool) -> None:
    if not value:
        return
    typer.echo(f"openclaw-voice {__version__}")
    raise typer.Exit()


@app.callback(invoke_without_command=True)
def synthesize(
    ctx: typer.Context,
    input_text_path: Annotated[
        Path,
        typer.Argument(
            ..., exists=True, dir_okay=False, file_okay=True, readable=True, resolve_path=True,
            help="Text file to convert into speech.",
        ),
    ],
    output_wav_path: Annotated[
        Path,
        typer.Argument(..., dir_okay=False, resolve_path=True, help="Path for the generated WAV file."),
    ],
    config_path: Annotated[
        Path | None,
        typer.Option("--config", help="Override the default ~/.openclaw-voice/config.yaml file."),
    ] = None,
    version: Annotated[
        bool | None,
        typer.Option("--version", callback=_show_version, is_eager=True, help="Show the application version."),
    ] = None,
) -> None:
    """Synthesize a single output WAV file from a text file."""

    if ctx.invoked_subcommand is not None:
        return

    del version
    try:
        config = load_config(config_path)
        source_text = input_text_path.read_text(encoding="utf-8").strip()
        if not source_text:
            raise ConfigError("The input text file is empty.")

        chunking_config = ChunkingConfig(max_chunk_chars=config.max_chunk_chars)
        chunks = split_text_into_chunks(source_text, chunking_config)
        if not chunks:
            raise ConfigError("No usable text chunks were produced from the input file.")

        typer.echo(f"Loaded {len(chunks)} text chunk(s).")
        reference_text = read_reference_text(config)
        engine = VoiceCloningEngine(config)
        segments, sample_rate = engine.synthesize_chunks(chunks, reference_text)
        waveform = concatenate_segments(
            segments,
            sample_rate=sample_rate,
            inter_chunk_silence_ms=config.inter_chunk_silence_ms,
        )
        write_wav(output_wav_path, waveform, sample_rate)
        typer.echo(f"Wrote {output_wav_path}.")
    except (ConfigError, OSError, RuntimeError, ValueError) as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
