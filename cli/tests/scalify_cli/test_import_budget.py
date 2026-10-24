"""Startup import guard for the ``scalify`` entry point.

Every ``scalify`` invocation pays its import graph before doing any work, and
agents (scalify-agent, the MCP server) pay it on every tool call. This test pins
one thing: heavy libraries and subcommand modules that only some commands need
must not load for a trivial ``--version`` call. ``psutil``, GitPython, and the
whole ``scalify_cli.command`` package used to load at startup; see
``scalify_cli/_lazy.py`` and ``scalify_cli/command/__init__.py``.

The measurement is ``python -X importtime -m scalify_cli --json --version``, run
in a subprocess so it sees a cold interpreter exactly like a user does.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

# Modules that must stay off the startup path (a bare name covers the whole
# package). Add to this list when a lazy-import fix lands so the fix is guarded.
FORBIDDEN_AT_STARTUP = (
    "psutil",
    "git",
    "gitdb",
    "requests",
    "urllib.request",  # via scalify_cli.http; downloads only
    "scalify_cli.http",
    "scalify_cli.standalone",
    "scalify_cli.command.custom_nodes",
    "scalify_cli.command.install",
    "scalify_cli.command.run",
    "scalify_cli.command.transfer",
    "scalify_cli.command.project",
    "scalify_cli.command.nodes",
    "scalify_cli.command.launch",
    "scalify_cli.cloud.command",
)

_IMPORT_LINE = re.compile(r"^import time:\s+\d+ \|\s+\d+ \|\s*(\S+)")


def _startup_modules() -> list[str]:
    # pytest-cov's subprocess hook (a .pth file keyed on COV_CORE_* / COVERAGE_*
    # env vars) would load `coverage` and its dependencies into the child before
    # scalify_cli runs, adding a few hundred modules that a user never pays for.
    env = {k: v for k, v in os.environ.items() if not k.startswith(("COV_CORE_", "COVERAGE_"))}
    proc = subprocess.run(
        [sys.executable, "-X", "importtime", "-m", "scalify_cli", "--json", "--version"],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
        env=env,
    )
    assert proc.returncode == 0, (
        f"`scalify --json --version` failed (rc={proc.returncode}); stderr tail: {proc.stderr[-500:]}"
    )
    modules = []
    for line in proc.stderr.splitlines():
        m = _IMPORT_LINE.match(line)
        if m:
            modules.append(m.group(1))
    assert modules, f"no importtime output captured (rc={proc.returncode}); stderr tail: {proc.stderr[-500:]}"
    return modules


def test_heavy_libraries_stay_lazy():
    modules = _startup_modules()
    loaded = sorted(
        forbidden
        for forbidden in FORBIDDEN_AT_STARTUP
        if any(name == forbidden or name.startswith(forbidden + ".") for name in modules)
    )
    assert not loaded, f"imported at startup but should be lazy: {loaded}"
