"""Local credential store for scalify-cli.

Where keys live:

    ${XDG_CONFIG_HOME or platform-equivalent}/scalify-cli/secrets.json

Format::

    {
      "providers": {
        "scalify-cloud": {"key": "sk-…", "updated_at": "2026-05-15T12:00:00Z"},
        "civitai":     {"key": "...",  "updated_at": "..."}
      }
    }

The file is created with mode ``0600``. Phase 5 will replace this plaintext
JSON with an encrypted ``secrets.bin``; the API surface here is the
forward-compatible interface, so call sites don't need to change.

Local-only: this module never makes a network call.
"""

from scalify_cli.auth import store
from scalify_cli.auth.store import SUPPORTED_PROVIDERS, AuthRecord

__all__ = ["AuthRecord", "SUPPORTED_PROVIDERS", "store"]
