# Step 9: CI/CD — Tests, release-please, and PyPI Publishing

## Goal
Set up GitHub Actions workflows for automated testing on every push, automated release management via release-please, and automated PyPI publishing on release.

## Tasks

### 1. Test workflow — `.github/workflows/ci.yml`
Runs on every push and pull request to `main` and `dev`.

```yaml
name: CI

on:
  push:
    branches: [main, dev]
  pull_request:
    branches: [main, dev]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - name: Install dependencies
        run: uv sync --all-extras
      - name: Run pre-commit
        run: uv run pre-commit run --all-files
      - name: Run tests
        run: uv run pytest
```

### 2. Check for existing release-please workflow
There is already a `.github/workflows/release.yml` in the repo from the project template. Inspect it and update it as needed to ensure:
- It triggers on pushes to `main`.
- It uses `googleapis/release-please-action`.
- It is configured for a Python package (release type: `python`).
- It updates the version in `pyproject.toml`.

If the existing workflow already handles this correctly, no changes are needed — document what was verified.

### 3. PyPI publishing workflow — `.github/workflows/publish.yml`
Triggers when release-please creates a new GitHub release (i.e., when a release tag is pushed).

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write  # required for trusted publishing (OIDC)
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - name: Build package
        run: uv build
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
```

Use **PyPI Trusted Publishing** (OIDC) rather than an API token — no secrets needed, just configure the trusted publisher on PyPI for the `publish.yml` workflow.

### 4. Configure PyPI Trusted Publishing
Document the one-time manual setup required on PyPI:
- Go to the timeo project on PyPI (create it if it doesn't exist yet by publishing manually once).
- Under "Publishing", add a trusted publisher:
  - Owner: `wtewalt`
  - Repository: `timeo`
  - Workflow: `publish.yml`
  - Environment: `pypi`
- Create a `pypi` environment in the GitHub repo settings to match.

### 5. Verify `pyproject.toml` build configuration
Ensure `pyproject.toml` has a `[build-system]` section compatible with `uv build`:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

Confirm the `timeo/` package directory will be included in the built distribution.

## Notes
- Do not add `PYPI_API_TOKEN` as a secret — use OIDC trusted publishing instead.
- The `release.yml` workflow (release-please) creates the GitHub release; the `publish.yml` workflow reacts to it and pushes to PyPI. These are intentionally separate.
- Pin action versions to a specific SHA or tag for security.

## Acceptance Criteria
- `ci.yml` runs successfully on a push to `dev`.
- Merging a `feat:` commit to `main` causes release-please to open a release PR.
- Merging the release PR triggers `publish.yml` and publishes the package to PyPI.
- `uv build` succeeds locally and produces a `.whl` and `.tar.gz` in `dist/`.
- The published package is installable: `pip install timeo` works.
