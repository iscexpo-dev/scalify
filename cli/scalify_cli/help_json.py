"""Machine-readable help for the Typer/Click command tree.

``scalify --help-json`` writes a single JSON document describing every command,
its options, types, defaults, and examples. The shape is the contract for
agents that drive the CLI without reading source.

Examples are looked up from ``HELP_EXAMPLES`` (a module-level dict keyed by
fully-qualified command path) so we can attach one-liners without bloating
docstrings. Phase 2 will hoist this alongside ``scalify discover`` and add a
``schemas`` field that points at each command's output schema.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import typer

if TYPE_CHECKING:
    import click

# One-liner examples per fully-qualified command path. Agents copy/paste.
# Keys match the full ``path`` we emit (``"scalify <subcommand> ..."``).
HELP_EXAMPLES: dict[str, list[str]] = {
    "scalify env": ["scalify env", "scalify --json env"],
    "scalify which": ["scalify which", "scalify --json which"],
    "scalify discover": [
        "scalify --json discover",
        "scalify --json discover --schemas-only",
    ],
    "scalify nodes ls": [
        "scalify --json nodes ls --produces MODEL",
        "scalify nodes ls --input object_info.json --category 'loaders*'",
    ],
    "scalify auth": ["scalify auth list", "scalify auth set civitai --key ..."],
    "scalify auth set": ["scalify auth set civitai --key sk-…"],
    "scalify auth list": ["scalify auth list", "scalify --json auth list"],
    "scalify auth remove": ["scalify auth remove civitai"],
    "scalify install": [
        "scalify install --nvidia",
        "scalify install --cpu --skip-manager",
    ],
    "scalify launch": [
        "scalify launch",
        "scalify launch -- --listen 0.0.0.0 --port 8188",
    ],
    "scalify run": [
        "scalify run --workflow path/to/workflow_api.json",
        "scalify --json-stream run --workflow path/to/workflow_api.json",
    ],
    "scalify stop": ["scalify stop"],
    "scalify logs": ["scalify logs", "scalify --json logs --tail 50"],
    "scalify set-default": ["scalify set-default /path/to/ScalifyUI"],
    "scalify update": ["scalify update", "scalify update all"],
    "scalify standalone": ["scalify standalone"],
    "scalify feedback": ["scalify feedback"],
    "scalify model": ["scalify model download --url ..."],
    "scalify model download": [
        "scalify model download --url https://civitai.com/api/download/models/12345",
    ],
    "scalify node": ["scalify node show installed"],
    "scalify manager": ["scalify manager disable-gui"],
    "scalify workflow print": [
        "scalify workflow print wf.json --input object_info.json",
        "scalify --json workflow print wf.json --select bindings",
    ],
}


def _param_to_dict(param: click.Parameter) -> dict[str, Any]:
    info: dict[str, Any] = {
        "name": param.name,
        "param_kind": param.param_type_name,  # "option" or "argument"
        "required": bool(param.required),
        "hidden": bool(getattr(param, "hidden", False)),
        "default": _coerce_default(param.default),
        "help": getattr(param, "help", None),
        "is_flag": bool(getattr(param, "is_flag", False)),
        "multiple": bool(getattr(param, "multiple", False)),
    }
    type_info = _type_to_dict(param.type)
    info["type"] = type_info["type"]
    if "choices" in type_info:
        info["choices"] = type_info["choices"]
    # Duck-type "is this an option?" via ``param_type_name`` rather than
    # ``isinstance(param, click.Option)``: typer >= 0.13 ships ``TyperOption`` /
    # ``TyperArgument`` whose MRO is ``-> click.Parameter`` (they no longer
    # subclass click.Option/Argument), so the isinstance check silently dropped
    # ``flags``/``envvar`` from every option in the help JSON contract.
    if param.param_type_name == "option":
        info["flags"] = list(param.opts) + list(param.secondary_opts)
        info["envvar"] = param.envvar
    return info


def _type_to_dict(t: click.ParamType) -> dict[str, Any]:
    name = getattr(t, "name", t.__class__.__name__).lower()
    out: dict[str, Any] = {"type": name}
    # Duck-type the choice list instead of ``isinstance(t, click.Choice)``:
    # typer >= 0.24 runs on a vendored click, so the param types it builds are
    # no instance of the installed ``click``'s classes and the isinstance check
    # silently dropped ``choices`` from every enum option.
    choices = getattr(t, "choices", None)
    if isinstance(choices, (list, tuple)):
        # ``schemas/help.json`` requires strings, and click >= 8.2 allows a
        # ``Choice`` over enum members.
        out["choices"] = [str(c) for c in choices]
    return out


def _coerce_default(default: Any) -> Any:
    # Typer wraps defaults in OptionInfo / ArgumentInfo; unwrap.
    if hasattr(default, "default"):
        default = default.default
    if callable(default):
        return None
    if default is ... or default is None:
        return None
    try:
        import json

        json.dumps(default)
        return default
    except TypeError:
        return str(default)


def _command_to_dict(cmd: click.Command, *, path: list[str]) -> dict[str, Any]:
    fqp = " ".join(path)
    params = [_param_to_dict(p) for p in cmd.params]
    entry: dict[str, Any] = {
        "name": cmd.name,
        "path": fqp,
        "help": (cmd.help or "").strip() or None,
        "short_help": (cmd.short_help or "").strip() or None,
        "hidden": bool(getattr(cmd, "hidden", False)),
        "params": params,
        "examples": HELP_EXAMPLES.get(fqp, []),
    }
    # Duck-type the group capability instead of ``isinstance(cmd, click.Group)``.
    # typer >= 0.13 / click >= 8.2 ship a ``TyperGroup`` that no longer subclasses
    # ``click.Group`` (its MRO is ``TyperGroup -> click.Command``), so the isinstance
    # check silently returned no subcommands and produced an empty command tree.
    if hasattr(cmd, "list_commands") and hasattr(cmd, "get_command"):
        subs: dict[str, Any] = {}
        for sub_name in sorted(cmd.list_commands(ctx=None)):  # type: ignore[arg-type]
            sub = cmd.get_command(None, sub_name)  # type: ignore[arg-type]
            if sub is None:
                continue
            subs[sub_name] = _command_to_dict(sub, path=path + [sub_name])
        entry["subcommands"] = subs
    return entry


def build_help_json(app: typer.Typer, *, prog_name: str = "scalify") -> dict[str, Any]:
    """Walk the Typer app and produce a help JSON document."""
    click_command = typer.main.get_command(app)
    root = _command_to_dict(click_command, path=[prog_name])
    return {
        "prog": prog_name,
        "commands": root.get("subcommands", {}),
        "root": {
            "help": root.get("help"),
            "params": root.get("params", []),
        },
    }


def iter_command_paths(app: typer.Typer, *, prog_name: str = "scalify") -> list[str]:
    """Return every leaf-command path as a flat list. Useful for tests."""
    doc = build_help_json(app, prog_name=prog_name)
    out: list[str] = []

    def walk(node: dict[str, Any], path: list[str]) -> None:
        subs = node.get("subcommands")
        if subs:
            for name, child in subs.items():
                walk(child, path + [name])
        else:
            out.append(" ".join(path))

    walk({"subcommands": doc["commands"]}, [prog_name])
    return out
