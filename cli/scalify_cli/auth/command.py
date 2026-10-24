"""``scalify auth`` — manage API tokens for third-party model hosts.

Tokens here are used by ``scalify model download`` when fetching gated
checkpoints / LoRAs / VAEs from Civitai or Hugging Face. Stored locally,
never transmitted except to the issuing provider.

Scalify Cloud sign-in lives in a separate namespace — see ``scalify cloud``.
"""

from __future__ import annotations

from typing import Annotated

import typer

from scalify_cli import tracking
from scalify_cli.auth import store
from scalify_cli.output import get_renderer, rprint

app = typer.Typer(
    no_args_is_help=True,
    help="Manage API tokens for model hosts (Civitai, Hugging Face).",
)


@app.command("list", help="List third-party API-key providers (civitai, huggingface).")
@tracking.track_command("auth")
def list_cmd():
    renderer = get_renderer()
    records = store.list_records()
    if renderer.is_pretty():
        _render_pretty_list(records=records)
    renderer.emit(
        {
            "providers": [r.to_dict(redact=True) for r in records],
            "supported": list(store.SUPPORTED_PROVIDERS),
            "path": str(store.secrets_path()),
            "action": "list",
        },
        command="auth list",
    )


@app.command("set", help="Set or replace the API token for a third-party model host.")
@tracking.track_command("auth")
def set_cmd(
    provider: Annotated[
        str,
        typer.Argument(help="Provider name — `civitai` or `huggingface`. Scalify Cloud uses `scalify cloud login`."),
    ],
    key: Annotated[
        str,
        typer.Option(
            "--key",
            show_default=False,
            help="The API token. Stored locally; never sent except to the provider.",
        ),
    ],
):
    renderer = get_renderer()
    if provider == "scalify-cloud":
        renderer.error(
            code="auth_use_login_for_cloud",
            message="Scalify Cloud uses OAuth — `auth set --key` is not supported for `scalify-cloud`.",
            hint="run: scalify cloud login   (or `scalify cloud set-key` for the API-key path)",
            details={"provider": provider},
        )
        raise typer.Exit(code=1)
    if not key:
        renderer.error(code="auth_invalid_key", message="--key cannot be empty.")
        raise typer.Exit(code=1)
    try:
        record = store.set(provider, key)
    except ValueError as e:
        renderer.error(code="auth_invalid_key", message=str(e))
        raise typer.Exit(code=1)
    if renderer.is_pretty():
        rprint(f"[bold green]Stored token for {record.provider}[/bold green] ({record.to_dict()['key']})")
        if provider not in store.SUPPORTED_PROVIDERS:
            rprint(f"[yellow]Note:[/yellow] {provider!r} is not a well-known provider; stored anyway.")
    renderer.emit(
        {
            "providers": [r.to_dict(redact=True) for r in store.list_records()],
            "supported": list(store.SUPPORTED_PROVIDERS),
            "path": str(store.secrets_path()),
            "action": "set",
        },
        command="auth set",
        changed=True,
    )


@app.command("remove", help="Remove a stored third-party API token.")
@tracking.track_command("auth")
def remove_cmd(
    provider: Annotated[str, typer.Argument(help="Provider name.")],
):
    renderer = get_renderer()
    if provider == "scalify-cloud":
        renderer.error(
            code="auth_use_logout_for_cloud",
            message="Scalify Cloud uses OAuth — use `scalify cloud logout` to clear the session.",
            hint="run: scalify cloud logout",
            details={"provider": provider},
        )
        raise typer.Exit(code=1)
    removed = store.remove(provider)
    if not removed:
        renderer.error(
            code="auth_not_found",
            message=f"No stored key for {provider!r}.",
            hint="run: scalify auth list",
            details={"provider": provider},
        )
        raise typer.Exit(code=1)
    if renderer.is_pretty():
        rprint(f"[bold]Removed token for {provider}[/bold]")
    renderer.emit(
        {
            "providers": [r.to_dict(redact=True) for r in store.list_records()],
            "supported": list(store.SUPPORTED_PROVIDERS),
            "path": str(store.secrets_path()),
            "action": "remove",
        },
        command="auth remove",
        changed=True,
    )


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _render_pretty_list(*, records):
    """Pretty-render the auth list (third-party provider tokens only)."""
    from rich.console import Group
    from rich.text import Text

    from scalify_cli.config_manager import ConfigManager
    from scalify_cli.output.branding import branded_panel
    from scalify_cli.output.panels import auth_empty_panel, auth_list_table

    renderer = get_renderer()
    path = str(store.secrets_path())

    if not records:
        # Empty-state has its own panel; brand it via the canonical wrapper.
        body = auth_empty_panel(supported=list(store.SUPPORTED_PROVIDERS), path=path)
    else:
        redacted = [r.to_dict(redact=True) for r in records]
        body = auth_list_table(redacted, supported=list(store.SUPPORTED_PROVIDERS), path=path)

    hint = Text("Scalify Cloud sign-in lives under `scalify cloud whoami`.", style="dim")
    group = Group(body, Text(""), hint)

    renderer.console().print(branded_panel(group, title="auth", version=ConfigManager().get_cli_version()))
