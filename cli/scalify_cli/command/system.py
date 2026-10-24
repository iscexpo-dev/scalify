"""``scalify system-stats`` and ``scalify free`` — ScalifyUI resource-management passthrough.

Thin wrappers over ScalifyUI's own ``GET /system_stats`` and ``POST /free``
endpoints (routed through :class:`scalify_cli.scalify_client.Client`, cloud or
local via ``resolve_target``), so agents can read VRAM state and free it
without any direct HTTP.

Both entry points stamp ``renderer.where`` from the resolved target right
after ``resolve_target``, so every envelope they emit — the unreachable-server
errors especially — names the backend the command routed to.
"""

from __future__ import annotations

import urllib.error
from typing import Any

import typer

from scalify_cli.scalify_client import Client, HTTPError
from scalify_cli.output.sanitize import sanitize_markup
from scalify_cli.target import resolve_target


def _humanize_bytes(n: Any) -> str:
    """Render a byte count as a compact human-readable string (e.g. ``3.5 GiB``).

    Non-numeric input (a device that omitted the field) renders as ``?``
    rather than raising, since pretty-mode rendering must never crash on a
    server payload we don't fully control.
    """
    if not isinstance(n, (int, float)):
        return "?"
    value = float(n)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(value) < 1024.0:
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} {unit}"
        value /= 1024.0
    return f"{value:.1f} PiB"


def _render_stats_pretty(renderer, stats: dict[str, Any]) -> None:
    from rich.table import Table

    devices = stats.get("devices") or []
    tbl = Table(show_header=True, header_style="bold")
    tbl.add_column("name")
    tbl.add_column("type")
    tbl.add_column("index")
    tbl.add_column("vram_free")
    tbl.add_column("vram_total")
    for dev in devices:
        if not isinstance(dev, dict):
            continue
        # Device name/type/index are whatever `/system_stats` reported, and
        # `Table.add_row` parses markup in a `str` cell. The two byte columns
        # are built by `_humanize_bytes`, which only ever emits digits and a
        # unit, so they carry nothing to escape.
        tbl.add_row(
            sanitize_markup(dev.get("name", "?")),
            sanitize_markup(dev.get("type", "?")),
            sanitize_markup(dev.get("index", "?")),
            _humanize_bytes(dev.get("vram_free")),
            _humanize_bytes(dev.get("vram_total")),
        )
    renderer.console().print(tbl)

    system = stats.get("system") or {}
    ram_free = _humanize_bytes(system.get("ram_free"))
    ram_total = _humanize_bytes(system.get("ram_total"))
    # Same payload, same hazard one line further on: this f-string IS markup,
    # and `Renderer.print` hands it to `rich.print` without escaping anything.
    version = sanitize_markup(system.get("scalifyui_version", "?"))
    renderer.print(f"[dim]RAM: {ram_free} / {ram_total} free — ScalifyUI {version}[/dim]")


def _handle_unreachable(renderer, e: Exception, *, target, operation: str) -> None:
    if isinstance(e, HTTPError):
        code = "cloud_http_error" if target.is_cloud else "server_not_running"
        renderer.error(
            code=code,
            message=f"HTTP {e.status} from ScalifyUI during {operation}: {e.message}",
            hint="run `scalify cloud whoami` to verify auth"
            if target.is_cloud
            else "run `scalify launch` to start a local server",
            details={"status": e.status},
        )
        return
    code = "cloud_http_error" if target.is_cloud else "server_not_running"
    renderer.error(
        code=code,
        message=f"could not reach ScalifyUI during {operation}: {e}",
        hint="check `--where` and network connectivity"
        if target.is_cloud
        else "run `scalify launch` to start a local server",
    )


def system_stats_execute(renderer, *, where: str | None = None) -> None:
    """Entry point wired from ``scalify system-stats`` in cmdline.py."""
    target = resolve_target(where=where)
    renderer.where = target.kind
    client = Client(target)
    try:
        stats = client.get_system_stats()
    except (HTTPError, urllib.error.URLError, OSError) as e:
        _handle_unreachable(renderer, e, target=target, operation="system-stats")
        raise typer.Exit(code=1) from e

    if not isinstance(stats, dict):
        renderer.error(
            code="cloud_http_error" if target.is_cloud else "server_not_running",
            message="ScalifyUI returned an unparseable /system_stats response",
            hint="check that the host really is a ScalifyUI server",
        )
        raise typer.Exit(code=1)

    if renderer.is_pretty():
        _render_stats_pretty(renderer, stats)
    renderer.emit(stats, command="system-stats")


def free_execute(
    renderer,
    *,
    where: str | None = None,
    unload_models: bool = True,
    free_memory: bool = False,
) -> None:
    """Entry point wired from ``scalify free`` in cmdline.py."""
    target = resolve_target(where=where)
    renderer.where = target.kind
    client = Client(target)
    try:
        client.post_free(unload_models=unload_models, free_memory=free_memory)
    except (HTTPError, urllib.error.URLError, OSError) as e:
        _handle_unreachable(renderer, e, target=target, operation="free")
        raise typer.Exit(code=1) from e

    note = (
        "applies when the queue worker next iterates — immediate if idle, after the current job if busy; "
        "does not interrupt a running job"
    )
    payload = {
        "requested": {"unload_models": unload_models, "free_memory": free_memory},
        "note": note,
    }
    if renderer.is_pretty():
        renderer.success(f"Requested: unload_models={unload_models}, free_memory={free_memory}")
        renderer.print(f"[dim]{note}[/dim]")
    renderer.emit(payload, command="free")
