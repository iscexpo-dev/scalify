# scalify-cli: A Command Line Tool for ScalifyUI

[![Run pytest](https://github.com/Khulnasoft/scalify-cli/actions/workflows/pytest.yml/badge.svg)](https://github.com/Khulnasoft/scalify-cli/actions/workflows/pytest.yml)
[![codecov](https://codecov.io/github/Khulnasoft/scalify-cli/graph/badge.svg?token=S64WJWD2ZX)](https://codecov.io/github/Khulnasoft/scalify-cli)
[![PyPI](https://img.shields.io/pypi/v/scalify-cli.svg)](https://pypi.org/project/scalify-cli/)
[![Downloads](https://static.pepy.tech/badge/scalify-cli/month)](https://pepy.tech/project/scalify-cli)
[![Python](https://img.shields.io/pypi/pyversions/scalify-cli)](https://pypi.org/project/scalify-cli/)
[![License](https://img.shields.io/pypi/l/scalify-cli)](https://github.com/Khulnasoft/scalify-cli/blob/main/LICENSE)

scalify-cli is a command-line tool for installing, running, and extending
[ScalifyUI](https://github.com/khulnasoft/scalify) — the open-source
generative-media engine. Set up ScalifyUI, install custom nodes and models, run
workflows, and call hosted partner image models, all from your terminal.

## Demo

<img src="https://github.com/yoland68/scalify-cli/raw/main/assets/scalify-demo.gif" width="400" alt="Scalify Command Demo">

## Features

- 🚀 One-command ScalifyUI install and launch
- 🎨 Direct calls to partner image and video nodes (Flux, Ideogram, DALL·E, Recraft, Reve, Gemini/nano-banana, Kling, Luma, Runway, Pika, Vidu, Hailuo, Seedance, …) via `scalify generate`, no workflow JSON required
- 🔧 Custom node management — install, update, snapshot, bisect
- 📦 Fast dependency resolution with `uv` (`--fast-deps`, `--uv-compile`)
- 🗄️ Model downloads from CivitAI, Hugging Face, and direct URLs
- 🎬 Run workflows against a local ScalifyUI server, including auto-conversion of UI-format JSON
- 🧪 Test ScalifyUI and frontend pull requests with one flag
- 💻 Cross-platform: Windows, macOS, Linux
- ☁️  Route any workflow to **Scalify Cloud** with `--where cloud` (no GPU required)
- 🤖 Agent-friendly: every command emits structured `--json` envelopes
- 📚 Bundled skills teach Claude / Cursor to drive scalify natively

## Quick Start

```bash
pip install scalify-cli
scalify setup
```

`scalify setup` walks you through everything — local or cloud routing, authentication, and agent skill installation — in one interactive wizard. Pass `-y` for non-interactive (CI/scripted) installs.

## Run a workflow in the cloud

No local GPU? Route any API-format workflow to [Scalify Cloud](https://www.scalify.khulnasoft.com/) with `--where cloud`:

```bash
scalify cloud login                                        # sign in via your browser (OAuth)
scalify run --workflow ./workflow.json --where cloud       # submits, prints a prompt_id, returns immediately
scalify jobs wait <prompt_id> --where cloud                # block until the job finishes (or: jobs status for a one-shot check)
scalify download <prompt_id> --where cloud -o ./outputs    # save the results locally
```

`scalify run` submits asynchronously and prints the `prompt_id` you feed to `jobs`/`download`; add `--wait` to block inline instead. Check your sign-in anytime with `scalify cloud whoami`. Export the workflow JSON from ScalifyUI via **File → Export (API)** (UI-format JSON is auto-converted). Set cloud as your default target so you can drop the flag: `scalify set-default --where cloud`.

**Credits:** cloud generation (`scalify run --where cloud`, `scalify generate`) consumes Scalify Cloud credits and needs an active subscription. Discovery and inspection commands — `scalify cloud whoami`, `scalify cloud status`, `scalify jobs status/ls`, `scalify templates ls`, `scalify generate list` — don't. Check your balance and tier with `scalify cloud status`.

## Installation

1. (Recommended) Activate a virtual environment ([venv](https://docs.python.org/3/library/venv.html) or [conda](https://conda.io/projects/conda/en/latest/user-guide/getting-started.html)).

2. Install with `pip` (requires Python 3.10+):

   ```bash
   pip install scalify-cli
   ```

### Shell Autocomplete

Install shell completion so `scalify <TAB>` expands commands and options:

```bash
scalify --install-completion
```

## Usage

### Installing ScalifyUI

To install ScalifyUI using scalify, simply run:

`scalify install`

This command will download and set up the latest version of ScalifyUI and ScalifyUI-Manager on your
system. If you run in a ScalifyUI repo that has already been setup. The command
will simply update the scalify.yaml file to reflect the local setup

- `scalify install --skip-manager`: Install ScalifyUI without ScalifyUI-Manager.
  To use a custom Manager fork or specific version, skip the default installation
  and install your own into the workspace venv:
  ```bash
  scalify install --skip-manager
  # Then install your custom Manager:
  pip install -e /path/to/your-manager-fork   # editable install
  # or
  pip install scalifyui-manager==4.1b8          # specific version
  ```
- `scalify --workspace=<path> install`: Install ScalifyUI into `<path>/ScalifyUI`.
- `scalify install --fast-deps`: Use `uv` instead of `pip` for faster dependency resolution
  during initial ScalifyUI installation. scalify-cli's built-in resolver compiles all requirements (core + custom nodes)
  into a single lockfile and installs from it. Also handles GPU-specific PyTorch wheel selection automatically.
- For `scalify install`, if no path specification like `--workspace, --recent, or --here` is provided, it will be implicitly installed in `<HOME>/scalify`.

#### Python environment handling

When you run `scalify install`, scalify-cli picks a Python environment for ScalifyUI
dependencies using the following precedence:

1. An **active virtualenv or conda** environment (`VIRTUAL_ENV` / `CONDA_PREFIX`) is used as-is.
2. An **existing `.venv` or `venv`** directory inside the workspace is reused.
3. Otherwise the choice depends on how scalify-cli was installed:
   - **`pip install scalify-cli`** (global / system Python): dependencies go
     directly into the same Python environment. This is the typical Docker setup.
   - **`pipx install scalify-cli`** or **`uv tool install scalify-cli`** (isolated
     tool environment): a `.venv` is created inside the ScalifyUI workspace.
     Use `scalify launch` to start ScalifyUI with the correct Python.

### Updating ScalifyUI

`scalify update` brings an existing workspace up to date:

- `scalify update` (or `scalify update scalify`): pull the branch the workspace is currently on and reinstall `requirements.txt`.
- `scalify update all`: also update every installed custom node.
- `scalify update cli`: upgrade scalify-cli itself.

By default `scalify update all` exits 0 even when the custom-node update step fails — the error is printed, but the exit code says success, so scripts and wrappers can't tell. Pass `--exit-on-fail` (the same flag name and default as `scalify node install --exit-on-fail`) to have that failure exit non-zero instead. The flag only changes the `all` target; `scalify update scalify` and `scalify update cli` already exit non-zero when they fail, and accept the flag as a no-op so it can be forwarded unconditionally.

One limit worth knowing: `--exit-on-fail` can only surface what ScalifyUI-Manager's `cm-cli update` reports. `cm-cli` currently handles a *single* pack failing to update by printing `ERROR: ...` and carrying on, still exiting 0, so that particular case stays invisible until ScalifyUI-Manager propagates it. Unlike `scalify node install`, the flag is not forwarded to `cm-cli` — only its `install` subcommand accepts `--exit-on-fail`; its `update` subcommand has no such option and would reject it.

When the flag does fire, the exit code is `cm-cli`'s own, normalized so it is always usable: a process killed by a signal becomes `128+N` rather than a truncated value, an exit code that would truncate to 0 becomes 1, and 2 becomes 1 so it can't be mistaken for a CLI usage error. In `--json` mode the failure is also reported as an `update_custom_nodes_failed` error envelope carrying `cm-cli`'s raw status in `details.cm_cli_returncode`.

#### Switching to a specific version

`scalify update scalify --version <X>` moves an existing workspace to a specific ScalifyUI version — a downgrade (rollback) or an upgrade — without prompting for anything, so it is safe to run headlessly or from a script. `<X>` is `nightly` (the repo's default branch), `latest` (the newest stable release), or a version number such as `0.3.0` (a leading `v` is optional).

```bash
scalify update scalify --version 0.3.0      # roll back to the v0.3.0 release
scalify update scalify --version latest     # newest stable release
scalify update scalify --version nightly    # roll forward to the default branch
```

Behavior worth knowing:

- **The target is validated before anything is touched.** An unknown version exits non-zero, lists the nearest available versions, and leaves the working tree exactly as it was.
- **Uncommitted changes are stashed by default** (`git stash push -u`) and are *never* popped or dropped automatically — the stash ref is printed so you can restore them with `git stash pop`. Pass `--no-stash` if you would rather the command refuse to run on a dirty tree.
- **A version number checks out a tag, which leaves a detached HEAD.** That is expected. Roll forward again with `scalify update scalify --version nightly` (or `--version latest`); a plain `scalify update` cannot advance a detached HEAD.
- **Dependencies are reinstalled** from the target version's `requirements.txt`. PyTorch is deliberately left alone: the ScalifyUI version doesn't determine your torch build, your machine does. If the dependency install fails, the command exits non-zero and says so — the tree is already on the new version, and re-running the same command is safe.
- `--version` and `--no-stash` apply only to target `scalify`; combining `--version` with `all` or `cli` is an error.

### Specifying execution path

- You can specify the path of ScalifyUI where the command will be applied through path indicators as follows:
  - `scalify --workspace=<path>`: Run from the ScalifyUI installed in the specified workspace.
  - `scalify --recent`: Run from the recently executed or installed ScalifyUI.
  - `scalify --here`: Run from the ScalifyUI located in the current directory.
- --workspace, --recent, and --here options cannot be used simultaneously.
- If there is no path indicator, the following priority applies:

  - Run from the default ScalifyUI at the path specified by `scalify set-default <path>`.
  - Run from the recently executed or installed ScalifyUI.
  - Run from the ScalifyUI located in the current directory.

- Example 1: To run the recently executed ScalifyUI:
  - `scalify --recent launch`
- Example 2: To install a package on the ScalifyUI in the current directory:
  - `scalify --here node install scalifyui-impact-pack`
- Example 3: To update the automatically selected path of ScalifyUI and custom nodes based on priority:

  - `scalify node update all`

- You can use the `scalify which` command to check the path of the target workspace.
  - e.g `scalify --recent which`, `scalify --here which`, `scalify which`, ...

### Default Setup

The default sets the option that will be executed by default when no specific workspace's ScalifyUI has been set for the command.

`scalify set-default <workspace path> ?[--launch-extras="<extra args>"]`

- `--launch-extras` option specifies extra args that are applied only during launch by default. However, if extras are specified at the time of launch, this setting is ignored.

### Launch ScalifyUI

Scalify provides commands that allow you to easily run the installed ScalifyUI.

`scalify launch`

- To run with default ScalifyUI options:

  `scalify launch -- <extra args...>`

  `scalify launch -- --cpu --listen 0.0.0.0`

  - When you manually configure the extra options, the extras set by set-default will be overridden.

- To run background

  `scalify launch --background`

  `scalify --workspace=~/scalify launch --background -- --listen 10.0.0.10 --port 8000`

  - Instances launched with `--background` are displayed in the "Background ScalifyUI" section of `scalify env`, providing management functionalities for a single background instance only.
  - Background-running ScalifyUI can be stopped with `scalify stop`.

- To point **every** command (not just one) at a ScalifyUI on a non-default
  address — e.g. a server you started _outside_ scalify-cli on `:8189` — export
  the `SCALIFY_LOCAL_URL` environment variable:

  `export SCALIFY_LOCAL_URL=http://127.0.0.1:8189`

  - Accepts `http://host:port`, `host:port`, or `http://host` (the port
    defaults to `8188`; the scheme is optional and, if present, must be
    `http`). IPv6 literals are bracketed: `SCALIFY_LOCAL_URL=http://[::1]:8189`.
  - Honored by `scalify env`, `scalify run`, `scalify jobs`, `scalify upload`/`download`,
    `scalify nodes`, and every other local-targeting command, so `scalify env`'s
    "Scalify Server Running" line now probes and reports the resolved address.
  - Precedence (per command): a per-command `--host`/`--port` flag wins, then
    `SCALIFY_LOCAL_URL`, then a scalify-cli-launched background server, then the
    `127.0.0.1:8188` default. A malformed value is ignored with a one-line
    stderr warning rather than breaking the command.

- to run ScalifyUI with a specific pull request:

  `scalify install --pr "#1234"`

  `scalify install --pr "jtydhr88:load-3d-nodes"`

  `scalify install --pr "https://github.com/khulnasoft/scalify/pull/1234"`

  - If you want to run ScalifyUI with a specific pull request, you can use the `--pr` option. This will automatically install the specified pull request and run ScalifyUI with it.
  - Important: The --pr option cannot be combined with --version or --commit and will be rejected if used together.

- To test a frontend pull request:

  ```
  scalify launch --frontend-pr "#456"
  scalify launch --frontend-pr "username:branch-name"
  scalify launch --frontend-pr "https://github.com/Khulnasoft/scalify/pull/456"
  ```

  - The `--frontend-pr` option allows you to test frontend PRs by automatically cloning, building, and using the frontend for that session.
  - Requirements: Node.js and npm must be installed to build the frontend.
  - Builds are cached for quick switching between PRs - subsequent uses of the same PR are instant.
  - Each PR is used only for that launch session. Normal launches use the default frontend.

  **Managing PR cache**:
  ```
  scalify pr-cache list              # List cached PR builds
  scalify pr-cache clean             # Clean all cached builds
  scalify pr-cache clean 456         # Clean specific PR cache
  ```

  - Cache automatically expires after 7 days
  - Maximum of 10 PR builds are kept (oldest are removed automatically)
  - Cache limits help manage disk space while keeping recent builds available

- To check VRAM/RAM usage: `scalify system-stats` (add `--where cloud` to target Scalify Cloud instead of local)
- To unload models / free the executor cache: `scalify free` (pass `--free-memory` to also reset the executor cache)

### Managing Custom Nodes

scalify provides a convenient way to manage custom nodes for extending ScalifyUI's functionality. Here are some examples:

- Show custom nodes' information:

```
scalify node [show|simple-show] [installed|enabled|not-installed|disabled|all|snapshot|snapshot-list]
                             ?[--channel <channel name>]
                             ?[--mode [remote|local|cache]]
```

- `scalify node show all --channel recent`

  `scalify node simple-show installed`

  `scalify node update all`

  `scalify node install scalifyui-impact-pack`

  > **Note:** the argument is the node's **Scalify Registry ID**, which is
  > lowercase (e.g. `scalifyui-impact-pack`), not the GitHub repository name
  > (`ScalifyUI-Impact-Pack`). Passing the repo-name casing fails to resolve with
  > an error like `Node 'ScalifyUI-Impact-Pack@unknown' not found`. Find a node's
  > ID on its [Scalify Registry](https://registry.scalify.khulnasoft.com) page or via
  > `scalify node show all`.

- Managing snapshot:

  `scalify node save-snapshot`

  `scalify node restore-snapshot <snapshot name>`

- Install dependencies:

  `scalify node install-deps --deps=<deps .json file>`

  `scalify node install-deps --workflow=<workflow .json/.png file>`

- Generate deps:

  `scalify node deps-in-workflow --workflow=<workflow .json/.png file> --output=<output deps .json file>`

#### `install` vs `registry-install`

scalify-cli offers two ways to install a custom node, backed by different
mechanisms:

- **`scalify node install <id>...`** delegates to
  [ScalifyUI-Manager](https://github.com/Khulnasoft/ScalifyUI-Manager)'s `cm-cli`.
  It accepts one or more node IDs, resolves them through the Manager's channel
  database (`--channel`, `--mode`), and installs dependencies via the Manager
  (so it also supports `--fast-deps`, `--no-deps`, and `--uv-compile`). This is
  the recommended command for day-to-day node management, and it requires
  ScalifyUI-Manager to be present in the workspace.

  `scalify node install scalifyui-impact-pack`

- **`scalify node registry-install <id> [--version <v>]`** talks directly to the
  [Scalify Registry](https://registry.scalify.khulnasoft.com) API. It downloads the published
  archive for a single node (optionally pinned with `--version`), extracts it
  into `custom_nodes/`, and runs the node's own install script. It does **not**
  go through ScalifyUI-Manager, so it does not require the Manager to be
  installed — this is the command the Registry's own install instructions use.

  `scalify node registry-install scalifyui-impact-pack`

  `scalify node registry-install scalifyui-impact-pack --version 1.0.0`  # install a specific version

  Because `registry-install` bypasses the Manager's dependency machinery and
  simply runs the node's bundled install script, it only accepts
  `--force-download` — it does **not** accept `--fast-deps`, `--no-deps`, or
  `--uv-compile`. If you want fast/unified dependency resolution, use
  `scalify node install` instead.

#### Unified Dependency Resolution (--uv-compile)

Requires ScalifyUI-Manager v4.1+. Instead of installing dependencies per-node with
`pip install`, `--uv-compile` delegates to ScalifyUI-Manager's unified resolver which batch-resolves
all custom node dependencies via `uv pip compile` with **cross-node conflict detection** —
it can identify which node packs have incompatible dependencies and why.

- Install with unified resolution:

  `scalify node install scalifyui-impact-pack --uv-compile`

- Available on: `install`, `reinstall`, `update`, `fix`, `restore-snapshot`,
  `restore-dependencies`, `install-deps`

- Run standalone (resolve all existing custom node dependencies):

  `scalify node uv-sync`

- `--uv-compile` is mutually exclusive with `--fast-deps` and `--no-deps` —
  except on `restore-snapshot`, where `--fast-deps` selects the `--uv-compile`
  path instead (see [--fast-deps](#--fast-deps) below).

- To make `--uv-compile` the default for all commands, see
  [uv-compile default](#uv-compile-default) below.

- Use `--no-uv-compile` to override the default for a single command:

  `scalify node install scalifyui-impact-pack --no-uv-compile`

#### --fast-deps

`--fast-deps` swaps scalify-cli's dependency installation from `pip` to scalify-cli's
built-in `uv`-based resolver (`DependencyCompiler`), which is significantly
faster and only requires `uv` (no ScalifyUI-Manager). On a dependency version
conflict it prompts you interactively to pick a version.

- Accepted by: `scalify install`, `scalify node install`, `scalify node reinstall`,
  and `scalify node restore-snapshot`.

  `scalify install --fast-deps`

  `scalify node install scalifyui-impact-pack --fast-deps`

- **Not** accepted by `scalify node registry-install`: that command installs a
  node directly from the Scalify Registry by running the node's own bundled
  install script, so it never touches scalify-cli's dependency resolver (see
  [`install` vs `registry-install`](#install-vs-registry-install) above).
- Mutually exclusive with `--no-deps` and `--uv-compile`, where those flags
  exist — the exact pairing is per-command:

  | Command | Rejected combination |
  |---------|----------------------|
  | `scalify node install` | `--fast-deps --no-deps`, `--fast-deps --uv-compile` |
  | `scalify node reinstall` | `--fast-deps --uv-compile` (no `--no-deps` on this command) |
  | `scalify node restore-snapshot` | `--fast-deps --no-uv-compile` (see below) |
  | `scalify install` | none (neither flag exists on this command) |

- **Exception — `scalify node restore-snapshot`:** here `--fast-deps` *selects*
  the `--uv-compile` fast path rather than conflicting with it. ScalifyUI-Manager's
  `cm-cli` has no `--no-deps` on `restore-snapshot`, and its `--uv-compile`
  already implies no-deps internally, so the two are synonyms on this command.
  Combining `--fast-deps` with `--no-uv-compile` is the contradiction, and it
  errors: `Cannot use --fast-deps with --no-uv-compile`.

#### --fast-deps vs --uv-compile

Both flags use `uv` for faster dependency resolution, but they work differently:

|                       | `--fast-deps`                                   | `--uv-compile`                                |
|-----------------------|-------------------------------------------------|-----------------------------------------------|
| **Resolver**          | scalify-cli built-in (`DependencyCompiler`)       | ScalifyUI-Manager (`UnifiedDepResolver`)        |
| **Scope**             | `scalify install`, `scalify node install/reinstall/restore-snapshot` | Custom node commands only    |
| **Conflict handling** | Interactive prompt to pick a version            | Automatic detection with node attribution     |
| **Config default**    | No                                              | Yes (`scalify manager uv-compile-default true`) |
| **Requires**          | Only `uv`                                       | ScalifyUI-Manager v4.1+                         |

**When to use which:**
- For initial ScalifyUI installation with uv: `scalify install --fast-deps`
- For custom node management with Manager v4.1+: `--uv-compile` (recommended)
- For custom node management with older Manager: `--fast-deps`

#### Bisect custom nodes

If you encounter bugs only with custom nodes enabled, and want to find out which custom node(s) causes the bug,
the bisect tool can help you pinpoint the custom node that causes the issue.

- `scalify node bisect start`: Start a new bisect session with optional ScalifyUI launch args. It automatically marks the starting state as bad, and takes all enabled nodes when the command executes as the test set.
- `scalify node bisect good`: Mark the current active set as good, indicating the problem is not within the test set.
- `scalify node bisect bad`: Mark the current active set as bad, indicating the problem is within the test set.
- `scalify node bisect reset`: Reset the current bisect session.

### Managing Models

- Model downloading

  `scalify model download --url <URL> ?[--relative-path <PATH>] ?[--set-civitai-api-token <TOKEN>] ?[--set-hf-api-token <TOKEN>]`

  - URL: CivitAI page, Hugging Face file URL, etc...
  - You can also specify your API tokens via the `CIVITAI_API_TOKEN` and `HF_API_TOKEN` environment variables. The order of priority is `--set-X-token` (always highest priority), then the environment variables if they exist, and lastly your config's stored tokens from previous `--set-X-token` usage (which remembers your most recently set token values).
  - Tokens provided via the environment variables are never stored persistently in your config file. They are intended as a way to easily and safely provide transient secrets.

- Model remove

  `scalify model remove ?[--relative-path <PATH>] --model-names <model names>`

- Model list

  `scalify model list ?[--relative-path <PATH>]`

### Running on Scalify Cloud (`--where cloud`)

Scalify Cloud runs your workflow on Scalify's GPUs — no local ScalifyUI install and no GPU required. The same verbs you use locally take `--where cloud`; the only extra step is signing in once.

Prerequisites — a Scalify account with a credit balance ([add credits](https://docs.scalify.khulnasoft.com/interface/credits); cloud runs are metered per GPU-second):

```bash
scalify cloud login                   # opens your browser (OAuth + PKCE), stores a session
scalify cloud whoami                  # confirm who you're signed in as
scalify cloud status                  # workspace, credit balance, tier, concurrency limit
```

Then submit, watch, and collect:

```bash
scalify run --workflow my_workflow_api.json --where cloud   # submits, prints a prompt_id, returns
scalify jobs ls --where cloud                               # queue + history for your account
scalify jobs status <prompt_id> --where cloud               # one job's state
scalify jobs watch <prompt_id> --where cloud                # live progress until it finishes
scalify download <prompt_id> --where cloud                  # fetch the outputs
```

Notes:

- `--where cloud` is per-invocation. Make it the default with `scalify set-default --where cloud`; every command then honors it without the flag, and `--where local` overrides it for one call. Clear it again with `scalify set-default --clear-where`.
- Add `--wait` to `scalify run` to block until the job completes instead of returning immediately.
- `scalify run --prompt "<text>"` (no `--workflow`) runs a bundled default text2img graph. **That graph loads the SD1.5 checkpoint `v1-5-pruned-emaonly.ckpt`, which scalify-cli does not download for you** — install it into `models/checkpoints`, or point the graph at a checkpoint you do have with `scalify run --prompt "…" --set checkpoint=<name>`. The same applies on cloud, where the checkpoint must exist in your cloud assets.
- `scalify download` also reads a `prompt_id` from piped stdin, so `scalify run ... --where cloud | scalify download --where cloud` works.
- Models and custom nodes must exist on the cloud side. `scalify models search --where cloud` lists the cloud asset catalog, and `scalify nodes ls --where cloud` lists the node classes cloud can run.
- Sign out with `scalify cloud logout`. If a run fails with `cloud_unauthorized`, your session expired — re-run `scalify cloud login`.

### Calling partner nodes (`scalify generate`)

`scalify generate` calls Scalify's partner nodes directly from the terminal — no
local ScalifyUI or workflow JSON required. It hits the same hosted partner nodes
you'd otherwise wire into a ScalifyUI workflow, but as one-shot CLI calls. Image
models (Flux, Ideogram, DALL·E, Recraft, Runway, Reve, xAI Grok, Google
Gemini Flash Image aka **nano-banana**, …) and video models (Kling,
Luma, Runway Gen-3, Pika, Vidu, Moonvalley, Hailuo, Grok video, ByteDance
**Seedance**) are all covered; video jobs run async and the CLI polls until
the result is ready.

Prerequisites — a Scalify API key and a credit balance:

- [Create an API key](https://docs.scalify.khulnasoft.com/development/scalifyui-server/api-key-integration)
- [Browse partner nodes and per-call credit costs](https://docs.scalify.khulnasoft.com/tutorials/partner-nodes/overview) · [pricing table](https://docs.scalify.khulnasoft.com/tutorials/partner-nodes/pricing)
- [Add credits](https://docs.scalify.khulnasoft.com/interface/credits)

Set the key once, then go:

```bash
export SCALIFY_API_KEY=scalifyui-...   # or pass --api-key on each call

scalify generate list                                  # browse available models
scalify generate schema flux-pro                       # see params for one model
scalify generate flux-pro --prompt "a cat on the moon" \
    --width 1024 --height 1024 --download cat.png
```

Reference images can be passed as local paths — the CLI uploads them through
the cloud's storage endpoint (or base64-encodes inline, as each partner
requires):

```bash
scalify generate flux-kontext --prompt "add a top hat" \
    --input_image ./photo.jpg --download out.png

scalify generate upload ./photo.jpg                    # explicit upload
```

Async models (every video model plus the Flux family) block until ready by
default. Pass `--async` to return immediately with a job id, then resume later
with `scalify generate resume <model> <job_id>`. Examples:

```bash
scalify generate kling --prompt "a paper boat drifting on a river at dusk" \
    --duration 5 --download boat.mp4

scalify generate luma --prompt "..." --aspect_ratio 16:9 --async
# → prints job id; resume with:
scalify generate resume luma <job_id> --download out.mp4
```

**Gemini Flash Image (nano-banana)** — text-to-image and image edits in one
alias. Pass `--image` (repeatable) for reference images. The response is
inline base64, so `--download` is required to save:

```bash
scalify generate nano-banana --prompt "a watercolor of a sleeping fox" \
    --download fox.png

# Image edit — reference accepted as a local path, http(s) URL, or data URI:
scalify generate nano-banana --prompt "add a top hat" \
    --image ./cat.png --download out.png

# Switch model variants:
scalify generate nano-banana --prompt "..." --model gemini-3-pro-image-preview \
    --download out.png
```

**Seedance** — text-to-video and image-to-video, up to 1080p / 12s clips.
Resolution, ratio, duration, fps, etc. get passed through as flags; the CLI
inlines them into Seedance's prompt syntax for you:

```bash
scalify generate seedance --prompt "a hummingbird hovering over a flower" \
    --resolution 1080p --duration 5 --download bird.mp4

# Image-to-video: pick a lite/i2v variant and pass a first frame.
scalify generate seedance --model seedance-1-0-lite-i2v-250428 \
    --prompt "the wave crests and crashes" \
    --image ./still.jpg --download wave.mp4
```

### Managing ScalifyUI-Manager

- Disable ScalifyUI-Manager completely (no manager flags passed to ScalifyUI):

  `scalify manager disable`

- Enable ScalifyUI-Manager with new GUI:

  `scalify manager enable-gui`

- Enable ScalifyUI-Manager without GUI (manager runs but UI is hidden):

  `scalify manager disable-gui`

- Enable ScalifyUI-Manager with legacy GUI:

  `scalify manager enable-legacy-gui`

- Clear reserved startup action:

  `scalify manager clear`

- Migrate legacy git-cloned ScalifyUI-Manager to pip package:

  `scalify manager migrate-legacy`

#### uv-compile default

Set `--uv-compile` as the default behavior for all custom node operations:

  `scalify manager uv-compile-default true`

When enabled, all node commands (`install`, `reinstall`, `update`, `fix`,
`restore-snapshot`, `restore-dependencies`, `install-deps`) will automatically
use `--uv-compile`. Use `--no-uv-compile` on any individual command to override.

To disable:

  `scalify manager uv-compile-default false`

## Beta Feature: format of scalify-lock.yaml (WIP)

```
basic:

models:
  - model: [name of the model]
    url: [url of the source, e.g. https://huggingface.co/...]
    paths: [list of paths to the model]
      - path: [path to the model]
      - path: [path to the model]
    hashes: [hashes for the model]
      - hash: [hash]
        type: [AutoV1, AutoV2, SHA256, CRC32, and Blake3]
    type: [type of the model, e.g. diffuser, lora, etc.]

  - model:
  ...

# compatible with ScalifyUI-Manager's .yaml snapshot
custom_nodes:
  scalifyui: [commit hash]
  file_custom_nodes:
  - disabled: [bool]
    filename: [.py filename]
    ...
  git_custom_nodes:
    [git-url]:
      disabled: [bool]
      hash: [commit hash]
    ...
```

## Curated model knowledge

Discovery commands can attach a `knowledge` block to their `--json` output: which
model a name refers to, whether it is deprecated, ranked picks per capability,
and known pitfalls. A signed-in install (`scalify cloud login`) fetches the bundle
from the cloud knowledge channel on its own. Signed out, the fetch fails quietly
and no block is emitted unless a bundle is already cached.

Point the CLI at a different bundle with either of:

```
export SCALIFY_KNOWLEDGE_URL=https://.../knowledge.json   # fetched and cached
export SCALIFY_KNOWLEDGE_FILE=/path/to/knowledge.json     # read directly, never cached
```

Check what is loaded:

```
scalify knowledge status
scalify knowledge resolve "Kling 3.0"
scalify knowledge pick lipsync
```

Turn it off again:

```
export SCALIFY_KNOWLEDGE_DISABLE=1
```

Signing out is *not* an off switch. Once a bundle is cached it keeps being
served, stale or not. `SCALIFY_KNOWLEDGE_DISABLE` suppresses envelope
enrichment outright; the `scalify knowledge` verbs keep working under it, since
those are you asking for the bundle directly.

Enrichment only ever reads the cache, so no command waits on a fetch. The cache
refreshes during `scalify skills install` and in the background during
`scalify launch`, or on demand with `scalify knowledge status --refresh`.

## Analytics

Analytics are **opt-in and off by default**. The first time you run the CLI in an
interactive terminal it asks whether to enable tracking, and that prompt defaults
to no. Nothing is sent unless you answer yes. A non-interactive run (a pipe, CI,
an agent) never enables it on its own. Setting `DO_NOT_TRACK` or
`SCALIFY_NO_TELEMETRY` in the environment overrides the setting and suppresses
everything.

Change your mind at any time:

```
scalify tracking enable
scalify tracking disable
```

When tracking is on, we use Mixpanel to understand usage patterns and know where
to prioritize our efforts.

**One event carries text you typed.** If a curated knowledge bundle is loaded
(a signed-in install fetches one on its own), then `scalify nodes search`,
`scalify templates ls`, `scalify generate schema`,
`scalify generate list` and `scalify models search` send the search terms you typed
and which curated entries they matched. This tells us what people look for and fail
to find. It needs both the bundle and your tracking consent, so with either one
absent nothing is sent.

Check out the usage here: [Mixpanel Board](https://mixpanel.com/p/13hGfPfEPdRkjPtNaS7BYQ)

## Contributing

We welcome contributions to scalify-cli! For ideas, suggestions, or bug reports,
open an issue at [Khulnasoft/scalify-cli](https://github.com/Khulnasoft/scalify-cli/issues).
For code changes, fork the repo and open a pull request.

See [CONTRIBUTING.md](/CONTRIBUTING.md) for setup, the checks CI enforces,
and PR conventions. Notable changes are recorded in [CHANGELOG.md](/CHANGELOG.md).

## License

Released under the [GNU General Public License v3.0](https://github.com/Khulnasoft/scalify-cli/blob/main/LICENSE).

## Support

Questions or issues? [Open an issue](https://github.com/Khulnasoft/scalify-cli/issues)
or reach us on [Discord](https://discord.com/invite/scalify).

Happy diffusing with ScalifyUI and scalify-cli! 🎉
