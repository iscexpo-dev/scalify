# ADR-DEPENDENCIES-0001: Delegate Unified Dependency Resolution to ScalifyUI-Manager

Date: 2026-03-27

## Status

Accepted

## Context

ScalifyUI-Manager already owns `UnifiedDepResolver` and its `uv pip compile`
behavior. scalify-cli needed to expose unified dependency resolution without
creating a second implementation that could drift from the manager.

This decision was originally recorded in
[`DESIGN-uv-compile.md`](../DESIGN-uv-compile.md) and shipped in commit
`0cb2cb8a` through PR #363. The current command implementation and tests still
enforce that boundary.

## Decision

scalify-cli owns command-line selection, configuration, conflict validation, and
process invocation. It delegates unified dependency resolution by passing
`--uv-compile` or invoking `uv-sync` in `cm_cli`; it does not import or
reimplement `UnifiedDepResolver`.

The existing scalify-cli `--fast-deps` path remains a separate mechanism.

## Alternatives considered

- Import `UnifiedDepResolver` into scalify-cli. Rejected because it couples the
  CLI to manager internals and creates shared lifecycle and compatibility work.
- Reimplement unified resolution in scalify-cli. Rejected because it creates two
  authorities for dependency semantics.

## Consequences

### Positive

- Resolver behavior and upgrades remain owned by ScalifyUI-Manager.
- scalify-cli remains a thin, testable command and policy layer.

### Negative

- `--uv-compile` depends on a compatible ScalifyUI-Manager version.
- Manager errors and compatibility behavior cross the subprocess boundary.

## Validation

`scalify_cli/command/custom_nodes/cm_cli_util.py` contains the pass-through, and
the custom-node command tests assert forwarding, precedence, and mutual
exclusion behavior.
