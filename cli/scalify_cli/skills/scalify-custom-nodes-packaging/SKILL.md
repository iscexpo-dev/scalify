---
name: scalify-custom-nodes-packaging
description: Packaged fallback for custom-node registry metadata, validation, and publishing.
---

# Packaging fallback

Registry metadata lives in the pack's `pyproject.toml`. `scalify node init` refuses to overwrite an existing file, so edit in place. `[project]` carries `name`, `description`, `version`, `license`, `dependencies` and `urls.Repository`; `[tool.scalify]` carries `PublisherId`, `DisplayName`, `Icon` and `includes`.

The two compatibility ranges come from different places. `[tool.scalify].requires-scalifyui` states the ScalifyUI range; the frontend range is a `scalifyui-frontend-package` entry in `[project].dependencies`, which is stripped from the published dependency list rather than installed. Declare operating systems and accelerators as `[project].classifiers`.

Run `scalify node validate` before `scalify node publish --token <token>`; it runs the publishing checks without uploading. An empty `project.version` fails, and a dynamic version needs `[tool.scalify.version].path`.

What the archive contains depends on git, and the two cases fail in opposite directions. In a git checkout it is git-tracked files, minus `.scalifyignore` matches, plus every `[tool.scalify].includes` path — `includes` overrides `.scalifyignore`, so an untracked asset that is not listed ships missing. Outside a git checkout, or with no usable `git`, the whole tree is archived minus `.scalifyignore` matches, so an untracked secret or local weight ships. Read the archive's file list before publishing instead of reasoning from the tree.
