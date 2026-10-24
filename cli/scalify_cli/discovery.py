"""Self-discovery for agents.

``scalify discover --json`` emits a single document describing the entire CLI
surface plus the JSON Schemas the CLI's structured outputs adhere to.

Why this exists: a fresh agent should be able to ``scalify discover`` once and
have everything it needs — command tree, schemas, error codes, capability
flags — without scraping ``--help`` text or reading source.
"""

from __future__ import annotations

import json
from importlib import resources
from typing import Any

from scalify_cli.help_json import build_help_json
from scalify_cli.output.renderer import ENVELOPE_SCHEMA, EVENT_SCHEMA

# Maps fully-qualified command paths to the schema name (without .json) that
# the command's envelope ``data`` field validates against. Phase 2 covers the
# commands that already emit structured output. New commands should register
# here as they migrate.
COMMAND_SCHEMAS: dict[str, str] = {
    "scalify env": "env",
    "scalify which": "which",
    "scalify run": "run",
    "scalify discover": "discover",
    "scalify auth list": "auth",
    "scalify auth set": "auth",
    "scalify auth remove": "auth",
    "scalify cloud login": "auth",
    "scalify cloud logout": "auth",
    "scalify cloud whoami": "auth",
    "scalify cloud status": "cloud_status",
    "scalify build init": "build_init",
    "scalify build push": "build_push",
    "scalify build pull": "build_pull",
    "scalify build status": "build_status",
    "scalify build ls": "build_ls",
    "scalify build show": "build_show",
    "scalify build release create": "build_release_create",
    "scalify build release ls": "build_release_ls",
    "scalify build release show": "build_release_show",
    "scalify build release logs": "build_release_logs",
    "scalify build release manifest": "build_release_manifest",
    "scalify build release delete": "build_release_delete",
    "scalify build validate": "build_validate",
    "scalify build delete": "build_delete",
    "scalify build update": "build_update",
    "scalify build refs resolve": "build_refs_resolve",
    "scalify build refs base-images": "build_refs_base_images",
    "scalify build refs build-targets": "build_refs_build_targets",
    "scalify build refs model-dirs": "build_refs_model_dirs",
    "scalify build blob ls": "build_blob_ls",
    "scalify deploy up": "deploy_up",
    "scalify deploy promote": "deploy_promote",
    "scalify deploy rollback": "deploy_rollback",
    "scalify deploy rename": "deploy_rename",
    "scalify deploy cancel": "deploy_cancel",
    "scalify deploy history": "deploy_history",
    "scalify deploy status": "deploy_status",
    "scalify deploy ls": "deploy_ls",
    "scalify deploy show": "deploy_show",
    "scalify deploy logs": "deploy_logs",
    "scalify deploy events": "deploy_events",
    "scalify deploy scale": "deploy_scale",
    "scalify deploy stop": "deploy_stop",
    "scalify deploy start": "deploy_start",
    "scalify deploy delete": "deploy_delete",
    "scalify deploy run": "deploy_run",
    "scalify deploy refs compute": "deploy_refs_compute",
    "scalify jobs ls": "jobs",
    "scalify jobs status": "jobs",
    "scalify jobs watch": "jobs",
    "scalify jobs wait": "jobs_wait",
    # workspace lifecycle
    "scalify update": "update",
    # help / validation
    "scalify help": "help",
    # `scalify workflow validate` is the canonical home; `scalify validate` is the
    # hidden deprecated alias — both emit the same workflow-validation payload.
    "scalify workflow validate": "workflow",
    "scalify validate": "workflow",
    # nodes introspection
    "scalify nodes ls": "nodes",
    "scalify nodes show": "nodes",
    "scalify nodes search": "nodes",
    "scalify nodes upstream": "nodes",
    "scalify nodes downstream": "nodes",
    "scalify nodes path": "nodes",
    "scalify nodes types": "nodes",
    "scalify nodes categories": "nodes",
    "scalify nodes refresh": "nodes",
    # The widget catalog gets its OWN schema, not `nodes`: `nodes.json` declares
    # `types` as an array of connection-type names (`nodes types`), and the
    # catalog's `types` is a class_type→entry map. Same key, different contract.
    "scalify nodes widget-catalog": "widget_catalog",
    # workflow editing
    "scalify workflow slots": "workflow",
    "scalify workflow set-slot": "workflow",
    "scalify workflow vary": "workflow",
    "scalify workflow notes": "workflow",
    "scalify workflow print": "workflow",
    # structured edit primitives + recipes (CRDT op-based authoring)
    "scalify workflow insert-workflow": "workflow",
    "scalify workflow add-node": "workflow",
    "scalify workflow connect": "workflow",
    "scalify workflow disconnect": "workflow",
    "scalify workflow set-widget": "workflow",
    "scalify workflow set-node-field": "workflow",
    "scalify workflow delete-node": "workflow",
    "scalify workflow delete-nodes": "workflow",
    "scalify workflow ls-nodes": "workflow",
    # Whole-document edits: same `_finish` op envelope as the primitives above.
    "scalify workflow clear": "workflow",
    "scalify workflow reset-doc": "workflow",
    "scalify workflow apply": "workflow",
    "scalify workflow capture": "workflow",
    "scalify workflow foreach": "workflow",
    # workflow cloud CRUD + fragment composition
    "scalify workflow list": "workflow",
    "scalify workflow get": "workflow",
    "scalify workflow save": "workflow",
    "scalify preview": "preview",
    "scalify workflow delete": "workflow",
    "scalify workflow compose": "workflow",
    "scalify workflow decompose": "workflow",
    "scalify workflow fragment ls": "workflow",
    "scalify workflow fragment show": "workflow",
    "scalify workflow fragment validate": "workflow",
    # the local scalify agent's approvals
    "scalify agent permissions": "agent",
    "scalify agent allow": "agent",
    "scalify agent deny": "agent",
    # skill management
    "scalify skills install": "skill",
    "scalify skills uninstall": "skill",
    "scalify skills show": "skill",
    "scalify skills status": "skill",
    "scalify skills validate": "skill",
    # `scalify skill` is the hidden singular alias; envelopes from the skills
    # group carry the singular form in `command`, so both spellings register.
    "scalify skill install": "skill",
    "scalify skill uninstall": "skill",
    "scalify skill list": "skill",
    "scalify skill show": "skill",
    "scalify skill status": "skill",
    # model discovery (all asset types: checkpoints, loras, controlnets, vae, ...)
    # Canonical spelling under the `model` noun.
    "scalify model search": "models",
    "scalify model show": "models",
    "scalify model list-folders": "models",
    "scalify model list-folder": "models",
    # `scalify models` is the hidden, deprecated plural alias; the discovery
    # envelopes still carry the `models …` form in `command`, so both spellings
    # register (mirrors the `skill`/`skills` alias above).
    "scalify models search": "models",
    "scalify models show": "models",
    "scalify models list-folders": "models",
    "scalify models list-folder": "models",
    # background model downloads (`scalify model download --background`)
    "scalify model download": "download",
    "scalify model download-status": "download_status",
    "scalify model download-cancel": "download_status",
    "scalify model downloads": "downloads",
    # partner-model discovery (`scalify generate`'s two read-only sub-actions —
    # they are argv-tail actions, not Typer subcommands, so they have no node in
    # the help tree; agents resolve them through `command_schemas`).
    "scalify generate list": "generate_list",
    "scalify generate schema": "generate_schema",
    # Terminal result of `scalify generate <model>` / `generate resume` /
    # sync-mode creates: the partner payload wrapped as
    # ``data.result`` (+ ``data.saved`` under --download). These are
    # argv-tail paths too, so they have no help-tree node.
    "scalify generate": "generate_result",
    # curated model-knowledge bundle
    "scalify knowledge status": "knowledge",
    "scalify knowledge resolve": "knowledge",
    "scalify knowledge pick": "knowledge",
    "scalify knowledge authoring": "knowledge",
    # template gallery
    "scalify templates ls": "templates",
    "scalify templates show": "templates",
    "scalify templates fetch": "templates",
    "scalify templates get": "templates",
    "scalify templates refresh": "templates",
    "scalify templates check": "templates",
    # lifecycle
    "scalify launch": "launch",
    "scalify stop": "stop",
    # file transfer
    "scalify upload": "transfer",
    "scalify download": "transfer",
    # project convention
    "scalify project init": "project",
    "scalify project status": "project",
    "scalify assets push": "assets",
    "scalify assets library ls": "assets_library",
    "scalify assets library ensure": "assets_library",
    # config
    "scalify set-default": "set_default",
    # Not a subcommand: the root `--version` flag emits `command="version"`,
    # and this map is keyed by "scalify <emit name>". Verified by
    # tests/scalify_cli/output/test_discovery.py.
    "scalify version": "version",
    # installed-vs-latest report
    "scalify outdated": "outdated",
    # per-pack declared-vs-installed Python dependency report
    "scalify node deps": "node_deps",
    # background server logs
    "scalify logs": "logs",
    # resource management (ScalifyUI /system_stats + /free passthrough)
    "scalify system-stats": "system_stats",
    "scalify free": "free",
}


