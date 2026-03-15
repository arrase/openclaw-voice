"""CLI entry point for OpenClaw Voice."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from openclaw_voice import __version__
from openclaw_voice.config import ConfigError
from openclaw_voice.messaging import DeliveryError
from openclaw_voice.service import synthesize_and_send

app = typer.Typer(
    add_completion=False,
    help="Generate cloned speech from a text file and send it through a configured messaging bot.",
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
        typer.Option(
            ..., "--input-text", exists=True, dir_okay=False, file_okay=True, readable=True, resolve_path=True,
            help="Text file to convert into speech.",
        ),
    ],
    bot_name: Annotated[
        str,
        typer.Option(..., "--bot-name", help="Configured bot name from the tts section to use for delivery."),
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
    """Synthesize speech and deliver it with the selected messaging bot."""

    if ctx.invoked_subcommand is not None:
        return

    del version
    try:
        result = synthesize_and_send(
            input_text_path=input_text_path,
            bot_name=bot_name,
            config_path=config_path,
        )
        typer.echo(f"Loaded {result.chunk_count} text chunk(s).")
        typer.echo(f"Sent {result.attachment_filename} with bot {result.bot_name}.")
    except (ConfigError, DeliveryError, OSError, RuntimeError, ValueError) as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
