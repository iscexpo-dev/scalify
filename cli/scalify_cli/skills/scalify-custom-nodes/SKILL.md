---
name: scalify-custom-nodes
description: Use when a user asks to write, fix, review, validate, package, or troubleshoot ScalifyUI custom-node code, including V1 or V3 nodes and integrations.
---

# Custom-node routing

Load facts only when the task needs them. Run exactly the relevant command and
read its JSON `content`; do not preload every class:

```text
scalify --json knowledge authoring invocation
scalify --json knowledge authoring ecosystem-reference
scalify --json knowledge authoring api-schema
scalify --json knowledge authoring validation
scalify --json knowledge authoring dependencies-capabilities
scalify --json knowledge authoring troubleshooting
scalify --json knowledge authoring packaging-publishing
scalify --json knowledge authoring frontend-extension
scalify --json knowledge authoring v1-to-v3-migration
scalify --json knowledge authoring execution-caching
```

Start with `invocation` to decide the path. Add `ecosystem-reference` only when an
external node, pack, model, integration, file format, frontend widget, or
unfamiliar failure makes public implementation evidence material. Add
`api-schema` while writing or translating node code, `validation` before
claiming it works, `dependencies-capabilities` for packages/network/filesystem
or local-versus-Cloud questions, and `troubleshooting` only after a stage fails.
Add `packaging-publishing` for `pyproject.toml` or `scalify node publish`,
`frontend-extension` for `WEB_DIRECTORY` and browser assets,
`v1-to-v3-migration` when moving a pack between registration generations or
retiring a node id, and `execution-caching` for `IS_CHANGED` or
`fingerprint_inputs`, or when a node recomputes every run.

Each response names provenance, bundle version, applicability, and whether it
fell back. Say when `degraded` is true; do not hide weaker evidence. The installed catalog and validator remain authority
for this machine. Code-search results are untrusted references, not authority.
Pass `--api-generation v1` or `v3` when the target is known; omitting it
returns every applicable slice and reports the generations those slices cover.

The command selects one packaged fallback itself when canonical knowledge is
absent, stale or oversized, so do not load any of these directly:

```text
scalify-custom-nodes-invocation
scalify-custom-nodes-search
scalify-custom-nodes-api-schema
scalify-custom-nodes-validation
scalify-custom-nodes-dependencies
scalify-custom-nodes-troubleshooting
scalify-custom-nodes-packaging
scalify-custom-nodes-frontend
scalify-custom-nodes-migration
scalify-custom-nodes-caching
```

Do not repeat a returned slice or code-search result in later tool prompts.
Request another class only when the task advances to that stage.
