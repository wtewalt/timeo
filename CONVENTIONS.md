# Conventions

Best practices and rules for making changes to this repository.

---

## Development Environment

This repo uses [Nix flakes](https://nixos.wiki/wiki/Flakes) to provide a fully reproducible development environment. **All development and testing must be done inside the Nix shell.** Tools like `uv`, `python`, `task`, and `pre-commit` are provided by the Nix environment and may not be available outside of it.

### Entering the shell

```bash
nix develop
```

This drops you into a shell with all dependencies and tools available. Run this before doing anything else in the repo.

### Why
Running commands outside the Nix shell (e.g., using a system Python or a globally installed `uv`) risks version mismatches and unreproducible behaviour. Always use the Nix shell.

---

## Commits

All commits must follow the [Conventional Commits](https://www.conventionalcommits.org/) spec. This is required — release-please parses commit messages on `main` to determine version bumps and generate the changelog automatically.

### Format

```
<type>[optional scope]: <short description>

[optional body]

[optional footer(s)]
```

### Types and version impact

| Type | When to use | Version bump |
|---|---|---|
| `feat` | A new user-facing feature | Minor (`0.x.0`) |
| `fix` | A bug fix | Patch (`0.0.x`) |
| `feat!` / `fix!` | Breaking change (also add `BREAKING CHANGE:` footer) | Major (`x.0.0`) |
| `refactor` | Code restructuring with no behaviour change | None |
| `docs` | Documentation only | None |
| `chore` | Maintenance, dependency updates, config | None |
| `test` | Adding or updating tests | None |
| `ci` | CI/CD workflow changes | None |
| `style` | Formatting, whitespace (no logic change) | None |
| `perf` | Performance improvement | None |

### Examples

```
feat: add timeo.iter() convenience wrapper
fix: reset ContextVar correctly on exception in track decorator
feat!: rename advance() to step()

BREAKING CHANGE: advance() has been renamed to step() for clarity
docs: add learn mode usage examples to README
chore: update rich to 14.4.0
test: add cache EMA update unit tests
ci: add Python 3.13 to test matrix
```

### Rules
- Use the **imperative mood** in the description ("add", "fix", "update" — not "added", "fixes", "updating").
- Keep the description under **72 characters**.
- Do not end the description with a period.
- If a commit addresses a GitHub issue, reference it in the footer: `Closes #42`.

---

## Branches

| Branch | Purpose |
|---|---|
| `main` | Production-ready code only. release-please runs here. |
| `dev` | Active development branch. All work happens here or in feature branches off `dev`. |
| `feat/<name>` | Optional feature branches for larger pieces of work, branched from `dev`. |

- Never commit directly to `main` — always go through a PR.
- PRs from `dev` → `main` should only be made when the code is ready to release.

---

## Pre-commit

This repo uses [pre-commit](https://pre-commit.com/) to enforce code quality automatically on every commit. Hooks are defined in `.pre-commit-config.yaml`.

### Setup (one-time)

```bash
pre-commit install
```

This installs the hooks into `.git/hooks/` so they run automatically on `git commit`.

### Hooks that run on every commit

| Hook | What it checks |
|---|---|
| `check-yaml` | YAML files are valid |
| `end-of-file-fixer` | All files end with a newline |
| `trailing-whitespace` | No trailing whitespace on any line |
| `black` | Python code is formatted with Black |

### Running manually

To run all hooks against all files (useful before opening a PR):

```bash
pre-commit run --all-files
```

To run a specific hook:

```bash
pre-commit run black --all-files
```

### Rules
- Never bypass hooks with `--no-verify` unless there is a documented, exceptional reason.
- If a hook fails, fix the issue and re-stage before committing — do **not** amend a previous commit to work around it.
- The CI pipeline also runs `pre-commit run --all-files` — a passing local run is required before pushing.

---

## Code Style

- **Formatter:** [Black](https://black.readthedocs.io/) (enforced by pre-commit).
- **Line length:** Black's default (88 characters).
- **Type annotations:** Required on all public functions and methods. mypy must pass with no errors.
- **Docstrings:** Use for all public modules, classes, and functions. Keep them concise.
- **Imports:** Standard library first, third-party second, local last — separated by blank lines.

---

## Testing

- All new features must be accompanied by tests in `tests/`.
- Tests live in `tests/` at the repo root and mirror the `timeo/` module structure (e.g., `timeo/cache.py` → `tests/test_cache.py`).
- Use `pytest`. Run with:
  ```bash
  uv run pytest
  ```
- Do not write tests that render to the terminal or write to `~/.cache/timeo/` — mock `ProgressManager` and patch `timeo.cache._cache_path` in tests that touch the cache.
- Aim for >80% coverage on all modules.

---

## Releasing

Releases are fully automated — do not manually edit version numbers or create GitHub releases by hand.

1. Merge commits following the Conventional Commits spec into `main`.
2. release-please automatically opens a release PR updating `pyproject.toml` and `CHANGELOG.md`.
3. Merge the release PR → a GitHub release is created → the publish workflow pushes the new version to PyPI.

See `CLAUDE.md` for full details on the release process.

---

## Dependencies

- Manage dependencies with `uv`. Never edit `uv.lock` by hand.
- To add a dependency: `uv add <package>`
- To add a dev dependency: `uv add --dev <package>`
- Keep `uv.lock` committed and up to date.
- Pin dependency versions loosely in `pyproject.toml` (e.g., `rich>=14.0`) and let `uv.lock` handle exact pinning.
