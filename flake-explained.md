# flake.nix — Explained

This Nix flake sets up a reproducible Python development environment for a project called **timeo/senzu**, using `uv` for dependency management, `uv2nix` to bridge uv lockfiles into Nix, and `pre-commit` for code quality hooks.

---

## Inputs

The flake pulls in six external inputs, all pinned and wired to share the same `nixpkgs` source:

| Input | Source | Purpose |
|---|---|---|
| `nixpkgs` | `nixos-unstable` branch | Base package set |
| `flake-utils` | numtide/flake-utils | Multi-system output helpers |
| `uv2nix` | pyproject-nix/uv2nix | Converts `uv.lock` into Nix derivations |
| `pyproject-nix` | pyproject-nix/pyproject.nix | Reads `pyproject.toml` metadata |
| `pyproject-build-systems` | pyproject-nix/build-system-pkgs | Nix overlays for Python build backends |
| `pre-commit-hooks` | cachix/git-hooks.nix | Declarative pre-commit hook management |

All inputs that accept `nixpkgs` are pointed at the same instance via `inputs.nixpkgs.follows = "nixpkgs"`, ensuring a consistent package set and avoiding duplicate downloads.

---

## Outputs

Outputs are generated for every default system (Linux x86_64/aarch64, macOS x86_64/aarch64) using `flake-utils.lib.eachDefaultSystem`.

### Python Environment Construction

The environment is built in layers:

1. **Workspace loading** — `uv2nix` reads your `pyproject.toml` and `uv.lock` from the repo root.
2. **Overlay** — A Nix overlay is generated from the resolved lockfile, preferring pre-built wheels over source builds.
3. **Base Python set** — `pyproject-nix` constructs a Python 3.12 package set, extended with the build-systems overlay and the uv lockfile overlay.

This yields two distinct virtual environments:

| Env | Name | Contents | Use case |
|---|---|---|---|
| `timeoEnv` | `timeo-env` | Default (non-dev) dependencies only | Production / packaging |
| `devEnv` | `timeo-dev-env` | All deps including dev extras, `senzu` editable | Day-to-day development |

The editable install uses a separate overlay (`editableOverlay`) that installs the `senzu` package pointing at `$REPO_ROOT` on disk — changes to source files are reflected immediately without reinstalling. Hatchling's `editables` package is injected as a build-time dependency to make this work correctly.

### Packages & Apps

- **`packages.default`** — the frozen `timeoEnv` virtualenv.
- **`apps.default`** — runs `senzu` directly via `nix run`, sourced from `timeoEnv`.

### Dev Shells

Two shells are provided, both sharing the same base configuration:

**Shared shell config (`shellEnv` + `shellHook`)**
- `UV_NO_SYNC=1` — prevents uv from re-creating the virtualenv (Nix already manages it).
- `UV_PYTHON` — points uv at the Nix-managed Python interpreter.
- `UV_PYTHON_DOWNLOADS=never` — prevents uv from downloading its own Python binary.
- On entry, `PYTHONPATH` is cleared and `REPO_ROOT` is set to the git repo root.

**`devShells.default`** (used by `nix develop`)
Base packages: `devEnv`, `uv`, `pre-commit`, `go-task`. Assumes `gcloud` is already available on the host PATH if needed.

**`devShells.with-gcloud`** (used by `nix develop .#with-gcloud`)
Same as default, but adds `google-cloud-sdk`. Intended for fresh machines or CI environments that don't have gcloud pre-installed.

### Checks & Pre-commit Hooks

Running `nix flake check` installs and runs the following pre-commit hooks against the repo:

| Hook | Purpose |
|---|---|
| `ruff` | Python linting |
| `ruff-format` | Python formatting |
| `mypy` | Static type checking |
| `check-toml` | Validates TOML files |
| `check-yaml` | Validates YAML files |
| `end-of-file-fixer` | Ensures files end with a newline |
| `trim-trailing-whitespace` | Removes trailing whitespace |

---

## Quick Reference

```bash
# Enter the default dev shell
nix develop

# Enter the dev shell with gcloud included
nix develop .#with-gcloud

# Run the senzu app directly
nix run

# Run checks (installs pre-commit hooks)
nix flake check

# Build the production virtualenv
nix build
```