# Streaming event schemas for commands that emit NDJSON
# (e.g. `scalify --json-stream jobs watch <id>`).


# Streaming commands additionally emit per-line events that validate against a
# different schema. Keyed by command path.
STREAM_EVENT_SCHEMAS: dict[str, str] = {
    "scalify run": "run_event",
    "scalify jobs watch": "run_event",
    # upload progress; under plain --json the same lines go to stderr
    "scalify build push": "build_push_event",
    # the deployment coming up; same rule about stderr
    "scalify deploy up": "deploy_progress_event",
    "scalify deploy status": "deploy_progress_event",
    "scalify deploy promote": "deploy_progress_event",
    "scalify deploy rollback": "deploy_progress_event",
}


def _read_schema(name: str) -> dict[str, Any]:
    pkg = resources.files("scalify_cli.schemas")
    text = (pkg / f"{name}.json").read_text(encoding="utf-8")
    return json.loads(text)


def list_schema_names() -> list[str]:
    pkg = resources.files("scalify_cli.schemas")
    out: list[str] = []
    for child in pkg.iterdir():
        n = child.name
        if n.endswith(".json"):
            out.append(n[:-5])
    return sorted(out)


def load_all_schemas() -> dict[str, dict[str, Any]]:
    """Return ``{schema_name: {name, title, schema}}`` for every shipped schema."""
    bundle: dict[str, dict[str, Any]] = {}
    for name in list_schema_names():
        schema = _read_schema(name)
        bundle[name] = {
            "name": f"{name}.json",
            "title": schema.get("title", name),
            "schema": schema,
        }
    return bundle


