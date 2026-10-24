"""Scalify Cloud client surface.

Defaults to ``cloud.scalify.khulnasoft.com`` (production). Override via
``SCALIFY_CLOUD_BASE_URL`` — useful when a local frontend dev server (e.g.
``ScalifyUI_frontend`` running ``dev:cloud``) is proxying ``/oauth/*`` to a
test env, or to pin a PR-preview environment for debugging.
"""

from __future__ import annotations

import os

_DEFAULT_BASE_URL = "https://cloud.scalify.khulnasoft.com"


CONFIG_KEY_BASE_URL = "cloud_base_url"


def _resolve_base_url() -> str:
    override = os.environ.get("SCALIFY_CLOUD_BASE_URL")
    if override:
        return override.rstrip("/")
    # Persisted config (set via `scalify cloud set-base-url <url>`).
    try:
        from scalify_cli.config_manager import ConfigManager

        stored = ConfigManager().get(CONFIG_KEY_BASE_URL)
        if stored:
            return stored.rstrip("/")
    except Exception:  # noqa: BLE001 — never fail base-url resolution on a bad config
        pass
    return _DEFAULT_BASE_URL


def get_base_url() -> str:
    """Resolve the cloud base URL fresh.

    Precedence:
    1. ``SCALIFY_CLOUD_BASE_URL`` env var (per-shell).
    2. ``cloud_base_url`` in the persisted CLI config (one-time setup).
    3. Default (``cloud.scalify.khulnasoft.com``).

    Called per-invocation so changes take effect without re-importing.
    """
    return _resolve_base_url()


# Kept for backwards compatibility with call sites that captured this at
# import time. New code should call ``get_base_url()`` instead.
BASE_URL = _resolve_base_url()

# Default OAuth resource path. Appended to the resolved base_url at runtime
# so it works with any environment (production, PR preview, etc.).
# The cloud seed migration provisions two resources:
#   - resource_id "scalify-cloud", resource_uri "/api",  audience "scalify-cloud"
#   - resource_id "scalify-mcp",   resource_uri "/mcp",  audience "scalify-cloud-mcp"
# The CLI targets the scalify-cloud resource (/api) for workflow execution.
_DEFAULT_RESOURCE_PATH = "/api"
_DEFAULT_SCOPES = (
    "scalify-cloud:workflows:read",
    "scalify-cloud:workflows:write",
    "scalify-cloud:jobs:read",
    "scalify-cloud:jobs:write",
    "scalify-cloud:files:read",
    "scalify-cloud:files:write",
    "scalify-cloud:assets:read",
    "scalify-cloud:assets:write",
    "scalify-cloud:hub:read",
    "scalify-cloud:hub:write",
    "scalify-cloud:user:read",
    "scalify-cloud:settings:read",
    "scalify-cloud:settings:write",
    "scalify-cloud:billing:read",
)

CONFIG_KEY_RESOURCE_URL = "cloud_resource_url"
CONFIG_KEY_SCOPES = "cloud_scopes"


def _resolve_resource_url() -> str:
    override = os.environ.get("SCALIFY_CLOUD_RESOURCE_URL")
    if override:
        return override
    try:
        from scalify_cli.config_manager import ConfigManager

        stored = ConfigManager().get(CONFIG_KEY_RESOURCE_URL)
        if stored:
            return stored
    except Exception:  # noqa: BLE001
        pass
    # Derive from the current base_url so PR-preview / staging envs work.
    return _resolve_base_url() + _DEFAULT_RESOURCE_PATH


def _resolve_scopes() -> tuple[str, ...]:
    override = os.environ.get("SCALIFY_CLOUD_SCOPES")
    if override:
        return tuple(s for s in override.split() if s)
    try:
        from scalify_cli.config_manager import ConfigManager

        stored = ConfigManager().get(CONFIG_KEY_SCOPES)
        if stored:
            return tuple(s for s in stored.split() if s)
    except Exception:  # noqa: BLE001
        pass
    return _DEFAULT_SCOPES


def get_resource_url() -> str:
    """Resolve the OAuth resource URL fresh."""
    return _resolve_resource_url()


def get_scopes() -> tuple[str, ...]:
    """Resolve the OAuth scopes fresh."""
    return _resolve_scopes()


# Backwards compat — captured once at import.
RESOURCE_URL = _resolve_resource_url()
DEFAULT_SCOPES = _resolve_scopes()

# Pre-registered first-party client_id for the scalify CLI. Provisioned by the
# cloud's seed migration (20260515000002_seed_oauth_clients_and_resources.sql):
#
#     INSERT INTO oauth_clients (
#       client_id, display_name, redirect_uris, resource_grants, active
#     ) VALUES (
#       'scalify-cli', 'Scalify CLI',
#       '["http://127.0.0.1/callback", "http://[::1]/callback"]'::jsonb,
#       '{"scalify-cloud": ["scalify-cloud:workflows:read", ...]}'::jsonb, true);
#
# The cloud's `MatchRegisteredRedirectURI` honors RFC 8252 §7.3
# (loopback port-variance) for native clients, so we can present any
# ephemeral port at /callback and still match. The PATH must be byte-exact.
CLIENT_ID = "scalify-cli"
CLIENT_NAME = "Scalify CLI"
CALLBACK_PATH = "/callback"