def load_error_codes() -> list[dict[str, Any]]:
    """Return the error-code list for the discovery envelope.

    Sourced from the typed registry in :mod:`scalify_cli.error_codes`, which is
    the contract agents branch on.
    """
    from scalify_cli import error_codes

    return [dict(row) for row in error_codes.as_discover_rows()]


def build_discovery(app: Any, *, prog_name: str = "scalify", version: str = "") -> dict[str, Any]:
    """Build the discovery document.

    ``app`` is the root Typer app. Kept untyped to avoid importing typer at
    module import; the call site already has it.
    """
    help_doc = build_help_json(app, prog_name=prog_name)

    schemas = load_all_schemas()

    # Annotate each leaf command with its schema (when known) so agents don't
    # have to cross-reference the schemas map.
    _annotate_schemas(help_doc["commands"], path=[prog_name])

    capabilities = {
        "json_envelope": True,
        "json_stream": True,
        "cancellation": True,
        "cql": True,
        "where_routing": True,
        "where_targets": ["local", "cloud"],
        # Scalify Cloud uses OAuth (Authorization Code + PKCE); third-party
        # services that don't speak OAuth keep the API-key path.
        "cloud_oauth": True,
        "auth_providers": {
            "oauth": ["scalify-cloud"],
            "api_key": ["civitai", "huggingface"],
        },
    }

    return {
        "prog": prog_name,
        "version": version,
        # Versioned machine-output contract (see scalify_cli/output/renderer.py
        # for the constants and the bump rule). Agents negotiate shape on
        # these, not on the CLI `version` above.
        "output_contract": {"envelope": ENVELOPE_SCHEMA, "event": EVENT_SCHEMA},
        "commands": help_doc["commands"],
        "root": help_doc["root"],
        "schemas": schemas,
        "command_schemas": dict(COMMAND_SCHEMAS),
        "stream_event_schemas": dict(STREAM_EVENT_SCHEMAS),
        "error_codes": load_error_codes(),
        "capabilities": capabilities,
    }


def _annotate_schemas(commands: dict[str, Any], *, path: list[str]) -> None:
    for name, entry in commands.items():
        fqp = " ".join(path + [name])
        schema_name = COMMAND_SCHEMAS.get(fqp)
        if schema_name:
            entry["output_schema"] = f"{schema_name}.json"
        stream_schema = STREAM_EVENT_SCHEMAS.get(fqp)
        if stream_schema:
            entry["stream_event_schema"] = f"{stream_schema}.json"
        subs = entry.get("subcommands")
        if subs:
            _annotate_schemas(subs, path=path + [name])
